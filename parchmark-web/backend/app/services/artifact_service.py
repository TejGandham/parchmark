"""Artifact business logic: publish artifacts and their versions, read and manage them.

Ownership rule: every lookup is filtered by the caller's user id, so another
user's artifact behaves exactly like one that does not exist (404). Versions
are append-only; publishing adds the next version number and moves the
artifact's current_version_id to it. Slugs carry 128 bits of randomness and
never change once issued.
"""

import secrets

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import Artifact
from app.models.artifact_version import ArtifactVersion
from app.models.models import User
from app.schemas.artifact import (
    ArtifactCreate,
    ArtifactResponse,
    ArtifactVersionCreate,
    ArtifactVersionResponse,
    ArtifactVisibilityUpdate,
)
from app.schemas.schemas import DeleteResponse


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
