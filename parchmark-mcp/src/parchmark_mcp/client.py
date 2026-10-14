"""ParchMark API client authenticated with a personal API token."""

import httpx
from fastmcp.exceptions import ToolError

from parchmark_mcp.models import Note, NoteSummary


class ParchMarkClient:
    """Client for ParchMark REST API that sends a personal API token on every request."""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self._http = httpx.AsyncClient(timeout=30.0, headers={"Authorization": f"Bearer {token}"})

    async def _request(
        self,
        method: str,
        path: str,
        json_data: dict[str, str] | None = None,
    ) -> dict[str, str | int | list[dict[str, str]]] | list[dict[str, str]]:
        """Make authenticated request with error handling."""
        response = await self._http.request(
            method,
            f"{self.base_url}{path}",
            json=json_data,
        )

        if response.status_code == 401:
            raise ToolError("Authentication failed - check that PARCHMARK_TOKEN is valid and not revoked")
        if response.status_code == 404:
            raise ToolError("Note not found")
        if response.status_code >= 400:
            raise ToolError(f"API error: {response.status_code}")

        return response.json()

    async def list_notes(self) -> list[NoteSummary]:
        """Get all notes (without content in response model)."""
        data = await self._request("GET", "/notes/")
        if not isinstance(data, list):
            raise ToolError("Unexpected response format")
        return [NoteSummary.model_validate(note) for note in data]

    async def get_note(self, note_id: str) -> Note:
        """Get a specific note with content."""
        data = await self._request("GET", f"/notes/{note_id}")
        if isinstance(data, list):
            raise ToolError("Unexpected response format")
        return Note.model_validate(data)

    async def create_note(self, content: str) -> Note:
        """Create a new note. Title is omitted so the API extracts it from the first H1."""
        data = await self._request(
            "POST",
            "/notes/",
            json_data={"content": content},
        )
        if isinstance(data, list):
            raise ToolError("Unexpected response format")
        return Note.model_validate(data)

    async def update_note(self, note_id: str, content: str) -> Note:
        """Update a note's content."""
        data = await self._request(
            "PUT",
            f"/notes/{note_id}",
            json_data={"content": content},
        )
        if isinstance(data, list):
            raise ToolError("Unexpected response format")
        return Note.model_validate(data)

    async def delete_note(self, note_id: str) -> None:
        """Delete a note."""
        await self._request("DELETE", f"/notes/{note_id}")
