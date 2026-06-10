#!/usr/bin/env python3
"""PreToolUse hook: reminds about safety check when editing critical modules.
Non-blocking — emits an advisory `additionalContext` reminder to run
/safety-check; never denies the edit (always exits 0).

CUSTOMIZE: Update the file pattern matchers below to match your project's
critical modules (the ones where domain invariant violations would be dangerous).

Examples:
    Git project:  */git.ex, */git/*.ex, */repo_server.ex
    API project:  */auth/*, */middleware/*, */db/queries/*
    Data pipeline: */transforms/*, */ingestion/*, */schema/*
"""

import json
import sys

try:
    input_data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}
except (json.JSONDecodeError, ValueError):
    # Malformed/empty stdin: degrade to a clean no-op rather than crash.
    # This hook is advisory-only, so a clean exit 0 never blocks the edit.
    sys.exit(0)


def _edited_path(data):
    """Extract the edited file path, dual-payload (Claude + Codex).

    Claude Code's Edit/Write payload carries `tool_input.file_path`. Codex
    runs edits via apply_patch and may name the field `path`/`filename`; the
    exact Codex tool-input shape is a Phase 5 live re-verification item, so we
    check the known candidates and no-op (advisory) if none is present.
    """
    ti = data.get("tool_input", {}) or {}
    for key in ("file_path", "path", "filename"):
        val = ti.get(key)
        if isinstance(val, str) and val:
            return val
    return ""


file_path = _edited_path(input_data)

if not file_path:
    sys.exit(0)

# CUSTOMIZE: Replace this pattern with your critical file paths
CRITICAL_PATTERNS = [
    "REPLACE_WITH_YOUR_CRITICAL_PATTERN",
]

if any(pattern in file_path for pattern in CRITICAL_PATTERNS):
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": "KEEL SAFETY: You are editing a file that touches critical domain operations. Run /safety-check before committing.",
        }
    }
    json.dump(output, sys.stdout)
