#!/usr/bin/env python3
"""PostToolUse hook: reminds Claude to run doc-gardener after git commits.
Fires AFTER the commit succeeds.
"""

import json
import sys

try:
    input_data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}
except (json.JSONDecodeError, ValueError):
    # Malformed/empty stdin: advisory hook, degrade to a clean no-op.
    sys.exit(0)


def _command_str(data):
    """Extract the shell command, dual-payload (Claude + Codex).

    Claude Code's Bash payload carries `tool_input.command` as a string.
    Codex runs shell via its own tool and may pass an argv LIST; joining it
    keeps the `git commit` substring match working. The exact Codex shell
    tool-input shape is a Phase 5 live re-verification item.
    """
    cmd = (data.get("tool_input", {}) or {}).get("command", "")
    if isinstance(cmd, list):
        return " ".join(str(part) for part in cmd)
    return cmd if isinstance(cmd, str) else ""


command = _command_str(input_data)

if not command:
    sys.exit(0)

if "git commit" in command:
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "KEEL DOCS: Commit detected. Run doc-gardener agent to check for doc drift. (north-star.md: Garbage Collection)",
        }
    }
    json.dump(output, sys.stdout)
