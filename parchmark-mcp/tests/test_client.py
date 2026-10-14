"""Tests for ParchMark API client."""

import json

import pytest
import respx
from httpx import Response

from parchmark_mcp.client import ParchMarkClient

TOKEN = "pmat_test-token"


@pytest.fixture
def client() -> ParchMarkClient:
    """Create test client."""
    return ParchMarkClient(base_url="https://api.example.com", token=TOKEN)


@pytest.mark.asyncio
async def test_sends_token_and_never_logs_in(client: ParchMarkClient, respx_mock: respx.MockRouter) -> None:
    """Every request carries the token as a bearer header and no auth endpoint is called."""
    list_route = respx_mock.get("https://api.example.com/notes/").mock(return_value=Response(200, json=[]))
    delete_route = respx_mock.delete("https://api.example.com/notes/note-123").mock(
        return_value=Response(200, json={"message": "Note deleted"})
    )

    await client.list_notes()
    await client.delete_note("note-123")

    # Only the two note requests went out: no login or refresh round-trip.
    assert respx_mock.calls.call_count == 2
    for route in (list_route, delete_route):
        assert route.calls.last.request.headers["Authorization"] == f"Bearer {TOKEN}"


@pytest.mark.asyncio
async def test_rejected_token_raises(client: ParchMarkClient, respx_mock: respx.MockRouter) -> None:
    """A 401 for an invalid or revoked token surfaces as a tool error."""
    from fastmcp.exceptions import ToolError

    respx_mock.get("https://api.example.com/notes/").mock(return_value=Response(401, json={"detail": "Unauthorized"}))
    with pytest.raises(ToolError, match="PARCHMARK_TOKEN"):
        await client.list_notes()


@pytest.mark.asyncio
async def test_list_notes(
    client: ParchMarkClient,
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
    respx_mock: respx.MockRouter,
) -> None:
    """Client deletes note successfully."""
    respx_mock.delete("https://api.example.com/notes/note-123").mock(
        return_value=Response(200, json={"message": "Note deleted"})
    )
    await client.delete_note("note-123")  # Should not raise
