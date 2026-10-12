"""Tests for ParchMark API client."""

import json

import pytest
import respx
from httpx import Response

from parchmark_mcp.client import ParchMarkClient


@pytest.fixture
def client() -> ParchMarkClient:
    """Create test client."""
    return ParchMarkClient(
        base_url="https://api.example.com",
        username="testuser",
        password="testpass",
    )


@pytest.fixture
def mock_login(respx_mock: respx.MockRouter) -> respx.Route:
    """Mock successful login."""
    return respx_mock.post("https://api.example.com/auth/login").mock(
        return_value=Response(
            200,
            json={
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "token_type": "bearer",
            },
        )
    )


@pytest.mark.asyncio
async def test_login_success(client: ParchMarkClient, mock_login: respx.Route) -> None:
    """Client stores tokens after successful login."""
    await client._login()  # pyright: ignore[reportPrivateUsage]
    assert client.access_token == "test-access-token"
    assert client.refresh_token == "test-refresh-token"
    assert mock_login.called


@pytest.mark.asyncio
async def test_login_failure(client: ParchMarkClient, respx_mock: respx.MockRouter) -> None:
    """Client raises error on login failure."""
    from fastmcp.exceptions import ToolError

    respx_mock.post("https://api.example.com/auth/login").mock(
        return_value=Response(401, json={"detail": "Invalid credentials"})
    )
    with pytest.raises(ToolError, match="Authentication failed"):
        await client._login()  # pyright: ignore[reportPrivateUsage]


@pytest.mark.asyncio
async def test_list_notes(
    client: ParchMarkClient,
    mock_login: respx.Route,
    respx_mock: respx.MockRouter,
) -> None:
    """Client lists notes successfully."""
    respx_mock.get("https://api.example.com/notes/").mock(
        return_value=Response(
            200,
            json=[
                {
                    "id": "note-1",
                    "title": "Note 1",
                    "content": "# Note 1",
                    "createdAt": "2026-01-28T10:00:00",
                    "updatedAt": "2026-01-28T10:00:00",
                }
            ],
        )
    )
    notes = await client.list_notes()
    assert len(notes) == 1
    assert notes[0].id == "note-1"


@pytest.mark.asyncio
async def test_get_note(
    client: ParchMarkClient,
    mock_login: respx.Route,
    respx_mock: respx.MockRouter,
) -> None:
    """Client gets single note with content."""
    respx_mock.get("https://api.example.com/notes/note-123").mock(
        return_value=Response(
            200,
            json={
                "id": "note-123",
                "title": "Test Note",
                "content": "# Test Note\n\nBody",
                "createdAt": "2026-01-28T10:00:00",
                "updatedAt": "2026-01-28T10:00:00",
            },
        )
    )
    note = await client.get_note("note-123")
    assert note.id == "note-123"
    assert note.content == "# Test Note\n\nBody"


@pytest.mark.asyncio
async def test_create_note(
    client: ParchMarkClient,
    mock_login: respx.Route,
    respx_mock: respx.MockRouter,
) -> None:
    """Client creates note without a title so the API extracts it from the H1."""
    create_route = respx_mock.post("https://api.example.com/notes/").mock(
        return_value=Response(
            200,
            json={
                "id": "note-new",
                "title": "New Note",
                "content": "# New Note\n\nContent",
                "createdAt": "2026-01-28T10:00:00",
                "updatedAt": "2026-01-28T10:00:00",
            },
        )
    )
    note = await client.create_note("# New Note\n\nContent")
    assert note.id == "note-new"
    assert note.title == "New Note"

    sent_body = json.loads(create_route.calls.last.request.content)
    assert sent_body == {"content": "# New Note\n\nContent"}


@pytest.mark.asyncio
async def test_delete_note(
    client: ParchMarkClient,
    mock_login: respx.Route,
    respx_mock: respx.MockRouter,
) -> None:
    """Client deletes note successfully."""
    respx_mock.delete("https://api.example.com/notes/note-123").mock(
        return_value=Response(200, json={"message": "Note deleted"})
    )
    await client.delete_note("note-123")  # Should not raise
