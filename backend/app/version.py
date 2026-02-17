"""
Single source of truth for ParchMark version information.

At build time, GIT_SHA and BUILD_DATE are injected via Docker build args.
At runtime, they're read from environment variables.
In development, they fall back to "dev" / "unknown".

Human-readable:  v1.1.0 (45300c8) built 2026-02-16
Machine-readable: {"version": "1.1.0", "gitSha": "45300c8", "buildDate": "2026-02-16T18:50:13Z"}
"""

import os

VERSION = "1.1.0"

GIT_SHA = os.getenv("GIT_SHA", "dev")

BUILD_DATE = os.getenv("BUILD_DATE", "unknown")


def get_version_info() -> dict:
    """Return version info dict suitable for JSON responses."""
    return {
        "version": VERSION,
        "gitSha": GIT_SHA,
        "buildDate": BUILD_DATE,
    }


def get_version_string() -> str:
    """Return human-readable version string, e.g. 'v1.1.0 (45300c8)'."""
    sha_display = GIT_SHA[:7] if len(GIT_SHA) > 7 else GIT_SHA
    return f"v{VERSION} ({sha_display})"
