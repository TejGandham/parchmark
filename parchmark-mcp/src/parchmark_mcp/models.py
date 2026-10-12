"""Pydantic models for ParchMark MCP server."""

from datetime import datetime

from pydantic import BaseModel, Field


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
