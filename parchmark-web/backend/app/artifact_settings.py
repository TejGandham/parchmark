"""
Artifact settings read from the environment at import.

ARTIFACT_CONTENT_ORIGIN is the scheme and host that serve artifact content at
/a/<slug>, for example https://artifacts.example.com. It must be a separate
origin from the app in production (see docs/PRODUCTION_DEPLOYMENT.md). Share
links are built from it, so the process refuses to start without a valid value.
"""

import os
from urllib.parse import urlsplit


def _content_origin(value: str | None) -> str:
    """Return the origin without a trailing slash, or raise ValueError if it is not a bare http(s) origin."""
    if not value:
        raise ValueError(
            "ARTIFACT_CONTENT_ORIGIN environment variable is not set.\n"
            "Set it to the scheme and host that serve artifact content, e.g. ARTIFACT_CONTENT_ORIGIN=http://localhost:8000"
        )
    origin = value.rstrip("/")
    parts = urlsplit(origin)
    if parts.scheme not in ("http", "https") or not parts.netloc or parts.path or parts.query or parts.fragment:
        raise ValueError(
            f"ARTIFACT_CONTENT_ORIGIN must be an http or https origin with a host and no path, query or fragment; "
            f"got {value!r}"
        )
    return origin


ARTIFACT_CONTENT_ORIGIN: str = _content_origin(os.getenv("ARTIFACT_CONTENT_ORIGIN"))
