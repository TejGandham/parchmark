#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""KEEL backlog structured-field backfill helper (offline, human-initiated).

Backfills the structured `dependencies:` (and, where derivable, a confirmed
`frozen_seams:`) YAML arrays into existing backlog entries from the
prose `Needs:` / `Design:` fields those entries already carry.

WHY THIS IS OPTIONAL: the pipeline resolver fail-safes a MISSING structured
array to the conservative (Opus) route — see
scripts/keel_work_items.py §"Structured backlog pretriage fields" and
scripts/keel-work-item-resolve.py. So a backlog with no structured arrays
still routes correctly; it just always pays the conservative price. This
tool is an *offline* convenience to let a human convert prose-only legacy
backlogs into entries that carry the deterministic pretriage signal. It is
NEVER invoked at pipeline runtime.

WHAT IT DERIVES vs. WHAT IT REFUSES TO GUESS:
- `dependencies:` of `kind: feature` — DERIVED losslessly from the `Needs:`
  prose. Each `Needs:` id WI## becomes `- id: WI##` / `kind: feature`. This is
  the same id set the resolver already trusts, so the conversion is exact.
- `Design:` library / protocol / prototype mentions — HEURISTIC. The tool
  does NOT silently write guessed `kind: library|protocol|prototype`
  entries. It surfaces a confirmation list (per entry, the tokens it
  noticed) so a human can decide. Confirmed tokens are NOT written by this
  run — the human edits them in or re-runs the drafter. Guessing a
  dependency the resolver then scores would be worse than the fail-safe.
- `frozen_seams:` — NOT derivable from prose. There is no `Needs:`/`Design:`
  source for an upstream frozen-seam name, and inventing one is forbidden
  (backlog-drafter.md §Structured pretriage fields). The tool reports that
  frozen seams cannot be backfilled and points at the drafter.

The written form matches exactly what `backlog-drafter` materializes and
what `keel_work_items._parse_yaml_listblock` reads: a `  dependencies:`
header line at the same 2-space indent as the entry's `Needs:`/`Binder:`
lines, with `    - id: WI##` / `      kind: feature` items at deeper indent.

