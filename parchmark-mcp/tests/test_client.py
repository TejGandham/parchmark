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


# The API builds share_url on its content origin, a different host from PARCHMARK_URL.
SHARE_URL = "https://artifacts.example.net/a/s3cr3t-slug"


def artifact_json(version: int = 1, visibility: str = "private") -> dict[str, object]:
    """An artifact as the API returns it."""
    return {
        "id": 7,
        "slug": "s3cr3t-slug",
        "share_url": SHARE_URL,
        "title": "Report",
        "visibility": visibility,
        "created_at": "2026-01-28T10:00:00",
        "current_version": {
            "id": 70 + version,
            "version": version,
            "content_type": "html",
            "created_at": "2026-01-28T10:00:00",
        },
    }


@pytest.fixture
def api_client() -> ParchMarkClient:
    """Client configured like production, with the API under /api."""
    return ParchMarkClient(base_url="https://notes.example.com/api/", token=TOKEN)


@pytest.mark.asyncio
async def test_publish_artifact(api_client: ParchMarkClient, respx_mock: respx.MockRouter) -> None:
    """Publishing posts title, content and type and relays the API's share_url as url."""
    route = respx_mock.post("https://notes.example.com/api/artifacts").mock(
        return_value=Response(201, json=artifact_json())
    )

    artifact = await api_client.publish_artifact("Report", "<h1>Hi</h1>", "html")

    assert json.loads(route.calls.last.request.content) == {
        "title": "Report",
        "content": "<h1>Hi</h1>",
        "content_type": "html",
    }
    assert artifact.id == 7
    assert artifact.title == "Report"
    assert artifact.version == 1
    assert artifact.url == SHARE_URL


@pytest.mark.asyncio
async def test_update_artifact(api_client: ParchMarkClient, respx_mock: respx.MockRouter) -> None:
    """Updating posts a new version and returns its number."""
    route = respx_mock.post("https://notes.example.com/api/artifacts/7/versions").mock(
        return_value=Response(201, json=artifact_json(version=2))
    )

    artifact = await api_client.update_artifact(7, "<h1>Hi again</h1>", "html")

    assert json.loads(route.calls.last.request.content) == {"content": "<h1>Hi again</h1>", "content_type": "html"}
    assert artifact.version == 2
    assert artifact.url == SHARE_URL


@pytest.mark.asyncio
async def test_list_and_get_artifacts(api_client: ParchMarkClient, respx_mock: respx.MockRouter) -> None:
    """Listing and getting relay each artifact's share_url as url."""
    respx_mock.get("https://notes.example.com/api/artifacts").mock(return_value=Response(200, json=[artifact_json()]))
    respx_mock.get("https://notes.example.com/api/artifacts/7").mock(return_value=Response(200, json=artifact_json()))

    listed = await api_client.list_artifacts()
    fetched = await api_client.get_artifact(7)

    assert [a.url for a in listed] == [SHARE_URL]
    assert fetched.url == SHARE_URL


@pytest.mark.asyncio
async def test_set_artifact_visibility(api_client: ParchMarkClient, respx_mock: respx.MockRouter) -> None:
    """Setting visibility posts the value and returns the updated artifact."""
    route = respx_mock.post("https://notes.example.com/api/artifacts/7/visibility").mock(
        return_value=Response(200, json=artifact_json(visibility="unlisted"))
    )

    artifact = await api_client.set_artifact_visibility(7, "unlisted")

    assert json.loads(route.calls.last.request.content) == {"visibility": "unlisted"}
    assert artifact.visibility == "unlisted"
    assert artifact.url == SHARE_URL


@pytest.mark.asyncio
async def test_private_artifact_still_carries_share_url(
    api_client: ParchMarkClient, respx_mock: respx.MockRouter
) -> None:
    """A private artifact keeps its url alongside visibility private."""
    respx_mock.get("https://notes.example.com/api/artifacts/7").mock(
        return_value=Response(200, json=artifact_json(visibility="private"))
    )

    artifact = await api_client.get_artifact(7)

    assert artifact.visibility == "private"
    assert artifact.url == SHARE_URL


@pytest.mark.asyncio
async def test_missing_artifact_raises(api_client: ParchMarkClient, respx_mock: respx.MockRouter) -> None:
    """A 404 from an artifact endpoint names the artifact, not a note."""
    from fastmcp.exceptions import ToolError

    respx_mock.get("https://notes.example.com/api/artifacts/9").mock(return_value=Response(404))
    with pytest.raises(ToolError, match="Artifact not found"):
        await api_client.get_artifact(9)
