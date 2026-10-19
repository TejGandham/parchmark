"""Tests for FastMCP server."""

import os
from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
import respx
from httpx import Response

import parchmark_mcp.server as server_module
from parchmark_mcp.models import (
    Artifact,
    ArtifactsListResponse,
    DeleteResponse,
    Note,
    NotesListResponse,
    NoteSummary,
)

ARTIFACT = Artifact(
    id=7,
    title="Report",
    version=2,
    content_type="html",
    visibility="unlisted",
    url="https://artifacts.example.net/a/s3cr3t-slug",
)


@pytest.fixture
def mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set required environment variables."""
    monkeypatch.setenv("PARCHMARK_URL", "https://api.example.com")
    monkeypatch.setenv("PARCHMARK_TOKEN", "pmat_test-token")


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
        mock.assert_called_with(base_url="https://api.example.com", token="pmat_test-token")


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


@pytest.mark.parametrize("token", [None, ""])
def test_get_client_missing_token_raises(token: str | None) -> None:
    """get_client raises when PARCHMARK_TOKEN is unset or empty, even with the old username/password set."""
    from fastmcp.exceptions import ToolError

    server_module._client = None  # pyright: ignore[reportPrivateUsage]
    env = {
        "PARCHMARK_URL": "https://api.example.com",
        "PARCHMARK_USERNAME": "testuser",
        "PARCHMARK_PASSWORD": "testpass",
    }
    if token is not None:
        env["PARCHMARK_TOKEN"] = token

    with (
        patch.dict(os.environ, env, clear=True),
        patch.object(server_module, "ParchMarkClient") as mock,
        pytest.raises(ToolError, match="PARCHMARK_TOKEN"),
    ):
        server_module.get_client()
    mock.assert_not_called()


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


@pytest.mark.asyncio
async def test_artifact_tools_return_share_url(mock_env: None, mock_client: AsyncMock) -> None:
    """Every artifact tool returns what the client gives back, url included."""
    from parchmark_mcp.server import (
        get_artifact,
        list_artifacts,
        publish_artifact,
        set_artifact_visibility,
        update_artifact,
    )

    mock_client.publish_artifact.return_value = ARTIFACT
    mock_client.update_artifact.return_value = ARTIFACT
    mock_client.get_artifact.return_value = ARTIFACT
    mock_client.set_artifact_visibility.return_value = ARTIFACT
    mock_client.list_artifacts.return_value = [ARTIFACT]

    results = [
        await publish_artifact.fn("Report", "<h1>Hi</h1>", "html"),
        await update_artifact.fn(7, "<h1>Hi</h1>", "html"),
        await get_artifact.fn(7),
        await set_artifact_visibility.fn(7, "unlisted"),
    ]
    listed = await list_artifacts.fn()

    assert isinstance(listed, ArtifactsListResponse)
    assert listed.count == 1
    for artifact in [*results, *listed.artifacts]:
        assert (artifact.id, artifact.title, artifact.version) == (7, "Report", 2)
        assert artifact.url == ARTIFACT.url
    mock_client.publish_artifact.assert_called_with("Report", "<h1>Hi</h1>", "html")
    mock_client.update_artifact.assert_called_with(7, "<h1>Hi</h1>", "html")
    mock_client.get_artifact.assert_called_with(7)
    mock_client.set_artifact_visibility.assert_called_with(7, "unlisted")


@pytest.mark.asyncio
@pytest.mark.parametrize("visibility", ["private", "unlisted"])
async def test_set_artifact_visibility_accepts_private_and_unlisted(
    mock_env: None, mock_client: AsyncMock, visibility: str
) -> None:
    """Through the MCP protocol, private and unlisted reach the API client."""
    from fastmcp import Client

    mock_client.set_artifact_visibility.return_value = ARTIFACT
    async with Client(server_module.mcp) as mcp_client:
        result = await mcp_client.call_tool("set_artifact_visibility", {"artifact_id": 7, "visibility": visibility})

    assert result.structured_content is not None
    assert result.structured_content["url"] == ARTIFACT.url
    mock_client.set_artifact_visibility.assert_called_with(7, visibility)


@pytest.mark.asyncio
@pytest.mark.parametrize("visibility", ["public", "PRIVATE", ""])
async def test_set_artifact_visibility_rejects_other_values(
    mock_env: None, mock_client: AsyncMock, visibility: str
) -> None:
    """Through the MCP protocol, any visibility other than private or unlisted is refused before the API call."""
    from fastmcp import Client
    from fastmcp.exceptions import ToolError

    async with Client(server_module.mcp) as mcp_client:
        with pytest.raises(ToolError, match="Input should be 'private' or 'unlisted'"):
            await mcp_client.call_tool("set_artifact_visibility", {"artifact_id": 7, "visibility": visibility})

    mock_client.set_artifact_visibility.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("visibility", ["private", "unlisted"])
async def test_artifact_tools_relay_api_share_url(
    monkeypatch: pytest.MonkeyPatch, respx_mock: respx.MockRouter, visibility: str
) -> None:
    """Through the MCP protocol and the real client, every tool's url is the API's share_url byte for byte.

    The share_url is on a different host from PARCHMARK_URL, so a url computed from PARCHMARK_URL fails.
    """
    from fastmcp import Client

    monkeypatch.setenv("PARCHMARK_URL", "https://notes.example.com/api")
    monkeypatch.setenv("PARCHMARK_TOKEN", "pmat_test-token")
    monkeypatch.setattr(server_module, "_client", None)
    share_url = "https://artifacts.example.net/a/s3cr3t-slug"
    record = {
        "id": 7,
        "slug": "s3cr3t-slug",
        "share_url": share_url,
        "title": "Report",
        "visibility": visibility,
        "created_at": "2026-01-28T10:00:00",
        "current_version": {"id": 71, "version": 1, "content_type": "html", "created_at": "2026-01-28T10:00:00"},
    }
    api = "https://notes.example.com/api"
    respx_mock.post(f"{api}/artifacts").mock(return_value=Response(201, json=record))
    respx_mock.post(f"{api}/artifacts/7/versions").mock(return_value=Response(201, json=record))
    respx_mock.get(f"{api}/artifacts").mock(return_value=Response(200, json=[record]))
    respx_mock.get(f"{api}/artifacts/7").mock(return_value=Response(200, json=record))
    respx_mock.post(f"{api}/artifacts/7/visibility").mock(return_value=Response(200, json=record))

    calls: list[tuple[str, dict[str, object]]] = [
        ("publish_artifact", {"title": "Report", "content": "<h1>Hi</h1>", "content_type": "html"}),
        ("update_artifact", {"artifact_id": 7, "content": "<h1>Hi</h1>", "content_type": "html"}),
        ("get_artifact", {"artifact_id": 7}),
        ("set_artifact_visibility", {"artifact_id": 7, "visibility": visibility}),
    ]
    async with Client(server_module.mcp) as mcp_client:
        results = [(await mcp_client.call_tool(name, args)).structured_content for name, args in calls]
        listed = (await mcp_client.call_tool("list_artifacts", {})).structured_content

    assert listed is not None
    assert listed["count"] == 1
    for result in [*results, *listed["artifacts"]]:
        assert result is not None
        assert result["url"] == share_url
        assert result["visibility"] == visibility
