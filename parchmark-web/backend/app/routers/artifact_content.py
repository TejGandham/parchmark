"""
Public artifact content route: GET and HEAD /a/<slug>.

Returns the raw content of an unlisted artifact's current version, without
authentication. A request carrying any of the query parameters v, e or s takes
the signed path instead: it serves exactly version v of any artifact, private
or not, only when s is a valid view-link signature of slug:v:e and e lies in
the next 300 seconds (see app.services.artifact_service). Every failure, on
either path, gets one constant 404 that says nothing about the slug, and the
route never reads the Authorization header or any cookie. The route is meant to be reached only through the
content origin, a host separate from the app (see docs/PRODUCTION_DEPLOYMENT.md). The web viewer frames it in an iframe whose
sandbox attribute never carries allow-same-origin.

Artifact content is untrusted. Every content response carries a Content-Security-Policy
that blocks all network loads, form submission and plugins, and whose sandbox
directive gives the document an opaque origin, so even a page opened directly
can read no cookies or storage of this origin or any other. Only HTML may run
scripts, and only inline ones. The route sets no cookies and ignores any it is sent.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_async_db
from app.services import artifact_service

router = APIRouter(prefix="/a", tags=["artifacts"])

# Self-contained documents only: inline styles plus data:/blob: images and fonts, nothing from the network.
_BASE_POLICY = (
    "default-src 'none'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; "
    "base-uri 'none'; form-action 'none'"
)

# content_type -> (Content-Type, policy additions). SVG is served as an image and markdown as plain text;
# neither may run scripts.
_SERVED_AS: dict[str, tuple[str, str]] = {
    "html": ("text/html; charset=utf-8", "script-src 'unsafe-inline'; sandbox allow-scripts"),
    "svg": ("image/svg+xml; charset=utf-8", "sandbox"),
    "markdown": ("text/plain; charset=utf-8", "sandbox"),
}


_COMMON_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    # The slug is the read capability; never leak it to sites the artifact links to.
    "Referrer-Policy": "no-referrer",
    # A visibility change back to private must take effect at once, so no cache may keep a copy.
    "Cache-Control": "no-store",
}


def _not_found() -> Response:
    """The one 404 for private and unknown slugs alike. Built here rather than raised as HTTPException,
    because the global HTTPException handler echoes the request path, and with it the slug, in its body."""
    return Response("Not found", status_code=404, media_type="text/plain; charset=utf-8", headers=_COMMON_HEADERS)


# KARTA-SME-OVERRIDE(fapi.1): raw artifact bytes have no Pydantic shape; the route declares response_class=Response
# and sets the media type per content type. HEAD runs the same lookup, so it answers every request with GET's status
# and headers; the server drops the body.
@router.api_route("/{slug}", methods=["GET", "HEAD"], response_class=Response)
async def read_artifact_content(
    slug: str,
    v: str | None = None,
    e: str | None = None,
    s: str | None = None,
    db: AsyncSession = Depends(get_async_db),
) -> Response:
    """Return an artifact version's raw content under a sandboxing Content-Security-Policy.

    Without v, e and s: the current version of an unlisted artifact. With any of them: the signed path, which
    never falls back to the unlisted one. v, e and s are plain strings so a malformed value is the 404, not a 422.
    """
    if v is None and e is None and s is None:
        version = await artifact_service.get_unlisted_version(db, slug)
    else:
        version = await artifact_service.get_signed_version(db, slug, v, e, s)
    if version is None:
        return _not_found()
    media_type, policy = _SERVED_AS[version.content_type]
    return Response(
        version.content,
        media_type=media_type,
        headers={"Content-Security-Policy": f"{_BASE_POLICY}; {policy}", **_COMMON_HEADERS},
    )
