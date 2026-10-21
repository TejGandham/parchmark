"""ParchMark API client authenticated with a personal API token."""

import httpx
from fastmcp.exceptions import ToolError

from parchmark_mcp.models import (
    Artifact,
    ArtifactContentType,
    ArtifactRecord,
    ArtifactVisibility,
    Note,
    NoteSummary,
)


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
        not_found: str = "Note not found",
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
            raise ToolError(not_found)
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

    async def _artifact_request(self, method: str, path: str, json_data: dict[str, str] | None = None) -> Artifact:
        """Call an artifact endpoint that returns one artifact."""
        data = await self._request(method, path, json_data=json_data, not_found="Artifact not found")
        if isinstance(data, list):
            raise ToolError("Unexpected response format")
        return self._to_artifact(ArtifactRecord.model_validate(data))

    @staticmethod
    def _to_artifact(record: ArtifactRecord) -> Artifact:
        """Flatten the API record; url is the API's share_url, never built here."""
        return Artifact(
            id=record.id,
            title=record.title,
            version=record.current_version.version,
            content_type=record.current_version.content_type,
            visibility=record.visibility,
            url=record.share_url,
        )

    async def publish_artifact(self, title: str, content: str, content_type: ArtifactContentType) -> Artifact:
        """Publish a new artifact; the content becomes version 1."""
        return await self._artifact_request(
            "POST",
            "/artifacts",
            json_data={"title": title, "content": content, "content_type": content_type},
        )

    async def update_artifact(self, artifact_id: int, content: str, content_type: ArtifactContentType) -> Artifact:
        """Publish the next version of an artifact and make it current."""
        return await self._artifact_request(
            "POST",
            f"/artifacts/{artifact_id}/versions",
            json_data={"content": content, "content_type": content_type},
        )

    async def list_artifacts(self) -> list[Artifact]:
        """List the user's artifacts, newest first."""
        data = await self._request("GET", "/artifacts")
        if not isinstance(data, list):
            raise ToolError("Unexpected response format")
        return [self._to_artifact(ArtifactRecord.model_validate(item)) for item in data]

    async def get_artifact(self, artifact_id: int) -> Artifact:
        """Get one of the user's artifacts with its current version."""
        return await self._artifact_request("GET", f"/artifacts/{artifact_id}")

    async def set_artifact_visibility(self, artifact_id: int, visibility: ArtifactVisibility) -> Artifact:
        """Make an artifact private or unlisted."""
        return await self._artifact_request(
            "POST",
            f"/artifacts/{artifact_id}/visibility",
            json_data={"visibility": visibility},
        )
