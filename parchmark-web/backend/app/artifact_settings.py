"""
Artifact settings read from the environment at import.

ARTIFACT_CONTENT_ORIGIN is the scheme and host that serve artifact content at
/a/<slug>, for example https://artifacts.example.com. It must be a separate
origin from the app in production (see docs/PRODUCTION_DEPLOYMENT.md). Share
links are built from it, so the process refuses to start without a valid value.

ARTIFACT_SIGNING_KEY is the dedicated HMAC key that signs the owner's short-lived
view links (see app.services.artifact_service). It is never derived from
SECRET_KEY: the process refuses to start when it is unset, shorter than 32
characters, or equal to SECRET_KEY.
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


_MIN_SIGNING_KEY_LENGTH = 32


def _signing_key(value: str | None, secret_key: str | None) -> str:
    """Return the view-link signing key, or raise ValueError if it is missing, short, or reuses SECRET_KEY."""
    if not value or len(value) < _MIN_SIGNING_KEY_LENGTH:
        raise ValueError(
            f"ARTIFACT_SIGNING_KEY environment variable must be set to at least {_MIN_SIGNING_KEY_LENGTH} characters.\n"
            "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    if value == secret_key:
        raise ValueError("ARTIFACT_SIGNING_KEY must differ from SECRET_KEY; it is a dedicated key for view links")
    return value


ARTIFACT_SIGNING_KEY: str = _signing_key(os.getenv("ARTIFACT_SIGNING_KEY"), os.getenv("SECRET_KEY"))
