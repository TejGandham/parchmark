"""
Single source of truth for ParchMark version information.

VERSION uses CalVer format: YYYYMMDD.HHMM.{short_sha}
e.g. "20260218.2110.cd63a25"

At build time, APP_VERSION, GIT_SHA, and BUILD_DATE are injected via
Docker build args.  At runtime they're read from environment variables.
In development, they fall back to "dev" / "unknown".
"""

import os

VERSION = os.getenv("APP_VERSION", "dev")

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
    """Return human-readable version string, e.g. '20260218.2110.cd63a25 (cd63a25)'."""
    sha_display = GIT_SHA[:7] if len(GIT_SHA) > 7 else GIT_SHA
    return f"{VERSION} ({sha_display})"
