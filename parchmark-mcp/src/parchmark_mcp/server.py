"""FastMCP server for ParchMark notes and artifacts."""

import os

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from parchmark_mcp.client import ParchMarkClient
from parchmark_mcp.models import (
    Artifact,
    ArtifactContentType,
    ArtifactsListResponse,
    ArtifactVisibility,
    DeleteResponse,
    Note,
    NotesListResponse,
)

mcp = FastMCP(
    "parchmark",
    instructions=(
        "Manage ParchMark notes - create, read, update, delete markdown notes. "
        "Publish HTML, Markdown or SVG artifacts. Each artifact tool returns url, the share link the API gives "
        "back (<content origin>/a/<slug>); it opens for others only after set_artifact_visibility makes the "
        "artifact unlisted."
    ),
)

_client: ParchMarkClient | None = None


def get_client() -> ParchMarkClient:
    """Get singleton client instance."""
    global _client
    if _client is None:
        base_url = os.environ.get("PARCHMARK_URL")
        token = os.environ.get("PARCHMARK_TOKEN")

        if not base_url or not token:
            raise ToolError("Missing environment variables: PARCHMARK_URL, PARCHMARK_TOKEN")

        _client = ParchMarkClient(base_url=base_url, token=token)
    return _client


@mcp.tool()
async def list_notes() -> NotesListResponse:
    """List all notes for the authenticated user.

    Returns note metadata (id, title, timestamps) without content.
    Use get_note to retrieve full content for a specific note.
    """
    client = get_client()
    notes = await client.list_notes()
    return NotesListResponse(notes=notes, count=len(notes))


@mcp.tool()
async def get_note(note_id: str) -> Note:
    """Get a specific note by ID with full content.

    Args:
        note_id: The unique identifier of the note (e.g., "note-1234567890")
    """
    client = get_client()
    return await client.get_note(note_id)


@mcp.tool()
async def create_note(content: str) -> Note:
    """Create a new note with markdown content.

    The note title is automatically extracted from the first H1 heading.

    Args:
        content: Markdown content for the note (should start with # Title)
    """
    client = get_client()
    return await client.create_note(content)


@mcp.tool()
async def update_note(note_id: str, content: str) -> Note:
    """Update an existing note's content.

    The note title is automatically re-extracted from the first H1 heading.

    Args:
        note_id: The unique identifier of the note to update
        content: New markdown content for the note
    """
    client = get_client()
    return await client.update_note(note_id, content)


@mcp.tool()
async def delete_note(note_id: str) -> DeleteResponse:
    """Delete a note by ID.

    Args:
        note_id: The unique identifier of the note to delete
    """
    client = get_client()
    await client.delete_note(note_id)
    return DeleteResponse(success=True, message=f"Note {note_id} deleted")


@mcp.tool()
async def publish_artifact(title: str, content: str, content_type: ArtifactContentType) -> Artifact:
    """Publish a self-contained HTML, Markdown or SVG document as a new artifact.

    The artifact starts private (only its owner can see it) at version 1.
    Its url opens for others only after set_artifact_visibility makes it unlisted.

    Args:
        title: Display title of the artifact
        content: Raw document content
        content_type: Kind of document: html, markdown or svg

    Returns the artifact id, title, version, content_type, visibility and url, the share link
    the API returns (<content origin>/a/<slug>).
    """
    client = get_client()
    return await client.publish_artifact(title, content, content_type)


@mcp.tool()
async def update_artifact(artifact_id: int, content: str, content_type: ArtifactContentType) -> Artifact:
    """Publish a new version of an existing artifact and make it the current one.

    Earlier versions are kept unchanged; the url stays the same.

    Args:
        artifact_id: The identifier of the artifact to update
        content: Raw document content of the new version
        content_type: Kind of document: html, markdown or svg

    Returns the artifact id, title, new version, content_type, visibility and url, the share
    link the API returns (<content origin>/a/<slug>).
    """
    client = get_client()
    return await client.update_artifact(artifact_id, content, content_type)


@mcp.tool()
async def list_artifacts() -> ArtifactsListResponse:
    """List all artifacts of the authenticated user, newest first.

    Each entry has the artifact id, title, current version, content_type, visibility and url,
    the share link the API returns (<content origin>/a/<slug>).
    """
    client = get_client()
    artifacts = await client.list_artifacts()
    return ArtifactsListResponse(artifacts=artifacts, count=len(artifacts))


@mcp.tool()
async def get_artifact(artifact_id: int) -> Artifact:
    """Get one artifact by ID.

    Args:
        artifact_id: The identifier of the artifact

    Returns the artifact id, title, current version, content_type, visibility and url, the
    share link the API returns (<content origin>/a/<slug>).
    """
    client = get_client()
    return await client.get_artifact(artifact_id)


@mcp.tool()
async def set_artifact_visibility(artifact_id: int, visibility: ArtifactVisibility) -> Artifact:
    """Set who can open an artifact.

    Args:
        artifact_id: The identifier of the artifact
        visibility: "private" (only the owner) or "unlisted" (anyone with the url); nothing else
            is accepted

    Returns the artifact id, title, current version, content_type, visibility and url, the
    share link the API returns (<content origin>/a/<slug>).
    """
    client = get_client()
    return await client.set_artifact_visibility(artifact_id, visibility)


def main() -> None:
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
