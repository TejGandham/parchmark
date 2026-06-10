#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = ["jsonschema>=4.25"]
# ///
"""Validate a KEEL prototype manifest against schemas/prototype.schema.json.

Single-stage validation: structural shape only. The prototype manifest
authors no cross-references — `entry` is a path inside the bundle and
existence-on-disk is the responsibility of `keel-refine` Phase 1 (which
enumerates the bundle to populate the manifest in the first place).
Validating path-existence here would re-do work the skill already did
and would fail when the validator runs against a bundle in a different
filesystem layout (e.g. test fixtures, dry-run inspection).

Usage:
  uv run scripts/validate-prototype-json.py path/to/prototype.json [--format human|json]

Exit codes:
  0  validation passed
  1  validation failed (findings reported to stdout)
  2  invocation error (file not found, not JSON, etc.)
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from jsonschema import Draft202012Validator


class Screen(TypedDict, total=False):
    label: str
    path: str
    states: list[str]


class Prototype(TypedDict, total=False):
    schema_version: int
    entry: str
    mode: str
    stack_match: bool
    screens: list[Screen]
    notes: str


@dataclass(slots=True, frozen=True)
class Finding:
    path: str
    message: str


SCHEMA_REL = Path("schemas") / "prototype.schema.json"
_SCHEMA_SEARCH_DEPTH = 4


def load_schema() -> dict:
    """Locate schemas/prototype.schema.json by walking up from the script.

    Mirrors validate-binder-json.py — KEEL scripts ship as standalone files,
    so a path-anchored lookup is the right tool. See AGENTS.md §Python
    conventions.
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


def validate(doc: Prototype, schema: dict) -> list[Finding]:
    v = Draft202012Validator(schema)
    errors = sorted(v.iter_errors(doc), key=lambda e: list(e.absolute_path))
    return [
        Finding(
            path="/" + "/".join(str(p) for p in e.absolute_path),
            message=e.message.split("\n")[0],
        )
        for e in errors
    ]


def render(fmt: str, findings: list[Finding], manifest_path: Path) -> str:
    match fmt:
        case "human":
            if not findings:
                return f"OK: {manifest_path} is a valid KEEL prototype manifest."
            lines = [f"Prototype manifest validation FAILED for {manifest_path}:"]
            lines.extend(f"  {f.path}: {f.message}" for f in findings)
            lines.extend([
                "",
                "Resolve each finding, then re-run:",
                f"  uv run scripts/validate-prototype-json.py {manifest_path}",
            ])
            return "\n".join(lines)
        case "json":
            return json.dumps(
                {
                    "manifest": str(manifest_path),
                    "passed": not findings,
                    "findings": [
                        {"path": f.path, "message": f.message} for f in findings
                    ],
                },
                indent=2,
            )
        case _:
            raise ValueError(f"unknown --format '{fmt}'; choose human or json")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a KEEL prototype manifest (JSON).",
    )
    parser.add_argument(
        "manifest",
        type=Path,
        help="Path to a prototype.json manifest file",
    )
    parser.add_argument(
        "--format",
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )
    args = parser.parse_args()

    if not args.manifest.is_file():
        print(f"halt: prototype manifest not found at {args.manifest}", file=sys.stderr)
        return 2

    try:
        doc = json.loads(args.manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(
            f"halt: {args.manifest} is not valid JSON: "
            f"{e.msg} (line {e.lineno}, col {e.colno})",
            file=sys.stderr,
        )
        return 2
    except UnicodeDecodeError as e:
        print(
            f"halt: {args.manifest} is not UTF-8 text: {e.reason} "
            f"(byte {e.start}-{e.end}). Manifest files must be UTF-8 JSON.",
            file=sys.stderr,
        )
        return 2

    try:
        schema = load_schema()
    except FileNotFoundError as e:
        print(f"halt: {e}", file=sys.stderr)
        return 2

    findings = validate(doc, schema)
    print(render(args.format, findings, args.manifest))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
