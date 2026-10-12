"""Tests for FastMCP server."""

import os
from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

import parchmark_mcp.server as server_module
from parchmark_mcp.models import DeleteResponse, Note, NotesListResponse, NoteSummary


@pytest.fixture
def mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set required environment variables."""
    monkeypatch.setenv("PARCHMARK_URL", "https://api.example.com")
    monkeypatch.setenv("PARCHMARK_USERNAME", "testuser")
    monkeypatch.setenv("PARCHMARK_PASSWORD", "testpass")


@pytest.fixture
def mock_client() -> Generator[AsyncMock, None, None]:
    """Create mock ParchMarkClient."""
    with (
        patch.object(server_module, "_client", None),
        patch.object(server_module, "ParchMarkClient") as mock,
    ):
        client_instance = AsyncMock()
        mock.return_value = client_instance
        yield client_instance


def test_get_client_creates_singleton(mock_env: None) -> None:
    """get_client creates client with env vars and reuses it."""
    # Reset singleton
    server_module._client = None  # pyright: ignore[reportPrivateUsage]

    with patch.object(server_module, "ParchMarkClient") as mock:
        # Call twice to verify singleton behavior
        server_module.get_client()
        server_module.get_client()

        # Should only create once
        assert mock.call_count == 1
        mock.assert_called_with(
            base_url="https://api.example.com",
            username="testuser",
            password="testpass",
        )


def test_get_client_missing_env_raises() -> None:
    """get_client raises error if env vars missing."""
    from fastmcp.exceptions import ToolError

    # Reset singleton and clear env
    server_module._client = None  # pyright: ignore[reportPrivateUsage]

    with (
        patch.dict(os.environ, {}, clear=True),
        pytest.raises(ToolError, match="Missing environment variables"),
    ):
        server_module.get_client()


@pytest.mark.asyncio
async def test_list_notes_tool(mock_env: None, mock_client: AsyncMock) -> None:
    """list_notes tool returns NotesListResponse."""
    from parchmark_mcp.server import list_notes

    mock_client.list_notes.return_value = [
        NoteSummary(
            id="note-1",
            title="Test",
            createdAt=datetime.now(UTC),
            updatedAt=datetime.now(UTC),
        )
    ]

    # Access the underlying function via .fn attribute
    tool = list_notes
    assert hasattr(tool, "fn")
    result = await tool.fn()  # type: ignore[union-attr]

    assert isinstance(result, NotesListResponse)
    assert result.count == 1
    assert result.notes[0].id == "note-1"


@pytest.mark.asyncio
async def test_get_note_tool(mock_env: None, mock_client: AsyncMock) -> None:
    """get_note tool returns Note."""
    from parchmark_mcp.server import get_note

    mock_client.get_note.return_value = Note(
        id="note-123",
        title="Test",
        content="# Test",
        createdAt=datetime.now(UTC),
        updatedAt=datetime.now(UTC),
    )

    # Access the underlying function via .fn attribute
    tool = get_note
    assert hasattr(tool, "fn")
    result = await tool.fn("note-123")  # type: ignore[union-attr]

    assert isinstance(result, Note)
    assert result.id == "note-123"
    mock_client.get_note.assert_called_with("note-123")


@pytest.mark.asyncio
async def test_create_note_tool(mock_env: None, mock_client: AsyncMock) -> None:
    """create_note tool returns created Note."""
    from parchmark_mcp.server import create_note

    mock_client.create_note.return_value = Note(
        id="note-new",
        title="New Note",
        content="# New Note",
        createdAt=datetime.now(UTC),
        updatedAt=datetime.now(UTC),
    )

    # Access the underlying function via .fn attribute
    tool = create_note
    assert hasattr(tool, "fn")
    result = await tool.fn("# New Note")  # type: ignore[union-attr]

    assert isinstance(result, Note)
    assert result.id == "note-new"
    mock_client.create_note.assert_called_with("# New Note")


@pytest.mark.asyncio
async def test_update_note_tool(mock_env: None, mock_client: AsyncMock) -> None:
    """update_note tool returns updated Note."""
    from parchmark_mcp.server import update_note

    mock_client.update_note.return_value = Note(
        id="note-123",
        title="Updated Note",
        content="# Updated Note",
        createdAt=datetime.now(UTC),
        updatedAt=datetime.now(UTC),
    )

    # Access the underlying function via .fn attribute
    tool = update_note
    assert hasattr(tool, "fn")
    result = await tool.fn("note-123", "# Updated Note")  # type: ignore[union-attr]

    assert isinstance(result, Note)
    assert result.id == "note-123"
    mock_client.update_note.assert_called_with("note-123", "# Updated Note")


@pytest.mark.asyncio
async def test_delete_note_tool(mock_env: None, mock_client: AsyncMock) -> None:
    """delete_note tool returns DeleteResponse."""
    from parchmark_mcp.server import delete_note

    mock_client.delete_note.return_value = None

    # Access the underlying function via .fn attribute
    tool = delete_note
    assert hasattr(tool, "fn")
    result = await tool.fn("note-123")  # type: ignore[union-attr]

    assert isinstance(result, DeleteResponse)
    assert result.success is True
    assert "note-123" in result.message
    mock_client.delete_note.assert_called_with("note-123")
