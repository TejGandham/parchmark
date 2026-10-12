"""ParchMark API client with JWT authentication."""

from datetime import UTC, datetime, timedelta

import httpx
from fastmcp.exceptions import ToolError

from parchmark_mcp.models import Note, NoteSummary


class ParchMarkClient:
    """Client for ParchMark REST API with automatic token management."""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.token_expiry: datetime | None = None
        self._http = httpx.AsyncClient(timeout=30.0)

    async def _login(self) -> None:
        """Authenticate and store tokens."""
        response = await self._http.post(
            f"{self.base_url}/auth/login",
            json={"username": self.username, "password": self.password},
        )
        if response.status_code != 200:
            raise ToolError("Authentication failed - check credentials")

        tokens = response.json()
        self.access_token = tokens["access_token"]
        self.refresh_token = tokens["refresh_token"]
        self.token_expiry = datetime.now(UTC) + timedelta(minutes=25)

    async def _refresh(self) -> None:
        """Refresh access token using refresh token."""
        response = await self._http.post(
            f"{self.base_url}/auth/refresh",
            json={"refresh_token": self.refresh_token},
        )
        if response.status_code != 200:
            await self._login()
            return

        tokens = response.json()
        self.access_token = tokens["access_token"]
        self.token_expiry = datetime.now(UTC) + timedelta(minutes=25)

    async def _ensure_authenticated(self) -> None:
        """Login or refresh token as needed."""
        if self.access_token is None:
            await self._login()
        elif self.token_expiry and datetime.now(UTC) >= self.token_expiry:
            await self._refresh()

    async def _request(
        self,
        method: str,
        path: str,
        json_data: dict[str, str] | None = None,
    ) -> dict[str, str | int | list[dict[str, str]]] | list[dict[str, str]]:
        """Make authenticated request with error handling."""
        await self._ensure_authenticated()

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = await self._http.request(
            method,
            f"{self.base_url}{path}",
            headers=headers,
            json=json_data,
        )

        if response.status_code == 401:
            raise ToolError("Authentication failed - session expired")
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
