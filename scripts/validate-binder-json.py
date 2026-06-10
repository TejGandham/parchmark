#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = ["jsonschema>=4.25"]
# ///
"""Validate a structured KEEL Binder (JSON) against schemas/binder.schema.json.

Applies three validation stages:
  1. JSON Schema validation (structural — Binder frame, feature frame, oracle
     shape, cross-reference IDs)
  2. Intra-Binder cross-reference integrity (work_items[].needs[] resolve,
     feature IDs unique, no self-dependency)
  3. Invariant-ID existence (`invariants_exercised[].invariant_id` resolves
     to an INV-### token declared in the project guide's §Safety Rules
     (AGENTS.md, or CLAUDE.md as fallback) — the same source `keel-refine`
     parses to seed the drafter's `repo_context.invariants[]` list)

Feature-specific contract content is intentionally NOT validated here.
Contract shapes are case-by-case and cannot be generalized into required
keys by layer or type. Feature-specific contract gaps are detected at
pipeline time by test-writer via expected-vs-declared key introspection.
See docs/design-docs/2026-04-24-structured-prds.md for the full rationale.

Usage:
  uv run scripts/validate-binder-json.py path/to/binder.json [--format human|json]

Exit codes:
  0  validation passed
  1  validation failed (findings reported to stdout)
  2  invocation error (file not found, not JSON, etc.)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, TypedDict

from jsonschema import Draft202012Validator

# --- Types ------------------------------------------------------------------

class Feature(TypedDict):
    id: str
    title: str
    layer: str
    needs: list[str]
    contract: dict
    oracle: dict


class Binder(TypedDict):
    id: str
    title: str
    motivation: str
    scope: dict
    design_facts: list[dict]
    invariants_exercised: list[dict]
    work_items: list[Feature]


@dataclass(slots=True, frozen=True)
class Finding:
    path: str
    message: str


class Validator(Protocol):
    def validate(self, doc: Binder) -> list[Finding]: ...


# --- Validator stages -------------------------------------------------------

@dataclass(slots=True, frozen=True)
class SchemaValidator:
    """JSON Schema validation of the Binder frame."""
    schema: dict

    def validate(self, doc: Binder) -> list[Finding]:
        v = Draft202012Validator(self.schema)
        errors = sorted(v.iter_errors(doc), key=lambda e: list(e.absolute_path))
        return [
            Finding(
                path="/" + "/".join(str(p) for p in e.absolute_path),
                message=e.message.split("\n")[0],
            )
            for e in errors
        ]


@dataclass(slots=True, frozen=True)
class XrefValidator:
    """Cross-reference integrity on top of the schema.

    Only runs when SchemaValidator reports no findings — if the document
    is shape-invalid (e.g. `work_items` is not a list), xref checks are
    meaningless and would raise Python errors instead of producing
    structured findings. Skipping until schema passes keeps P7 intact.

    Scope: intra-Binder references only. `needs[]` must resolve to some
    WI## in the same Binder; feature IDs must be unique. Existence of
    `invariants_exercised[].invariant_id` is checked by
    `InvariantXrefValidator` against the project guide's §Safety Rules
    (AGENTS.md, or CLAUDE.md as fallback).
    """

    def validate(self, doc: Binder) -> list[Finding]:
        findings: list[Finding] = []
        work_items = doc.get("work_items", [])
        if not isinstance(work_items, list):
            return findings  # schema stage would have already reported this
        known_ids = {
            f["id"] for f in work_items
            if isinstance(f, dict) and isinstance(f.get("id"), str)
        }

        seen_ids: dict[str, list[int]] = {}
        for i, work_item in enumerate(work_items):
            if not isinstance(work_item, dict):
                continue
            fid = work_item.get("id")
            needs = work_item.get("needs", [])
            if isinstance(needs, list):
                # Dangling dependency
                for need in needs:
                    if isinstance(need, str) and need not in known_ids:
                        findings.append(Finding(
                            path=f"/work_items/{i}/needs",
                            message=f"'{need}' does not resolve to any feature in this Binder",
                        ))
                # Self-dependency
                if isinstance(fid, str) and fid in needs:
                    findings.append(Finding(
                        path=f"/work_items/{i}/needs",
                        message=f"feature '{fid}' declares itself as a dependency",
                    ))
            if isinstance(fid, str):
                seen_ids.setdefault(fid, []).append(i)

        # Duplicate feature IDs — report every extra occurrence, not just one
        for fid, positions in seen_ids.items():
            if len(positions) > 1:
                first = positions[0]
                for dup_pos in positions[1:]:
                    findings.append(Finding(
                        path=f"/work_items/{dup_pos}/id",
                        message=(
                            f"duplicate feature id '{fid}' "
                            f"(already declared at /work_items/{first}/id)"
                        ),
                    ))

        return findings


# --- Invariant registry (project guide §Safety Rules) -----------------------

_GUIDE_SEARCH_DEPTH = 4  # mirrors _SCHEMA_SEARCH_DEPTH below
# Heading regex tolerates up to 3 spaces of indentation (CommonMark
# permits it on ATX headings and setext underlines, consistent with
# `_FENCE` below) and trailing content after "Rules" (anchors `{#id}`,
# suffixes like "(project-specific)", trailing colons). The `\b` after
# "Rules" anchors the word boundary.
_SAFETY_HEADING = re.compile(
    r"^[ \t]{0,3}(#{1,6})\s+Safety Rules\b", re.IGNORECASE,
)
_ANY_HEADING = re.compile(r"^[ \t]{0,3}(#{1,6})\s+\S")
# Setext heading underlines: a non-blank line followed by `===` or `---`.
# `===` always indicates an H1, `---` an H2 (treat as level 1/2 boundary).
_SETEXT_H1 = re.compile(r"^[ \t]{0,3}=+\s*$")
_SETEXT_H2 = re.compile(r"^[ \t]{0,3}-+\s*$")
# Setext heading text is paragraph content per CommonMark — it cannot
# start with a list marker, blockquote, or be indented code. Excluding
# these prevents `---` thematic breaks after list items from being
# misclassified as section boundaries.
_BLOCK_MARKER = re.compile(r"^[ \t]*(?:[-*+]|\d+[.)])\s|^[ \t]*>")
_FENCE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
# Closing fence requires ≤3 leading spaces, fence chars only, and no
# trailing info string (CommonMark §4.5). Using a distinct pattern
# (rather than reusing `_FENCE`) prevents a deeply-indented `\`\`\`` or
# one with trailing text from incorrectly closing an outer fence.
_FENCE_CLOSE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})\s*$")
# HTML comment stripper. `.*?` is non-greedy so adjacent comments do not
# fuse. Unterminated comments (missing `-->`) consume to end-of-string
# per CommonMark's unclosed-HTML-block semantics, so commented-out
# INV tokens do not leak when the closer was forgotten. Applied only
# to content OUTSIDE fenced code blocks — see `_strip_markdown_noise`.
_HTML_COMMENT = re.compile(r"<!--.*?(?:-->|\Z)", re.DOTALL)
# Word-boundaried token regex: `INV-001A` does not match `INV-001`,
# preventing typo'd registry entries from satisfying real Binder citations.
_INV_TOKEN = re.compile(r"\bINV-[0-9]{3,}\b")


def _locate_project_guide(binder_path: Path) -> Path | None:
    """Walk upward from the Binder's directory for the project guide.

    The project guide holds §Safety Rules and is `AGENTS.md` on every host
    (the host-neutral content root); `CLAUDE.md` is Claude Code's auto-load
    file and ships as a thin `@AGENTS.md` pointer, so it is only the
    fallback for a repo that keeps its rules in CLAUDE.md directly. At each
    level AGENTS.md is preferred over CLAUDE.md; the first level with either
    wins (closest to the Binder), so a fixture directory can ship its own
    guide without falling through to a framework-repo guide higher up the
    tree. Search depth matches the schema locator. A symlinked guide is
    accepted (`is_file()` follows the link); a *broken* symlink is also
    returned so the caller's `read_text` raises and surfaces a clear halt —
    silently walking past a broken nearest guide and binding to a
    parent-tree one would validate against the wrong registry.
    """
    here = binder_path.resolve().parent
    candidates = [here, *list(here.parents)[:_GUIDE_SEARCH_DEPTH]]
    for candidate in candidates:
        for name in ("AGENTS.md", "CLAUDE.md"):
            path = candidate / name
            if path.is_file():
                return path
            if path.is_symlink():  # broken symlink (target does not exist)
                return path
    return None


def _strip_markdown_noise(text: str) -> str:
    """Remove fenced code blocks and HTML comments before token scan.

    Counter-examples or illustrative tokens inside ```fences``` or
    `<!-- comments -->` inside §Safety Rules must not register as
    declared invariants — that would let a Binder citing a bogus INV-###
    pass the existence check.

    Two passes:

    1. Strip fenced code blocks via a line-by-line state machine. Fence
       length is preserved per CommonMark §4.5: a fence opened with N
       characters can only be closed by ≥ N matching characters, with
       ≤3 leading spaces and no trailing info string. The closer check
       uses `_FENCE_CLOSE` to enforce these constraints.
    2. Strip HTML comments (regex, non-greedy, unclosed-to-EOF). Run
       AFTER fence stripping so a literal `<!--` inside a code fence
       never triggers global comment consumption that would eat a
       later §Safety Rules heading.
    """
    out: list[str] = []
    fence_char: str | None = None
    fence_len = 0
    for line in text.splitlines():
        if fence_char is None:
            m = _FENCE.match(line)
            if m:
                fence_char = m.group(1)[0]
                fence_len = len(m.group(1))
            else:
                out.append(line)
        else:
            m_close = _FENCE_CLOSE.match(line)
            if (m_close is not None
                    and m_close.group(1)[0] == fence_char
                    and len(m_close.group(1)) >= fence_len):
                fence_char = None
                fence_len = 0
            # Inside-fence lines are always dropped; an unterminated
            # fence at EOF takes the rest of the file with it, per
            # CommonMark's EOF-closes-fence semantics.
    return _HTML_COMMENT.sub("", "\n".join(out))


def _is_setext_text(line: str) -> bool:
    """True if `line` could be the text of a setext heading.

    Per CommonMark, setext heading text is paragraph content: it
    cannot start with a list marker (`-`, `*`, `+`, `1.`), a
    blockquote (`>`), be indented code (≥4 leading spaces), or be
    itself an ATX heading. Without these filters, `---` thematic
    breaks after list items or under `### Subsection` would be
    misclassified as setext underlines, prematurely terminating the
    section and dropping subsection INVs.
    """
    if not line.strip():
        return False
    if _BLOCK_MARKER.match(line):
        return False
    if line.startswith("    "):
        return False
    if _ANY_HEADING.match(line):
        return False
    return True


def _extract_safety_rules_section(text: str) -> str | None:
    """Return the body of the first §Safety Rules section, or None.

    Section ends at the next ATX or setext heading at the same or
    shallower depth, or EOF. Subsection headings (deeper depth) stay
    inside the section. Setext underlines (`===`, `---`) are recognized
    when the preceding line is paragraph-shaped (see `_is_setext_text`)
    — list markers and blockquotes are excluded so a `---` thematic
    break after a list item is not misclassified as an H2 boundary.

    Callers should pre-strip fenced code blocks and HTML comments
    (see `_strip_markdown_noise`) — this function is line-structural
    and does not re-enter fence/comment state itself.
    """
    lines = text.splitlines()
    start: int | None = None
    level = 0
    for i, line in enumerate(lines):
        m = _SAFETY_HEADING.match(line)
        if m:
            start = i + 1
            level = len(m.group(1))
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start, len(lines)):
        line = lines[j]
        m = _ANY_HEADING.match(line)
        if m and len(m.group(1)) <= level:
            end = j
            break
        if j + 1 < len(lines) and _is_setext_text(line):
            nxt = lines[j + 1]
            if _SETEXT_H1.match(nxt) and level >= 1:
                end = j
                break
            if _SETEXT_H2.match(nxt) and level >= 2:
                end = j
                break
    return "\n".join(lines[start:end])


@dataclass(slots=True, frozen=True)
class InvariantXrefValidator:
    """Validate `invariants_exercised[].invariant_id` against the project guide.

    Source of truth is the project guide's §Safety Rules (AGENTS.md, or
    CLAUDE.md as fallback) — the same convention `keel-refine` Phase 2
    step 5 reads to seed the drafter's `repo_context.invariants[]` list,
    and that `backlog-drafter` is contractually bound to (line 98 of
    backlog-drafter.md). Putting the same parse in the standalone validator
    turns a soft drafter contract into a hard gate that also catches
    post-draft drift (e.g. an invariant renamed in the guide after Binders
    were written).

    Skipped silently when the Binder has no `invariants_exercised` entries
    — a Binder without invariant citations needs no registry.
    """

    binder_path: Path

    def validate(self, doc: Binder) -> list[Finding]:
        invs = doc.get("invariants_exercised", [])
        if not isinstance(invs, list) or not invs:
            return []

        cited: list[tuple[int, str]] = []
        for i, entry in enumerate(invs):
            if isinstance(entry, dict) and isinstance(entry.get("invariant_id"), str):
                cited.append((i, entry["invariant_id"]))
        if not cited:
            return []

        guide_path = _locate_project_guide(self.binder_path)
        if guide_path is None:
            return [Finding(
                path="/invariants_exercised",
                message=(
                    f"cannot resolve invariant IDs: no project guide "
                    f"(AGENTS.md or CLAUDE.md) found within "
                    f"{_GUIDE_SEARCH_DEPTH} levels above {self.binder_path}. "
                    f"Binder cites {len(cited)} invariant(s). Run /keel-adopt "
                    f"(brownfield) or /keel-setup (greenfield) to install a "
                    f"project guide with §Safety Rules."
                ),
            )]

        try:
            text = guide_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            return [Finding(
                path="/invariants_exercised",
                message=f"cannot read {guide_path}: {e}",
            )]

        # Strip fenced code blocks and HTML comments before BOTH section
        # extraction and token extraction. Without this, a fenced `##`
        # inside §Safety Rules could terminate the section early, and
        # illustrative INV tokens inside fences could still register as
        # declared — two symmetric false failure modes.
        scrubbed = _strip_markdown_noise(text)
        section = _extract_safety_rules_section(scrubbed)
        if section is None:
            return [Finding(
                path="/invariants_exercised",
                message=(
                    f"{guide_path} has no '## Safety Rules' section. "
                    f"Binder cites {len(cited)} invariant(s). Add the section "
                    f"and declare your INV-### invariants — run /keel-adopt "
                    f"(brownfield) or /keel-setup (greenfield) to walk through "
                    f"invariant authoring."
                ),
            )]

        declared = set(_INV_TOKEN.findall(section))
        if not declared:
            return [Finding(
                path="/invariants_exercised",
                message=(
                    f"{guide_path} §Safety Rules declares no INV-### tokens. "
                    f"Binder cites {len(cited)} invariant(s). If safety rules "
                    f"haven't been customized yet, run /keel-adopt "
                    f"(brownfield) or /keel-setup (greenfield). If your "
                    f"project has no registered invariants, remove the "
                    f"invariants_exercised entries from this Binder."
                ),
            )]

        findings: list[Finding] = []
        declared_list = ", ".join(sorted(declared))
        for i, inv_id in cited:
            if inv_id not in declared:
                findings.append(Finding(
                    path=f"/invariants_exercised/{i}/invariant_id",
                    message=(
                        f"'{inv_id}' is not declared in {guide_path} "
                        f"§Safety Rules. Add it there, or replace with one "
                        f"of: {declared_list}."
                    ),
                ))
        return findings


# --- Schema loader ----------------------------------------------------------

SCHEMA_REL = Path("schemas") / "binder.schema.json"
# How far up the tree to search. The script lives at scripts/ in both
# the KEEL source tree and user installs; the schema is a sibling dir
# (schemas/) one level up. A small cap keeps the search bounded and
# prevents an unrelated `schemas/binder.schema.json` in a grandparent
# directory from silently winning.
_SCHEMA_SEARCH_DEPTH = 4


def load_schema() -> dict:
    """Locate schemas/binder.schema.json by walking up from the script location.

    Note: `importlib.resources` is the idiomatic loader for resources
    bundled in an installable Python package. KEEL scripts ship as
    standalone files, not as a packaged Python distribution, so a
    path-anchored lookup is the right tool for this context.
    See AGENTS.md §Python conventions.
    """
    here = Path(__file__).resolve().parent
    candidates = [here, *list(here.parents)[:_SCHEMA_SEARCH_DEPTH]]
    for candidate in candidates:
        schema_path = candidate / SCHEMA_REL
        if schema_path.is_file() and not schema_path.is_symlink():
            return json.loads(schema_path.read_text(encoding="utf-8"))
    raise FileNotFoundError(
        f"Could not locate {SCHEMA_REL} within {_SCHEMA_SEARCH_DEPTH} levels "
        f"above {here}. Run from a KEEL-installed repo or framework source tree."
    )


# --- Output -----------------------------------------------------------------

def render(fmt: str, findings: list[Finding], binder_path: Path) -> str:
    match fmt:
        case "human":
            if not findings:
                return f"OK: {binder_path} is a valid KEEL Binder."
            lines = [f"Binder validation FAILED for {binder_path}:"]
            lines.extend(f"  {f.path}: {f.message}" for f in findings)
            lines.extend([
                "",
                "Resolve each finding (see message — some require editing "
                "the Binder, others the project guide), then re-run:",
                f"  uv run scripts/validate-binder-json.py {binder_path}",
            ])
            return "\n".join(lines)
        case "json":
            return json.dumps(
                {
                    "binder": str(binder_path),
                    "passed": not findings,
                    "findings": [
                        {"path": f.path, "message": f.message} for f in findings
                    ],
                },
                indent=2,
            )
        case _:
            raise ValueError(f"unknown --format '{fmt}'; choose human or json")


# --- Entrypoint -------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a KEEL structured (JSON) Binder.",
    )
    parser.add_argument("binder", type=Path, help="Path to a structured Binder JSON file")
    parser.add_argument(
        "--format",
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )
    args = parser.parse_args()

    if not args.binder.is_file():
        print(f"halt: Binder not found at {args.binder}", file=sys.stderr)
        return 2

    try:
        doc = json.loads(args.binder.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(
            f"halt: {args.binder} is not valid JSON: "
            f"{e.msg} (line {e.lineno}, col {e.colno})",
            file=sys.stderr,
        )
        return 2
    except UnicodeDecodeError as e:
        print(
            f"halt: {args.binder} is not UTF-8 text: {e.reason} "
            f"(byte {e.start}-{e.end}). Binder files must be UTF-8 JSON.",
            file=sys.stderr,
        )
        return 2

    try:
        schema = load_schema()
    except FileNotFoundError as e:
        print(f"halt: {e}", file=sys.stderr)
        return 2

    # Three-stage validation: schema first, then xref stages only if
    # schema is clean. Xref validators assume the document has the shape
    # schema enforces; running them against a shape-invalid doc would
    # mask the schema errors with Python traceback noise. The two xref
    # stages are independent — combine their findings so the human sees
    # every problem at once (P7).
    findings = SchemaValidator(schema=schema).validate(doc)
    if not findings:
        findings = (
            XrefValidator().validate(doc)
            + InvariantXrefValidator(binder_path=args.binder).validate(doc)
        )

    print(render(args.format, findings, args.binder))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