CLI:
    keel-backlog-migrate.py <backlog-path> [--feature WI##] [--dry-run]

Exit codes (every non-zero halt prints a P7 cause + next step to stderr):
  0 — success (changes written, or dry-run printed, or nothing to do)
  2 — invocation error (bad args, missing/unreadable backlog, bad --feature)
  3 — no matching feature entry found for --feature
  4 — backlog has duplicate entries for the requested feature
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# --- exit codes -------------------------------------------------------------

EXIT_OK = 0
EXIT_INVOCATION = 2
EXIT_FEATURE_NOT_FOUND = 3
EXIT_FEATURE_DUPLICATE = 4


class Halt(Exception):
    """Carries an exit code + a P7 message (cause + concrete next step)."""

    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


# --- backlog grammar (mirrors scripts/keel_work_items.py) ---------------------
#
# These patterns are deliberately kept in lockstep with keel_work_items.py so a
# migrated entry parses identically downstream. The entry-start and Needs:
# regexes are copied verbatim from that module; if the canonical grammar
# changes there, update here too (validated by the test suite round-trip).

_ENTRY_START_RE = re.compile(
    r"^[-*]\s+\[[ xX]\]\s+(?:\*\*)?WI(\d+)\b",
    re.MULTILINE,
)
_FEATURE_ID_RE = re.compile(r"^WI(\d+)$")
_NEEDS_RE = re.compile(
    r"(?:^|\|)\s*Needs:\s*([^|\n]+?)\s*(?=\||$)",
    re.MULTILINE,
)
_DESIGN_RE = re.compile(
    r"(?:^|\|)\s*Design:\s*([^|\n]+?)\s*(?=\||$)",
    re.MULTILINE,
)
_PROTOTYPE_MARKER_RE = re.compile(r"^\[prototype:(reference|seed)\]\s*")
# An already-present `dependencies:` header line (any indent) — the
# idempotency discriminator. Mirrors _parse_yaml_listblock's header probe.
_DEPENDENCIES_HEADER_RE = re.compile(r"^\s*dependencies:\s*$", re.MULTILINE)
_FROZEN_SEAMS_HEADER_RE = re.compile(r"^\s*frozen_seams:\s*$", re.MULTILINE)
# The 2-space indent KEEL uses for an entry's field lines (Needs:/Binder:/...).
_FIELD_LINE_RE = re.compile(r"^(\s+)\S")

# Heuristic Design: token classes. Prototype paths are recognized structurally
# (the `[prototype:*]` marker or a `/prototype/` path segment). Library /
# protocol guesses are intentionally weak — they exist only to FLAG tokens for
# a human, never to auto-write a kind.
_PROTOTYPE_PATH_RE = re.compile(r"/prototype/")
_PROTOCOL_HINT_RE = re.compile(
    r"\b(sse|server-sent-events|websocket|grpc|graphql|webhook|http/2|http2)\b",
    re.IGNORECASE,
)


# --- records ----------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class Entry:
    """A parsed backlog entry block and its source span."""

    feature_id: str          # e.g. "WI04"
    start: int               # byte offset of block start in the backlog text
    end: int                 # byte offset of block end (exclusive)
    block: str               # the raw block text


@dataclass(slots=True, frozen=True)
class Proposal:
    """A proposed backfill for one entry."""

    feature_id: str
    feature_deps: tuple[str, ...]        # Needs: ids → kind:feature deps
    already_migrated: bool               # entry already had a dependencies: block
    design_hints: tuple[str, ...]        # heuristic Design: tokens needing confirmation
    frozen_seam_note: bool               # entry has Design: but no frozen_seams: (cannot derive)

    @property
    def writes_anything(self) -> bool:
        return (not self.already_migrated) and bool(self.feature_deps)


# --- parsing ----------------------------------------------------------------

def find_entries(text: str) -> list[Entry]:
    """Split the backlog into feature-entry blocks (start → next start/EOF)."""
    starts = list(_ENTRY_START_RE.finditer(text))
    entries: list[Entry] = []
    for i, m in enumerate(starts):
        start = m.start()
        end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        entries.append(
            Entry(
                feature_id=f"WI{int(m.group(1)):02d}",
                start=start,
                end=end,
                block=text[start:end],
            )
        )
    return entries


def entries_for(text: str, feature_id: str | None) -> list[Entry]:
    """All entries, or just those matching `feature_id` (halts on dup/none)."""
    entries = find_entries(text)
    if feature_id is None:
        return entries
    norm = _normalize_feature_id(feature_id)
    matching = [e for e in entries if e.feature_id == norm]
    if not matching:
        raise Halt(
            EXIT_FEATURE_NOT_FOUND,
            f"No backlog entry for feature `{norm}` (looked for a "
            f"`- [ ] {norm} ...` line). Fix: pass a feature id that exists "
            f"in the backlog, or drop --feature to migrate every entry.",
        )
    if len(matching) > 1:
        raise Halt(
            EXIT_FEATURE_DUPLICATE,
            f"Backlog has {len(matching)} entries for feature `{norm}`. "
            f"Each WI## must appear exactly once. Fix: consolidate the "
            f"duplicate entries into one before migrating.",
        )
    return matching


def _normalize_feature_id(raw: str) -> str:
    """Normalize a user-supplied feature id to canonical `WI##` form."""
    m = _FEATURE_ID_RE.fullmatch(raw.strip())
    if not m:
        raise Halt(
            EXIT_INVOCATION,
            f"--feature value {raw!r} is not a valid feature id. Fix: pass "
            f"an id of the form WI## (e.g. WI04, WI123).",
        )
    return f"WI{int(m.group(1)):02d}"


def parse_needs_ids(block: str) -> tuple[str, ...]:
    """Feature ids from the entry's `Needs:` prose, in order, de-duplicated."""
    m = _NEEDS_RE.search(block)
    if not m:
        return ()
    seen: list[str] = []
    for tok in m.group(1).split(","):
        tok = tok.strip()
        idm = _FEATURE_ID_RE.fullmatch(tok)
        if idm:
            canon = f"WI{int(idm.group(1)):02d}"
            if canon not in seen:
                seen.append(canon)
    return tuple(seen)


def parse_design_hints(block: str) -> tuple[str, ...]:
    """Heuristic non-feature dependency tokens from the entry's `Design:` line.

    Returns a list of human-readable hint strings (NOT structured deps). These
    are surfaced for confirmation only — the tool never auto-writes a guessed
    kind. Empty when there is no Design: line or nothing recognizable."""
    m = _DESIGN_RE.search(block)
    if not m:
        return ()
    content = m.group(1).strip()
    hints: list[str] = []
    marker = _PROTOTYPE_MARKER_RE.match(content)
    if marker:
        hints.append(f"prototype (kind: prototype) — disposition {marker.group(1)!r}")
        content = content[marker.end():]
    paths = [p.strip() for p in content.split(",") if p.strip()]
    for p in paths:
        if _PROTOTYPE_PATH_RE.search(p):
            hints.append(f"{p}  (likely kind: prototype — under a /prototype/ dir)")
        elif _PROTOCOL_HINT_RE.search(p):
            hints.append(f"{p}  (possible kind: protocol)")
    return tuple(hints)


def build_proposal(entry: Entry) -> Proposal:
    already = _DEPENDENCIES_HEADER_RE.search(entry.block) is not None
    has_frozen = _FROZEN_SEAMS_HEADER_RE.search(entry.block) is not None
    feature_deps = parse_needs_ids(entry.block)
    design_hints = parse_design_hints(entry.block)
    return Proposal(
        feature_id=entry.feature_id,
        feature_deps=feature_deps,
        already_migrated=already,
        design_hints=design_hints,
        # A frozen-seam note is worth surfacing only when the entry has design
        # context but no frozen_seams: block — and even then we cannot derive.
        frozen_seam_note=bool(design_hints) and not has_frozen,
    )


# --- rendering --------------------------------------------------------------

def _detect_field_indent(block: str) -> str:
    """The indent KEEL uses for this entry's field lines (e.g. `Needs:`).

    Probes the line AFTER the `- [ ] **WI## ...**` header for its leading
    whitespace; falls back to two spaces (KEEL's canonical depth)."""
    lines = block.splitlines()
    for line in lines[1:]:
        if not line.strip():
            continue
        m = _FIELD_LINE_RE.match(line)
        if m:
            return m.group(1)
        break
    return "  "


def render_dependencies_block(feature_deps: tuple[str, ...], field_indent: str) -> str:
    """The `dependencies:` YAML lines to insert, matching drafter output.

    Header at `field_indent`; `- id:`/`kind:` items two spaces deeper, exactly
    the shape `_parse_yaml_listblock` reads back."""
    item_indent = field_indent + "  "
    sub_indent = item_indent + "  "
    out = [f"{field_indent}dependencies:"]
    for fid in feature_deps:
        out.append(f"{item_indent}- id: {fid}")
        out.append(f"{sub_indent}kind: feature")
    return "\n".join(out)


def apply_proposal(block: str, proposal: Proposal) -> str:
    """Return the block with a `dependencies:` block inserted after `Needs:`.

    Idempotent: when the entry already carries a `dependencies:` block (or has
    no feature deps to write), the block is returned unchanged."""
    if not proposal.writes_anything:
        return block
    field_indent = _detect_field_indent(block)
    dep_block = render_dependencies_block(proposal.feature_deps, field_indent)

    lines = block.splitlines(keepends=True)
    # Insert right after the Needs: line when present, else after the header.
    insert_at = None
    for i, line in enumerate(lines):
        if _NEEDS_RE.search(line):
            insert_at = i + 1
            break
    if insert_at is None:
        insert_at = 1 if lines else 0

    # Preserve the trailing newline style of the anchor line.
    anchor = lines[insert_at - 1] if insert_at > 0 and lines else ""
    needs_nl = bool(anchor) and not anchor.endswith("\n")
    inserted = ("\n" if needs_nl else "") + dep_block + "\n"
    new_lines = lines[:insert_at] + [inserted] + lines[insert_at:]
    return "".join(new_lines)


# --- reporting --------------------------------------------------------------

def format_report(proposals: list[Proposal], *, dry_run: bool) -> str:
    out: list[str] = []
    to_write = [p for p in proposals if p.writes_anything]
    skipped = [p for p in proposals if p.already_migrated]
    no_deps = [
        p for p in proposals
        if not p.already_migrated and not p.feature_deps
    ]

    verb = "Would backfill" if dry_run else "Backfilled"
    if to_write:
        out.append(f"{verb} dependencies[] for {len(to_write)} entr"
                   f"{'y' if len(to_write) == 1 else 'ies'}:")
        for p in to_write:
            deps = ", ".join(f"{d} (feature)" for d in p.feature_deps)
            out.append(f"  {p.feature_id}: {deps}")
    else:
        out.append(f"No entries to backfill ({verb.lower().split()[0]} nothing).")

    if skipped:
        ids = ", ".join(p.feature_id for p in skipped)
        out.append(f"Skipped (already have dependencies[]): {ids}")
    if no_deps:
        ids = ", ".join(p.feature_id for p in no_deps)
        out.append(f"Skipped (no Needs: prose to derive feature deps from): {ids}")

    # Confirmation list — heuristic Design: hints the tool refuses to auto-write.
    hint_entries = [p for p in proposals if p.design_hints]
    if hint_entries:
        out.append("")
        out.append("CONFIRMATION NEEDED — Design: tokens detected but NOT written")
        out.append("(non-feature deps are heuristic; confirm and add by hand or re-run")
        out.append(" backlog-drafter, which grounds novelty against landed features):")
        for p in hint_entries:
            out.append(f"  {p.feature_id}:")
            for h in p.design_hints:
                out.append(f"    - {h}")

    seam_entries = [p for p in proposals if p.frozen_seam_note]
    if seam_entries:
        out.append("")
        ids = ", ".join(p.feature_id for p in seam_entries)
        out.append(
            f"frozen_seams[] NOT derivable from prose for: {ids}. There is no "
            f"Needs:/Design: source for an upstream frozen-seam name, and "
            f"inventing one is forbidden. Next step: if any of these features "
            f"cross an upstream `### Constraints for downstream` frozen seam, "
            f"add frozen_seams[] by hand or re-run backlog-drafter."
        )

    return "\n".join(out)


# --- driver -----------------------------------------------------------------

def migrate(backlog_path: Path, feature_id: str | None, *, dry_run: bool) -> str:
    if not backlog_path.is_file():
        raise Halt(
            EXIT_INVOCATION,
            f"Backlog file not found at {backlog_path}. Fix: pass the path to "
            f"an existing backlog.md "
            f"(e.g. docs/exec-plans/active/backlog.md).",
        )
    try:
        text = backlog_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise Halt(
            EXIT_INVOCATION,
            f"Could not read {backlog_path}: {exc}. Fix: check file "
            f"permissions and re-run.",
        ) from exc

    targets = entries_for(text, feature_id)
    proposals = [build_proposal(e) for e in targets]

    if not dry_run:
        # Rewrite affected blocks back into the full text, last-to-first so
        # earlier offsets stay valid. Only entries that actually change are
        # touched (idempotent for already-migrated / no-dep entries).
        new_text = text
        for entry, proposal in sorted(
            zip(targets, proposals), key=lambda pair: pair[0].start, reverse=True
        ):
            if not proposal.writes_anything:
                continue
            new_block = apply_proposal(entry.block, proposal)
            if new_block != entry.block:
                new_text = new_text[:entry.start] + new_block + new_text[entry.end:]
        if new_text != text:
            backlog_path.write_text(new_text, encoding="utf-8")

    return format_report(proposals, dry_run=dry_run)


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="keel-backlog-migrate.py",
        description=(
            "Offline helper: backfill structured dependencies[] arrays into "
            "existing backlog entries from prose Needs:/Design: fields. NOT "
            "run at pipeline time — the resolver fail-safes missing arrays to "
            "the conservative route."
        ),
    )
    p.add_argument(
        "backlog_path",
        type=Path,
        help="path to backlog.md",
    )
    p.add_argument(
        "--feature",
        metavar="WI##",
        default=None,
        help="migrate only this feature entry (default: every entry)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="print proposed changes without writing",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        report = migrate(
            args.backlog_path, args.feature, dry_run=args.dry_run
        )
    except Halt as halt:
        print(halt.message, file=sys.stderr)
        return halt.code
    print(report)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
