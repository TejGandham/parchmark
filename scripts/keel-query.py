#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# ///
"""KEEL handoff read helper (operator ergonomics).

Read-side wrapper for routing.json + resolved-work-item.json. Agents
DO NOT depend on this script — they use the Read tool on the JSON
files directly. This script is for orchestrator scripting, CI checks,
and human inspection.

Subcommands:
  routing <handoff_dir> <jq-style-path>      — read a routing.json field
  resolved <handoff_dir> <jq-style-path>     — read a resolved-work-item.json field
  deliberation <handoff_dir> <touchpoint>    — concat deliberation attempts in numeric order
  list-files <handoff_dir>                   — list expected vs actual files

Path syntax (routing / resolved):
  Dot-separated keys with [N] array indices. Pure stdlib; no jq.
  Examples:  feature.title   dependencies.intra_binder[0].id   status

Exit codes:
  0  read succeeded
  1  field / file / attempt not found (the read failed)
  2  invocation error (bad path syntax, malformed JSON, unknown subcommand)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# A path segment is either a key (bareword) or a [N] index. We tokenize a
# path like `dependencies.intra_binder[0].id` into ["dependencies",
# "intra_binder", 0, "id"], where ints denote array indices.
_SEGMENT_RE = re.compile(r"[^.\[\]]+|\[\d+\]")
# Deliberation attempt files: attempt-<int>.md (at least one digit).
_ATTEMPT_RE = re.compile(r"^attempt-(\d+)\.md$")

# The two orchestrator-owned anchor files every standard handoff dir has.
# resolved-work-item.json is absent for bootstrap features (Binder-exempt), so
# list-files reports it as a status, not a hard requirement.
_ANCHORS = ("routing.json", "resolved-work-item.json")


def _parse_path(path: str) -> list[str | int] | None:
    """Tokenize a jq-style path into keys (str) and array indices (int).

    Returns None if the syntax is malformed (so callers emit a P7 halt
    with a concrete next step rather than a stack trace).
    """
    if not path:
        return None
    tokens = _SEGMENT_RE.findall(path)
    # Reassembling the tokens must reproduce the input minus the `.`
    # separators; anything left over means stray characters we don't grok.
    if "".join(tokens) != path.replace(".", ""):
        return None
    out: list[str | int] = []
    for tok in tokens:
        if tok.startswith("["):
            out.append(int(tok[1:-1]))
        else:
            out.append(tok)
    return out


def _navigate(doc: Any, segments: list[str | int]) -> tuple[bool, Any]:
    """Walk `segments` into `doc`. Returns (found, value)."""
    cur = doc
    for seg in segments:
        match seg:
            case int():
                if not isinstance(cur, list) or not (0 <= seg < len(cur)):
                    return (False, None)
                cur = cur[seg]
            case str():
                if not isinstance(cur, dict) or seg not in cur:
                    return (False, None)
                cur = cur[seg]
    return (True, cur)


def _format_value(value: Any) -> str:
    """Render a JSON-loaded value for stdout.

    Scalars print bare (so `routing ... feature.id` yields `WI22`, not
    `"WI22"`); containers print as compact JSON for further piping.
    """
    match value:
        case str():
            return value
        case bool():
            return "true" if value else "false"
        case None:
            return "null"
        case int() | float():
            return json.dumps(value)
        case _:
            return json.dumps(value, ensure_ascii=False)


def _load_json(handoff_dir: Path, filename: str) -> tuple[int, Any]:
    """Load <handoff_dir>/<filename>. Returns (exit_code, doc).

    exit_code 0 with doc on success; nonzero with None on failure (and a
    P7-style halt already printed to stderr).
    """
    target = handoff_dir / filename
    if not target.is_file():
        print(
            f"halt: {filename} not found at {target}.\n"
            f"  Next: confirm the handoff dir is correct and that Step 0 "
            f"wrote {filename} (bootstrap features have no "
            f"resolved-work-item.json).",
            file=sys.stderr,
        )
        return (1, None)
    try:
        return (0, json.loads(target.read_text(encoding="utf-8")))
    except json.JSONDecodeError as e:
        print(
            f"halt: {target} is not valid JSON: {e.msg} "
            f"(line {e.lineno}, col {e.colno}).\n"
            f"  Next: the orchestrator owns this file — re-run the step "
            f"that wrote it rather than hand-editing.",
            file=sys.stderr,
        )
        return (2, None)
    except UnicodeDecodeError as e:
        print(
            f"halt: {target} is not UTF-8 text: {e.reason} "
            f"(byte {e.start}-{e.end}).",
            file=sys.stderr,
        )
        return (2, None)


def _read_field(handoff_dir: Path, filename: str, path: str) -> int:
    segments = _parse_path(path)
    if segments is None:
        print(
            f"halt: malformed path '{path}'. Use dot-separated keys with "
            f"[N] array indices, e.g. dependencies.intra_binder[0].id.",
            file=sys.stderr,
        )
        return 2

    rc, doc = _load_json(handoff_dir, filename)
    if doc is None:
        return rc

    found, value = _navigate(doc, segments)
    if not found:
        print(
            f"halt: path '{path}' not found in {handoff_dir / filename}.\n"
            f"  Next: run `keel-query.py "
            f"{'resolved' if filename.startswith('resolved') else 'routing'}"
            f" {handoff_dir}` against a known-good path, or inspect the "
            f"file with the Read tool to see available keys.",
            file=sys.stderr,
        )
        return 1

    print(_format_value(value))
    return 0


def _read_deliberation(handoff_dir: Path, touchpoint: str) -> int:
    review_dir = handoff_dir / f"{touchpoint}-review"
    if not review_dir.is_dir():
        print(
            f"halt: deliberation dir '{review_dir.name}' not found under "
            f"{handoff_dir}.\n"
            f"  Next: confirm the touchpoint name (e.g. precheck, design, "
            f"landing) and that the panel ran for this feature.",
            file=sys.stderr,
        )
        return 1

    attempts: list[tuple[int, Path]] = []
    for entry in review_dir.iterdir():
        if not entry.is_file():
            continue
        m = _ATTEMPT_RE.match(entry.name)
        if m:
            attempts.append((int(m.group(1)), entry))

    if not attempts:
        print(
            f"halt: no attempt-N.md files in {review_dir}.\n"
            f"  Next: the review panel writes attempt-01.md (and -02, -03 "
            f"on kickback) — confirm the panel ran and wrote here.",
            file=sys.stderr,
        )
        return 1

    # Sort by parsed integer, NOT lexicographic: attempt-10 must follow
    # attempt-2, not precede it.
    attempts.sort(key=lambda pair: pair[0])
    bodies = [p.read_text(encoding="utf-8") for _, p in attempts]
    sys.stdout.write("\n\n---\n\n".join(bodies))
    return 0


def _list_files(handoff_dir: Path) -> int:
    if not handoff_dir.is_dir():
        print(
            f"halt: handoff dir not found at {handoff_dir}.\n"
            f"  Next: confirm the WI##-<slug> path under "
            f"docs/exec-plans/active/handoffs/.",
            file=sys.stderr,
        )
        return 1

    # Best-effort heuristic: the precise set of conditional agent/gate
    # files is derivable only from routing.json's routing flags + pipeline
    # variant (see design doc "Directory layout"). Rather than re-derive
    # that here (a cache that would stale, P4), we report the two anchor
    # files' presence as a status and then list everything actually on
    # disk, including deliberation subdirs. This stays self-sufficient
    # (P3): the listing reflects current state, not a precomputed manifest.
    print("anchors:")
    for anchor in _ANCHORS:
        present = (handoff_dir / anchor).is_file()
        mark = "present" if present else "MISSING"
        print(f"  {anchor}: {mark}")

    print("actual:")
    for entry in sorted(handoff_dir.iterdir(), key=lambda p: p.name):
        suffix = "/" if entry.is_dir() else ""
        print(f"  {entry.name}{suffix}")
        if entry.is_dir():
            for sub in sorted(entry.iterdir(), key=lambda p: p.name):
                print(f"    {sub.name}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read fields and deliberation from a KEEL handoff dir.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_routing = sub.add_parser("routing", help="read a routing.json field")
    p_routing.add_argument("handoff_dir", type=Path)
    p_routing.add_argument("path", help="dot/[N] path, e.g. feature.id")

    p_resolved = sub.add_parser(
        "resolved", help="read a resolved-work-item.json field",
    )
    p_resolved.add_argument("handoff_dir", type=Path)
    p_resolved.add_argument(
        "path", help="dot/[N] path, e.g. dependencies.intra_binder[0].id",
    )

    p_delib = sub.add_parser(
        "deliberation", help="concat deliberation attempts in numeric order",
    )
    p_delib.add_argument("handoff_dir", type=Path)
    p_delib.add_argument(
        "touchpoint", help="touchpoint name, e.g. precheck, design, landing",
    )

    p_list = sub.add_parser(
        "list-files", help="list anchor status + actual files",
    )
    p_list.add_argument("handoff_dir", type=Path)

    args = parser.parse_args()

    match args.command:
        case "routing":
            return _read_field(args.handoff_dir, "routing.json", args.path)
        case "resolved":
            return _read_field(
                args.handoff_dir, "resolved-work-item.json", args.path,
            )
        case "deliberation":
            return _read_deliberation(args.handoff_dir, args.touchpoint)
        case "list-files":
            return _list_files(args.handoff_dir)
        case _:  # argparse(required=True) makes this unreachable
            parser.error(f"unknown command: {args.command}")
            return 2


if __name__ == "__main__":
    sys.exit(main())
