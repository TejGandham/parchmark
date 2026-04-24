#!/usr/bin/env python3
"""Read-time assembler: print PRD narrative + derived F## slice.

Not a synthesizer — just grep + format. Stdlib only.

See docs/design-docs/2026-04-23-keel-prd-scope-design.md §"Day-1 read affordance".
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SPEC_FIELD_RE = re.compile(r"Spec:\s*([^\s|]+)")
# Slug must start AND end with [a-z0-9]. Rejects trailing-hyphen forms
# like "foo-" and "foo--". Single-char slugs (e.g. "a") still match via
# the optional inner group. Mirrors PRD_FIELD_RE in scripts/validate-prds.py.
SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Print PRD view.")
    p.add_argument("slug", help="PRD slug (filename without .md).")
    p.add_argument("--repo", default=".", help="Repo root (default: current directory).")
    return p.parse_args()


def halt(msg: str) -> None:
    print(f"keel-prd-view: HALT — {msg}", file=sys.stderr)
    sys.exit(1)


def parse_f_blocks(backlog_text: str) -> list[dict]:
    """Parse F## entries into blocks. Returns list of {id, status, text}.

    Block terminates on next F##, ## heading, --- hrule, blank+non-indented,
    or EOF. Matches the parser in scripts/validate-prds.py for consistency.
    """
    blocks: list[dict] = []
    lines = backlog_text.splitlines(keepends=True)
    current: dict | None = None
    f_start_re = re.compile(r"\s*-\s*\[([ x])\]\s*\*\*F(\d+)\s")
    for i, line in enumerate(lines):
        match = f_start_re.match(line)
        if match:
            if current is not None:
                blocks.append(current)
            current = {
                "id": match.group(2),
                "status": "[x]" if match.group(1) == "x" else "[ ]",
                "text": line,
            }
            continue
        if current is None:
            continue
        if re.match(r"^\s*##\s", line) or re.match(r"^\s*---\s*$", line):
            blocks.append(current)
            current = None
            continue
        if line.strip() == "":
            next_non_blank = None
            for j in range(i + 1, len(lines)):
                if lines[j].strip() != "":
                    next_non_blank = lines[j]
                    break
            if next_non_blank is None:
                blocks.append(current)
                current = None
                continue
            if not (next_non_blank.startswith(" ") or next_non_blank.startswith("\t")):
                blocks.append(current)
                current = None
                continue
        current["text"] += line
    if current is not None:
        blocks.append(current)
    return blocks


def main() -> int:
    # Pre-check: argparse otherwise intercepts any bare leading-hyphen arg
    # (e.g. `-foo`) as an unknown flag and errors out with a cryptic message
    # before SLUG_RE can emit its useful HALT. Catch that case here.
    if (
        len(sys.argv) > 1
        and sys.argv[1].startswith("-")
        and sys.argv[1] not in ("-h", "--help", "--repo")
        and not sys.argv[1].startswith("--repo=")
    ):
        halt(
            f"Slug '{sys.argv[1]}' is invalid. Must start AND end with "
            "[a-z0-9] (lowercase letters/digits), optionally with hyphens "
            "between. No leading or trailing hyphens. "
            "Example: auth-login, profile-edit."
        )
    args = parse_args()
    if not SLUG_RE.match(args.slug):
        halt(
            f"Slug '{args.slug}' is invalid. Must start AND end with "
            "[a-z0-9] (lowercase letters/digits), optionally with hyphens "
            "between. No leading or trailing hyphens. "
            "Example: auth-login, profile-edit."
        )
    repo = Path(args.repo).resolve()
    prd_path = repo / "docs" / "exec-plans" / "prds" / f"{args.slug}.md"

    if not prd_path.exists():
        halt(
            f"PRD file {prd_path} does not exist. "
            f"Check the slug, or create the PRD at the expected path."
        )

    backlog = repo / "docs" / "exec-plans" / "active" / "feature-backlog.md"
    if not backlog.exists():
        halt(f"feature-backlog.md not found at {backlog}.")

    try:
        rel_source = prd_path.relative_to(repo)
    except ValueError:
        rel_source = prd_path

    print("=" * 72)
    print(f"PRD: {args.slug}")
    print(f"Source: {rel_source}")
    print("=" * 72)
    print()
    print(prd_path.read_text(encoding="utf-8"))
    print()
    print("=" * 72)
    print(f"Features tagged `PRD: {args.slug}` (derived from backlog)")
    print("=" * 72)
    print()

    text = backlog.read_text(encoding="utf-8")
    blocks = parse_f_blocks(text)
    found_any = False
    for block in blocks:
        if not re.search(rf"PRD:\s*{re.escape(args.slug)}\s*$", block["text"], re.MULTILINE):
            continue
        found_any = True
        status = block["status"]
        fid = block["id"]
        title_match = re.search(r"\*\*F\d+\s+([^*]+)\*\*", block["text"])
        title = title_match.group(1).strip() if title_match else "<no title>"
        spec_match = SPEC_FIELD_RE.search(block["text"])
        spec = spec_match.group(1) if spec_match else "<no spec>"
        print(f"  {status} F{fid}  {title}")
        print(f"      Spec: {spec}")
        print()

    if not found_any:
        print(f"  (no F## entries reference PRD: {args.slug})")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
