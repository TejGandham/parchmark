#!/usr/bin/env python3
"""PreToolUse hook: reminds about running /safety-check when editing
files that touch ParchMark's critical domain modules.

Fires BEFORE the edit happens. Non-blocking — it only surfaces an
additionalContext reminder; the safety-auditor agent is the actual gate.

Critical file set is aligned with the domain invariants in
docs/design-docs/core-beliefs.md:
  - /auth/         — OIDC validation, JWT handling, password hashing
  - /routers/      — tenant isolation, auth dependency, typed bodies
  - /models/       — schema (embedding dim parity, password_hash column)
  - /services/embeddings  — generate_embedding contract, dimension constant
  - /database/     — engine, session DI, extension bootstrap
"""

import json
import sys

input_data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}
file_path = input_data.get("tool_input", {}).get("file_path", "")

if not file_path:
    sys.exit(0)

CRITICAL_PATTERNS = [
    "/backend/app/auth/",
    "/backend/app/routers/",
    "/backend/app/models/",
    "/backend/app/services/embeddings",
    "/backend/app/database/",
]

if any(pattern in file_path for pattern in CRITICAL_PATTERNS):
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": (
                "KEEL SAFETY: You are editing a file that touches one of "
                "ParchMark's nine domain invariants (see "
                "docs/design-docs/core-beliefs.md). Run /safety-check "
                "before committing."
            ),
        }
    }
    json.dump(output, sys.stdout)

sys.exit(0)
