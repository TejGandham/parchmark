#!/usr/bin/env python3
"""Validate invariant 7 across the backlog + PRD files.

Stdlib-only. Python 3.10+. Cross-platform.

See docs/design-docs/2026-04-23-keel-prd-scope-design.md §"Validator"
and docs/process/KEEL-PRINCIPLES.md for the principles this enforces.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ALLOWED_EXEMPT_REASONS = {"legacy", "bootstrap", "infra", "trivial"}
MARKER_RE = re.compile(r"<!--\s*KEEL-INVARIANT-7:\s*legacy-through=F(\d+)\s*-->")
# Slug alphabet mirrors SLUG_RE in scripts/keel-prd-view.py: a PRD slug must
# start AND end with [a-z0-9] so the viewer accepts it. Rejects trailing-hyphen
# forms like "foo-" or "foo--". Keeping the alphabets aligned prevents
# validate-prds from silently blessing slugs (e.g. "-foo", "foo-") that the
# viewer would later reject. Single-char slugs (e.g. "a") still match.
PRD_FIELD_RE = re.compile(r"^\s*PRD:\s*([a-z0-9](?:[a-z0-9-]*[a-z0-9])?)\s*$", re.MULTILINE)
PRD_EXEMPT_RE = re.compile(r"^\s*PRD-exempt:\s*(\S+)", re.MULTILINE)
F_PROSE_RE = re.compile(r"(?<![#/\w])F\d{2,}\b")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate invariant 7 PRD integrity.")
    p.add_argument(
        "--repo",
        default=".",
        help="Repo root to validate (default: current directory).",
    )
    return p.parse_args()


def halt(msg: str) -> None:
    """Halt with a call-to-action (P7)."""
    print(f"validate-prds: HALT — {msg}", file=sys.stderr)
    sys.exit(1)


def find_backlog(repo: Path) -> Path:
    backlog = repo / "docs" / "exec-plans" / "active" / "feature-backlog.md"
    if not backlog.exists():
        halt(
            f"no feature-backlog.md at {backlog}. "
            "Validate expects the canonical KEEL backlog path."
        )
    return backlog


def read_marker(backlog_text: str) -> int | None:
    """Return the legacy-through F## number, or None if marker absent."""
    m = MARKER_RE.search(backlog_text)
    return int(m.group(1)) if m else None


def strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks (backtick or tilde) and inline code spans.

    Prevents ``F##`` tokens appearing in legitimate code examples from
    triggering false positives in the PRD prose scope lint. Markdown
    supports both ```` ``` ```` and ``~~~`` fences; both must be stripped
    or a PRD using tilde fences silently bypasses the lint.
    """
    # Backtick fences (``` ... ```), including multi-line content.
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Tilde fences (~~~ ... ~~~).
    text = re.sub(r"~~~.*?~~~", "", text, flags=re.DOTALL)
    # Inline code spans (`...`).
    text = re.sub(r"`[^`\n]+`", "", text)
    return text


def parse_f_entries(backlog_text: str) -> list[dict]:
    """Parse F## entries. Each entry: {id, text, prd, exempt}.

    Terminates an entry on:
      - the next F## bullet line,
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
        match = re.match(r"\s*-\s*\[[ x]\]\s*\*\*F(\d+)\s", line)
        if match:
            # New F## entry starts — close previous if open.
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

    # Extract PRD: and PRD-exempt: from each entry's text.
    for e in entries:
        prd_matches = PRD_FIELD_RE.findall(e["text"])
        exempt_matches = PRD_EXEMPT_RE.findall(e["text"])
        e["prd_lines"] = prd_matches
        e["exempt_lines"] = exempt_matches

    return entries


def validate(repo: Path) -> list[str]:
    """Return list of error messages. Empty list = valid."""
    errors: list[str] = []
    backlog = find_backlog(repo)
    backlog_text = backlog.read_text(encoding="utf-8")

    cutoff = read_marker(backlog_text)
    entries = parse_f_entries(backlog_text)
    prd_dir = repo / "docs" / "exec-plans" / "prds"

    # Track referenced PRDs for orphan detection.
    referenced_slugs: set[str] = set()

    for entry in entries:
        fid = entry["id"]
        grandfathered = cutoff is not None and fid <= cutoff
        prds = entry["prd_lines"]
        exempts = entry["exempt_lines"]

        # Cardinality check: at most one PRD: line.
        if len(prds) > 1:
            errors.append(
                f"F{fid:02d} has multiple PRD: lines. "
                "PRD: is single-valued (cross-PRD work must split). "
                "Fix: consolidate to a single PRD: line."
            )

        # Cardinality check: at most one PRD-exempt: line.
        if len(exempts) > 1:
            errors.append(
                f"F{fid:02d} has multiple PRD-exempt: lines. "
                "Only one exemption reason per entry. "
                "Fix: consolidate to a single PRD-exempt: line."
            )

        # XOR check: PRD: and PRD-exempt: are mutually exclusive.
        # An entry is either covered by a PRD or exempted — never both.
        # This takes precedence over the missing-link check below.
        if prds and exempts:
            errors.append(
                f"F{fid:02d} has both PRD: and PRD-exempt: lines. "
                "These are mutually exclusive — pick one. "
                "Fix: remove the PRD-exempt line if this feature has a PRD, "
                "or remove the PRD line if this is genuinely exempt."
            )
            # Record the PRD ref anyway to prevent a spurious orphan cascade.
            # Without this, the PRD file foo.md would be falsely flagged as
            # orphaned, producing a second confusing error from the same root.
            if prds[0]:
                referenced_slugs.add(prds[0])
            continue  # skip further checks; the entry is structurally broken

        if cutoff is None:
            # Pre-adoption grace: don't enforce per-entry.
            if prds:
                referenced_slugs.add(prds[0])
            continue

        if grandfathered:
            if prds:
                referenced_slugs.add(prds[0])
            continue

        # Post-cutoff: must have PRD: or PRD-exempt:.
        if not prds and not exempts:
            errors.append(
                f"F{fid:02d} is past the legacy cutoff F{cutoff:02d}; missing PRD: and PRD-exempt:. "
                f"Fix: add PRD: <slug> pointing at docs/exec-plans/prds/<slug>.md, "
                f"or add PRD-exempt: <reason> where reason is one of "
                f"{sorted(ALLOWED_EXEMPT_REASONS)}."
            )
            continue

        if prds:
            slug = prds[0]
            prd_path = prd_dir / f"{slug}.md"
            if not prd_path.exists():
                errors.append(
                    f"F{fid:02d} references PRD '{slug}' but "
                    f"{prd_path} does not exist. "
                    f"Fix: create the PRD file, rename the slug, or mark "
                    f"F{fid:02d} as PRD-exempt with a valid reason."
                )
            referenced_slugs.add(slug)

        for reason in exempts:
            if reason not in ALLOWED_EXEMPT_REASONS:
                errors.append(
                    f"F{fid:02d} declares PRD-exempt with reason '{reason}'; "
                    f"must be one of {sorted(ALLOWED_EXEMPT_REASONS)}; "
                    f"got '{reason}'."
                )

    # Orphan detection: PRD files with no references.
    if prd_dir.exists():
        for prd_file in prd_dir.glob("*.md"):
            if prd_file.stem not in referenced_slugs:
                errors.append(
                    f"PRD file {prd_file} is not referenced by any F## in the backlog. "
                    f"Fix: either delete the orphaned PRD or add F## entries that reference it."
                )

            # Scope lint: no F## IDs in prose (ignore fenced/inline code).
            text = prd_file.read_text(encoding="utf-8")
            stripped_text = strip_code_blocks(text)
            for m in F_PROSE_RE.finditer(stripped_text):
                errors.append(
                    f"PRD prose {prd_file} contains F## reference '{m.group(0)}'. "
                    f"Narrative must use theme-level language, not IDs. "
                    f"Fix: rewrite the prose to describe themes/scope; use "
                    f"scripts/keel-prd-view.py {prd_file.stem} when you need the feature list."
                )

    return errors


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    errors = validate(repo)
    if errors:
        for e in errors:
            print(f"validate-prds: {e}", file=sys.stderr)
        print(f"\nvalidate-prds: {len(errors)} problem(s) found.", file=sys.stderr)
        return 1
    print("validate-prds: OK — invariant 7 compliant.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
