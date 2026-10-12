"""FastMCP server for ParchMark notes."""

import os

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from parchmark_mcp.client import ParchMarkClient
from parchmark_mcp.models import DeleteResponse, Note, NotesListResponse

mcp = FastMCP(
    "parchmark",
    instructions="Manage ParchMark notes - create, read, update, delete markdown notes",
)

_client: ParchMarkClient | None = None


def get_client() -> ParchMarkClient:
    """Get singleton client instance."""
    global _client
    if _client is None:
        base_url = os.environ.get("PARCHMARK_URL")
        username = os.environ.get("PARCHMARK_USERNAME")
        password = os.environ.get("PARCHMARK_PASSWORD")

        if base_url is None or username is None or password is None:
            raise ToolError("Missing environment variables: PARCHMARK_URL, PARCHMARK_USERNAME, PARCHMARK_PASSWORD")

        _client = ParchMarkClient(
            base_url=base_url,
            username=username,
            password=password,
        )
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


def main() -> None:
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
