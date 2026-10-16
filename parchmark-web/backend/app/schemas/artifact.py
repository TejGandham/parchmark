"""Pydantic schemas for artifact requests and responses."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ArtifactContentType = Literal["html", "markdown", "svg"]
ArtifactVisibility = Literal["private", "unlisted"]


class ArtifactVersionCreate(BaseModel):
    """Request body for publishing a new version of an existing artifact. Content is stored as sent."""

    content_type: ArtifactContentType = Field(..., description="Kind of document: html, markdown or svg")
    content: str = Field(..., min_length=1, description="Raw document content")


class ArtifactCreate(ArtifactVersionCreate):
    """Request body for publishing a new artifact together with its first version."""

    title: str = Field(..., min_length=1, max_length=255, description="Display title of the artifact")


class ArtifactVisibilityUpdate(BaseModel):
    """Request body for changing who can read an artifact."""

    visibility: ArtifactVisibility = Field(..., description="private (owner only) or unlisted (anyone with the link)")


class ArtifactVersionResponse(BaseModel):
    """Metadata of one artifact version. The raw content is not echoed back."""

    id: int = Field(..., description="Version identifier")
    version: int = Field(..., description="Version number, starting at 1 and increasing per publish")
    content_type: ArtifactContentType = Field(..., description="Kind of document: html, markdown or svg")
    created_at: datetime = Field(..., description="When the version was published")

    model_config = ConfigDict(from_attributes=True)


class ArtifactResponse(BaseModel):
    """Artifact metadata with its current version."""

    id: int = Field(..., description="Artifact identifier")
    slug: str = Field(..., description="Stable, unguessable identifier used in the artifact's URL")
    title: str = Field(..., description="Display title of the artifact")
    visibility: ArtifactVisibility = Field(..., description="private (owner only) or unlisted (anyone with the link)")
    created_at: datetime = Field(..., description="When the artifact was first published")
    current_version: ArtifactVersionResponse = Field(..., description="The version currently served")
