"""Artifact business logic: publish artifacts and their versions, read and manage them.

Ownership rule: every lookup is filtered by the caller's user id, so another
user's artifact behaves exactly like one that does not exist (404). The one
exception is the unauthenticated read by slug, which only ever finds unlisted
artifacts; a private one is a 404 there, exactly like a missing one. Versions
are append-only; publishing adds the next version number and moves the
artifact's current_version_id to it. Slugs carry 128 bits of randomness and
never change once issued.

View links: the owner can mint a link to /a/<slug>?v=<version>&e=<expiry>&s=<signature> that shows exactly
that version, private or not, for VIEW_LINK_LIFETIME_SECONDS. s is the lowercase hex HMAC-SHA256 of
"<slug>:<version>:<expiry>" under ARTIFACT_SIGNING_KEY, a key of its own that is never SECRET_KEY.
"""

import hashlib
import hmac
import secrets
import time
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.artifact_settings import ARTIFACT_CONTENT_ORIGIN, ARTIFACT_SIGNING_KEY
from app.models.artifact import Artifact
from app.models.artifact_version import ArtifactVersion
from app.models.models import User
from app.schemas.artifact import (
    ArtifactContentResponse,
    ArtifactCreate,
    ArtifactResponse,
    ArtifactVersionCreate,
    ArtifactVersionResponse,
    ArtifactVisibilityUpdate,
    ViewLinkResponse,
)
from app.schemas.schemas import DeleteResponse

VIEW_LINK_LIFETIME_SECONDS = 300


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")


def _owned_artifacts(current_user: User) -> Select[tuple[Artifact, ArtifactVersion]]:
    """Select the user's artifacts joined to their current version."""
    return (
        select(Artifact, ArtifactVersion)
        .join(ArtifactVersion, ArtifactVersion.id == Artifact.current_version_id)
        .filter(Artifact.owner_id == current_user.id)
    )


async def _get_owned_artifact(
    db: AsyncSession, current_user: User, artifact_id: int
) -> tuple[Artifact, ArtifactVersion]:
    """Return one of the user's artifacts and its current version.

    Raises:
        HTTPException: 404 if the artifact does not exist or belongs to another user.
    """
    row = (await db.execute(_owned_artifacts(current_user).filter(Artifact.id == artifact_id))).one_or_none()
    if row is None:
        raise _not_found()
    artifact, version = row
    return artifact, version


def _to_response(artifact: Artifact, version: ArtifactVersion) -> ArtifactResponse:
    return ArtifactResponse.model_validate(
        {
            "id": artifact.id,
            "slug": artifact.slug,
            "title": artifact.title,
            "visibility": artifact.visibility,
            "created_at": artifact.created_at,
            "current_version": ArtifactVersionResponse.model_validate(version),
            "share_url": f"{ARTIFACT_CONTENT_ORIGIN}/a/{artifact.slug}",
        }
    )


async def _append_version(db: AsyncSession, artifact: Artifact, request: ArtifactVersionCreate) -> ArtifactResponse:
    """Add the next version to an artifact, make it current, and commit."""
    latest = await db.scalar(
        select(func.max(ArtifactVersion.version)).filter(ArtifactVersion.artifact_id == artifact.id)
    )
    version = ArtifactVersion(
        artifact_id=artifact.id,
        version=(latest or 0) + 1,
        content_type=request.content_type,
        content=request.content,
    )
    db.add(version)
    await db.flush()
    artifact.current_version_id = version.id
    await db.commit()
    return _to_response(artifact, version)


async def create_artifact(db: AsyncSession, current_user: User, request: ArtifactCreate) -> ArtifactResponse:
    """Publish a new private artifact whose version 1 is the request's content."""
    artifact = Artifact(owner_id=current_user.id, slug=secrets.token_urlsafe(16), title=request.title)
    db.add(artifact)
    await db.flush()
    return await _append_version(db, artifact, request)


async def publish_version(
    db: AsyncSession, current_user: User, artifact_id: int, request: ArtifactVersionCreate
) -> ArtifactResponse:
    """Publish the next version of one of the user's artifacts and make it current.

    The artifact row stays locked until commit, so concurrent publishes get consecutive numbers. The lock
    query reads the artifact alone: joined to its current version, a publisher that waited on the lock would
    re-check the join against the moved current_version_id and lose the row.

    Raises:
        HTTPException: 404 if the artifact does not exist or belongs to another user.
    """
    artifact = await db.scalar(
        select(Artifact).filter(Artifact.id == artifact_id, Artifact.owner_id == current_user.id).with_for_update()
    )
    if artifact is None:
        raise _not_found()
    return await _append_version(db, artifact, request)


async def get_artifact(db: AsyncSession, current_user: User, artifact_id: int) -> ArtifactResponse:
    """Return one of the user's artifacts with its current version.

    Raises:
        HTTPException: 404 if the artifact does not exist or belongs to another user.
    """
    return _to_response(*await _get_owned_artifact(db, current_user, artifact_id))


