"""Pydantic models for ParchMark MCP server."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ArtifactContentType = Literal["html", "markdown", "svg"]
ArtifactVisibility = Literal["private", "unlisted"]


class NoteSummary(BaseModel):
    """Note metadata without content."""

    id: str
    title: str
    createdAt: datetime = Field(alias="createdAt")
    updatedAt: datetime = Field(alias="updatedAt")

    model_config = {"populate_by_name": True}


class Note(NoteSummary):
    """Full note including content."""

    content: str


class NotesListResponse(BaseModel):
    """Response for list_notes tool."""

    notes: list[NoteSummary]
    count: int


class DeleteResponse(BaseModel):
    """Response for delete_note tool."""

    success: bool
    message: str


class ArtifactVersionRecord(BaseModel):
    """Current version of an artifact as the API returns it."""

    version: int
    content_type: ArtifactContentType


class ArtifactRecord(BaseModel):
    """Artifact as the API returns it."""

    id: int
    slug: str
    share_url: str
    title: str
    visibility: ArtifactVisibility
    current_version: ArtifactVersionRecord


class Artifact(BaseModel):
    """Artifact returned by the artifact tools; url is the share link the API returned."""

    id: int
    title: str
    version: int
    content_type: ArtifactContentType
    visibility: ArtifactVisibility
    url: str


class ArtifactsListResponse(BaseModel):
    """Response for list_artifacts tool."""

    artifacts: list[Artifact]
    count: int
