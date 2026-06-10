#!/usr/bin/env python3
"""Validate invariant 7 — Binder link integrity on backlog entries.

Checks every WI## entry on the backlog carries either `Binder: <slug>` or
`Binder-exempt: <reason>` (XOR), and that each `Binder: <slug>` resolves to
an existing Binder file under `docs/exec-plans/binders/`.

**Extension handling.** The pipeline canon (NORTH-STAR §"Feature
input canon — single path, JSON Binders only") is structured JSON at
`<slug>.json`. This validator also accepts a legacy `<slug>.md` for
unmigrated repos and emits a stderr deprecation warning naming the
JSON canonical path; the `.md` Binder passes link integrity but the
warning steers the human to migrate via `/keel-refine`.

Scope: backlog-side invariant 7 enforcement only. For structural
validation of the Binder JSON content itself (schema, oracle shape,
cross-references), see the sibling `validate-binder-json.py`.

Stdlib-only. Python 3.10+. Cross-platform.

See docs/design-docs/2026-04-23-keel-prd-scope-design.md §"Validator"
(invariant 7 design),
docs/design-docs/2026-04-24-structured-prds.md (JSON Binder direction),
and docs/process/KEEL-PRINCIPLES.md for the principles this enforces.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ALLOWED_EXEMPT_REASONS = {"legacy", "bootstrap", "infra", "trivial"}
MARKER_RE = re.compile(r"<!--\s*KEEL-INVARIANT-7:\s*legacy-through=WI(\d+)\s*-->")
# Slug alphabet mirrors the Binder `id` pattern in schemas/binder.schema.json:
# `^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$`. Rejects trailing-hyphen forms like
# "foo-" or "foo--". Keeping alphabets aligned prevents validate-binders from
# silently blessing slugs that the JSON schema would later reject when the
# markdown Binder is migrated. Single-char slugs (e.g. "a") still match.
BINDER_FIELD_RE = re.compile(r"^\s*Binder:\s*([a-z0-9](?:[a-z0-9-]*[a-z0-9])?)\s*$", re.MULTILINE)
BINDER_EXEMPT_RE = re.compile(r"^\s*Binder-exempt:\s*(\S+)", re.MULTILINE)
STORY_PROSE_RE = re.compile(r"(?<![#/\w])WI\d{2,}\b")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate invariant 7 Binder integrity.")
    p.add_argument(
        "--repo",
        default=".",
        help="Repo root to validate (default: current directory).",
    )
    return p.parse_args()


def halt(msg: str) -> None:
    """Halt with a call-to-action (P7)."""
    print(f"validate-binders: HALT — {msg}", file=sys.stderr)
    sys.exit(1)


def find_backlog(repo: Path) -> Path:
    backlog = repo / "docs" / "exec-plans" / "active" / "backlog.md"
    if not backlog.exists():
        halt(
            f"no backlog.md at {backlog}. "
            "Validate expects the canonical KEEL backlog path."
        )
    return backlog


def read_marker(backlog_text: str) -> int | None:
    """Return the legacy-through WI## number, or None if marker absent."""
    m = MARKER_RE.search(backlog_text)
    return int(m.group(1)) if m else None


def strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks (backtick or tilde) and inline code spans.

    Prevents ``WI##`` tokens appearing in legitimate code examples from
    triggering false positives in the Binder prose scope lint. Markdown
    supports both ```` ``` ```` and ``~~~`` fences; both must be stripped
    or a Binder using tilde fences silently bypasses the lint.
    """
    # Backtick fences (``` ... ```), including multi-line content.
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Tilde fences (~~~ ... ~~~).
    text = re.sub(r"~~~.*?~~~", "", text, flags=re.DOTALL)
    # Inline code spans (`...`).
    text = re.sub(r"`[^`\n]+`", "", text)
    return text


def parse_story_entries(backlog_text: str) -> list[dict]:
    """Parse WI## entries. Each entry: {id, text, binder, exempt}.

    Terminates an entry on:
      - the next WI## bullet line,
      - a markdown heading (``^\\s*##\\s``) or horizontal rule
        (``^\\s*---\\s*$``),
      - a blank line followed by a non-indented content line (EOF also
        closes).
    Blank lines followed by indented continuation keep accumulating.
    """
    entries = []
    lines = backlog_text.splitlines(keepends=True)
    current = None
    for i, line in enumerate(lines):
        match = re.match(r"\s*-\s*\[[ x]\]\s*\*\*WI(\d+)\s", line)
        if match:
            # New WI## entry starts — close previous if open.
            if current is not None:
                entries.append(current)
            current = {"id": int(match.group(1)), "text": line}
            continue
        if current is None:
            continue
        # Terminate current entry on structural markers.
        if re.match(r"^\s*##\s", line) or re.match(r"^\s*---\s*$", line):
            entries.append(current)
            current = None
            continue
        # Terminate on blank line followed by non-indented content.
        if line.strip() == "":
            next_non_blank = None
            for j in range(i + 1, len(lines)):
                if lines[j].strip() != "":
                    next_non_blank = lines[j]
                    break
            if next_non_blank is None:
                # EOF — close entry.
                entries.append(current)
                current = None
                continue
            if not (next_non_blank.startswith(" ") or next_non_blank.startswith("\t")):
                # Next non-blank is non-indented → entry ends here.
                entries.append(current)
                current = None
                continue
            # Otherwise continue accumulating (blank + indented).
        current["text"] += line
    if current is not None:
        entries.append(current)

    # Extract Binder: and Binder-exempt: from each entry's text.
    for e in entries:
        epic_matches = BINDER_FIELD_RE.findall(e["text"])
        exempt_matches = BINDER_EXEMPT_RE.findall(e["text"])
        e["epic_lines"] = epic_matches
        e["exempt_lines"] = exempt_matches

    return entries


def validate(repo: Path) -> list[str]:
    """Return list of error messages. Empty list = valid."""
    errors: list[str] = []
    backlog = find_backlog(repo)
    backlog_text = backlog.read_text(encoding="utf-8")

    cutoff = read_marker(backlog_text)
    entries = parse_story_entries(backlog_text)
    epic_dir = repo / "docs" / "exec-plans" / "binders"

    # Track referenced Binders for orphan detection.
    referenced_slugs: set[str] = set()

    for entry in entries:
        sid = entry["id"]
        grandfathered = cutoff is not None and sid <= cutoff
        binders = entry["epic_lines"]
        exempts = entry["exempt_lines"]

        # Cardinality check: at most one Binder: line.
        if len(binders) > 1:
            errors.append(
                f"WI{sid:02d} has multiple Binder: lines. "
                "Binder: is single-valued (cross-Binder work must split). "
                "Fix: consolidate to a single Binder: line."
            )

        # Cardinality check: at most one Binder-exempt: line.
        if len(exempts) > 1:
            errors.append(
                f"WI{sid:02d} has multiple Binder-exempt: lines. "
                "Only one exemption reason per entry. "
                "Fix: consolidate to a single Binder-exempt: line."
            )

        # XOR check: Binder: and Binder-exempt: are mutually exclusive.
        # An entry is either covered by a Binder or exempted — never both.
        # This takes precedence over the missing-link check below.
        if binders and exempts:
            errors.append(
                f"WI{sid:02d} has both Binder: and Binder-exempt: lines. "
                "These are mutually exclusive — pick one. "
                "Fix: remove the Binder-exempt line if this work_item has a Binder, "
                "or remove the Binder line if this is genuinely exempt."
            )
            # Record the Binder ref anyway to prevent a spurious orphan cascade.
            # Without this, the Binder file foo.md would be falsely flagged as
            # orphaned, producing a second confusing error from the same root.
            if binders[0]:
                referenced_slugs.add(binders[0])
            continue  # skip further checks; the entry is structurally broken

        if cutoff is None:
            # Pre-adoption grace: don't enforce per-entry.
            if binders:
                referenced_slugs.add(binders[0])
            continue

        if grandfathered:
            if binders:
                referenced_slugs.add(binders[0])
            continue

        # Post-cutoff: must have Binder: or Binder-exempt:.
        if not binders and not exempts:
            errors.append(
                f"WI{sid:02d} is past the legacy cutoff WI{cutoff:02d}; missing Binder: and Binder-exempt:. "
                f"Fix: add Binder: <slug> pointing at docs/exec-plans/binders/<slug>.json, "
                f"or add Binder-exempt: <reason> where reason is one of "
                f"{sorted(ALLOWED_EXEMPT_REASONS)}."
            )
            continue

        if binders:
            slug = binders[0]
            # Pipeline canon (NORTH-STAR §Feature input canon): Binders are
            # structured JSON at <slug>.json. Legacy <slug>.md is accepted for
            # unmigrated repos and triggers a stderr deprecation warning that
            # names the canonical .json path so the human can migrate via
            # /keel-refine.
            binder_path_json = epic_dir / f"{slug}.json"
            binder_path_md = epic_dir / f"{slug}.md"
            if binder_path_json.exists():
                pass  # canonical path
            elif binder_path_md.exists():
                print(
                    f"warning: WI{sid:02d} references Binder '{slug}' which exists only as "
                    f"{binder_path_md}. Pipeline canon is structured JSON at "
                    f"{binder_path_json}. Migrate via /keel-refine.",
                    file=sys.stderr,
                )
            else:
                errors.append(
                    f"WI{sid:02d} references Binder '{slug}' but neither "
                    f"{binder_path_json} nor {binder_path_md} exists. "
                    f"Fix: run /keel-refine to author the structured JSON Binder, "
                    f"rename the slug, or mark WI{sid:02d} as Binder-exempt with "
                    f"a valid reason."
                )
            referenced_slugs.add(slug)

        for reason in exempts:
            if reason not in ALLOWED_EXEMPT_REASONS:
                errors.append(
                    f"WI{sid:02d} declares Binder-exempt with reason '{reason}'; "
                    f"must be one of {sorted(ALLOWED_EXEMPT_REASONS)}; "
                    f"got '{reason}'."
                )

    # Orphan detection: Binder files (both .json and .md during transition)
    # with no references. Scope-lint (WI## IDs in prose) runs only on
    # markdown Binders — it's not meaningful for structured JSON content.
    if epic_dir.exists():
        for epic_file in sorted(
            list(epic_dir.glob("*.json")) + list(epic_dir.glob("*.md"))
        ):
            if epic_file.stem not in referenced_slugs:
                errors.append(
                    f"Binder file {epic_file} is not referenced by any WI## in the backlog. "
                    f"Fix: either delete the orphaned Binder or add WI## entries that reference it."
                )

            if epic_file.suffix != ".md":
                continue

            # Scope lint: no WI## IDs in prose (ignore fenced/inline code).
            # Applies to legacy markdown Binders only.
            text = epic_file.read_text(encoding="utf-8")
            stripped_text = strip_code_blocks(text)
            for m in STORY_PROSE_RE.finditer(stripped_text):
                errors.append(
                    f"Binder prose {epic_file} contains WI## reference '{m.group(0)}'. "
                    f"Narrative must use theme-level language, not IDs. "
                    f"Fix: rewrite the prose to describe themes/scope; the "
                    f"feature list lives on docs/exec-plans/active/backlog.md "
                    f"(WI## entries tagged `Binder: {epic_file.stem}`)."
                )

    return errors


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    errors = validate(repo)
    if errors:
        for e in errors:
            print(f"validate-binders: {e}", file=sys.stderr)
        print(f"\nvalidate-binders: {len(errors)} problem(s) found.", file=sys.stderr)
        return 1
    print("validate-binders: OK — invariant 7 compliant.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