async def get_unlisted_version(db: AsyncSession, slug: str) -> ArtifactVersion | None:
    """Return the current version of the unlisted artifact with this slug, for readers without an account.

    Returns None when no artifact has this slug or the artifact is private; the caller cannot tell them apart.
    """
    return await db.scalar(
        select(ArtifactVersion)
        .join(Artifact, Artifact.current_version_id == ArtifactVersion.id)
        .filter(Artifact.slug == slug, Artifact.visibility == "unlisted")
    )


def sign_view_link(slug: str, version: int, expiry: int) -> str:
    """Return the lowercase hex HMAC-SHA256 of "slug:version:expiry" under ARTIFACT_SIGNING_KEY."""
    message = f"{slug}:{version}:{expiry}".encode()
    return hmac.new(ARTIFACT_SIGNING_KEY.encode(), message, hashlib.sha256).hexdigest()


def verify_view_link(slug: str, version: int, expiry: int, signature: str) -> bool:
    """Return whether signature is the view-link signature of slug:version:expiry, compared in constant time."""
    return hmac.compare_digest(sign_view_link(slug, version, expiry).encode(), signature.encode())


def _parse_count(value: str) -> int | None:
    """Parse a base-10 ASCII integer from a query parameter; anything else is None."""
    return int(value) if value.isascii() and value.isdigit() else None


async def mint_view_link(db: AsyncSession, current_user: User, artifact_id: int) -> ViewLinkResponse:
    """Return a signed link to the current version of one of the user's artifacts, valid for 300 seconds.

    Raises:
        HTTPException: 404 if the artifact does not exist or belongs to another user.
    """
    artifact, version = await _get_owned_artifact(db, current_user, artifact_id)
    expiry = int(time.time()) + VIEW_LINK_LIFETIME_SECONDS
    signature = sign_view_link(artifact.slug, version.version, expiry)
    return ViewLinkResponse(
        url=f"{ARTIFACT_CONTENT_ORIGIN}/a/{artifact.slug}?v={version.version}&e={expiry}&s={signature}",
        expires_at=datetime.fromtimestamp(expiry, tz=UTC),
    )


async def get_signed_version(
    db: AsyncSession, slug: str, v: str | None, e: str | None, s: str | None
) -> ArtifactVersion | None:
    """Return version v of the artifact with this slug when s signs slug:v:e and now <= e <= now + 300.

    Visibility does not matter. Returns None for a missing or malformed parameter, a bad signature, an expiry
    outside the window, an unknown slug, or a version the artifact does not have; the caller cannot tell them apart.
    """
    if v is None or e is None or s is None:
        return None
    version, expiry = _parse_count(v), _parse_count(e)
    if version is None or expiry is None or not verify_view_link(slug, version, expiry, s):
        return None
    now = int(time.time())
    if not now <= expiry <= now + VIEW_LINK_LIFETIME_SECONDS:
        return None
    return await db.scalar(
        select(ArtifactVersion)
        .join(Artifact, Artifact.id == ArtifactVersion.artifact_id)
        .filter(Artifact.slug == slug, ArtifactVersion.version == version)
    )


async def get_artifact_content(db: AsyncSession, current_user: User, artifact_id: int) -> ArtifactContentResponse:
    """Return the raw content of the current version of one of the user's artifacts.

    Raises:
        HTTPException: 404 if the artifact does not exist or belongs to another user.
    """
    _artifact, version = await _get_owned_artifact(db, current_user, artifact_id)
    return ArtifactContentResponse.model_validate(
        {"version": version.version, "content_type": version.content_type, "content": version.content}
    )


async def list_artifacts(db: AsyncSession, current_user: User) -> list[ArtifactResponse]:
    """Return the user's artifacts with their current versions, newest first."""
    result = await db.execute(_owned_artifacts(current_user).order_by(Artifact.id.desc()))
    return [_to_response(artifact, version) for artifact, version in result.all()]


async def set_visibility(
    db: AsyncSession, current_user: User, artifact_id: int, request: ArtifactVisibilityUpdate
) -> ArtifactResponse:
    """Make one of the user's artifacts private or unlisted.

    Raises:
        HTTPException: 404 if the artifact does not exist or belongs to another user.
    """
    artifact, version = await _get_owned_artifact(db, current_user, artifact_id)
    artifact.visibility = request.visibility
    await db.commit()
    return _to_response(artifact, version)


async def delete_artifact(db: AsyncSession, current_user: User, artifact_id: int) -> DeleteResponse:
    """Delete one of the user's artifacts; the database cascades the delete to its versions.

    Raises:
        HTTPException: 404 if the artifact does not exist or belongs to another user.
    """
    artifact, _current = await _get_owned_artifact(db, current_user, artifact_id)
    await db.delete(artifact)
    await db.commit()
    return DeleteResponse(message="Artifact deleted successfully", deleted_id=str(artifact_id))
