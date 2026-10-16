"""
Artifact routes for ParchMark backend API.

``router`` (mounted under /api) lets the signed-in user publish artifacts and
new versions of them, list, read, delete them and set their visibility. Every
one of these routes is filtered by owner, so another user's artifact is a 404.

``content_router`` serves the public content path /a/<slug> without
authentication. It only finds unlisted artifacts; a private one is a 404.

The business logic lives in ``app.services.artifact_service``.
"""

from fastapi import APIRouter, Depends, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.database import get_async_db
from app.models.models import User
from app.schemas.artifact import ArtifactCreate, ArtifactResponse, ArtifactVersionCreate, ArtifactVisibilityUpdate
from app.schemas.schemas import DeleteResponse
from app.services import artifact_service

router = APIRouter(prefix="/artifacts", tags=["artifacts"])
content_router = APIRouter(prefix="/a", tags=["artifacts"])


@router.post("", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def publish_artifact(
    request: ArtifactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> ArtifactResponse:
    """Publish a new private artifact; the request's content becomes version 1."""
    return await artifact_service.create_artifact(db, current_user, request)


@router.get("", response_model=list[ArtifactResponse])
async def list_artifacts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> list[ArtifactResponse]:
    """List the current user's artifacts with their current versions, newest first."""
    return await artifact_service.list_artifacts(db, current_user)


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> ArtifactResponse:
    """Return one of the current user's artifacts with its current version (404 if it is not theirs)."""
    return await artifact_service.get_artifact(db, current_user, artifact_id)


@router.post("/{artifact_id}/versions", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def publish_version(
    artifact_id: int,
    request: ArtifactVersionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> ArtifactResponse:
    """Publish the next version of an artifact and make it current. Earlier versions are kept unchanged."""
    return await artifact_service.publish_version(db, current_user, artifact_id, request)


@router.post("/{artifact_id}/visibility", response_model=ArtifactResponse)
async def set_visibility(
    artifact_id: int,
    request: ArtifactVisibilityUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> ArtifactResponse:
    """Make an artifact private (owner only) or unlisted (anyone with its /a/<slug> link)."""
    return await artifact_service.set_visibility(db, current_user, artifact_id, request)


@router.delete("/{artifact_id}", response_model=DeleteResponse)
async def delete_artifact(
    artifact_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> DeleteResponse:
    """Delete an artifact together with all of its versions."""
    return await artifact_service.delete_artifact(db, current_user, artifact_id)


@content_router.get("/{slug}", response_class=PlainTextResponse)
async def read_unlisted_artifact(slug: str, db: AsyncSession = Depends(get_async_db)) -> PlainTextResponse:
    """
    Return the current version's raw content of an unlisted artifact. No authentication.

    The content is sent as plain text with nosniff, so a browser shows it and never
    renders it as a page on this origin.
    """
    version = await artifact_service.get_unlisted_version(db, slug)
    return PlainTextResponse(version.content, headers={"X-Content-Type-Options": "nosniff"})
