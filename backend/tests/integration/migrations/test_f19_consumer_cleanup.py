"""
Integration tests for F19 consumer-path cleanup.

Oracle: /features/7/oracle
Assertions covered:
  /features/7/oracle/assertions/6 — grep routers/notes.py for access_count,
      last_accessed_at, defer(Note.embedding) returns zero matches
  /features/7/oracle/assertions/7 — grep schemas/schemas.py for accessCount,
      lastAccessedAt returns zero matches
  /features/7/oracle/assertions/8 — CRUD endpoints return non-error status
      and serialized note payloads contain no accessCount / lastAccessedAt fields
"""

import subprocess
from pathlib import Path

from fastapi import status
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_BACKEND_ROOT = Path(__file__).parents[3]
_ROUTERS_NOTES_PY = _BACKEND_ROOT / "app" / "routers" / "notes.py"
_SCHEMAS_PY = _BACKEND_ROOT / "app" / "schemas" / "schemas.py"


# ---------------------------------------------------------------------------
# /features/7/oracle/assertions/6
# ---------------------------------------------------------------------------


class TestRoutersNotesPyNoDroppedFieldReferences:
    """
    Static check: routers/notes.py has no references to the dropped fields.
    Contract: /features/7/contract/routers_notes_py/_note_to_response_fields_removed
              and list_query_defer_embedding_removed == true
    """

    def test_routers_notes_has_no_access_count_field(self):
        """
        Oracle: /features/7/oracle/assertions/6 (access_count reference)
        rg for 'access_count' in routers/notes.py must return exit 1.
        """
        assert _ROUTERS_NOTES_PY.exists(), f"notes.py not found at {_ROUTERS_NOTES_PY}"

        result = subprocess.run(
            ["rg", "-n", "access_count", str(_ROUTERS_NOTES_PY)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, (
            f"Expected zero matches for 'access_count' in {_ROUTERS_NOTES_PY}, "
            f"but rg returned exit {result.returncode} with matches:\n{result.stdout}"
        )

    def test_routers_notes_has_no_last_accessed_at_field(self):
        """
        Oracle: /features/7/oracle/assertions/6 (last_accessed_at reference)
        rg for 'last_accessed_at' in routers/notes.py must return exit 1.
        """
        assert _ROUTERS_NOTES_PY.exists(), f"notes.py not found at {_ROUTERS_NOTES_PY}"

        result = subprocess.run(
            ["rg", "-n", "last_accessed_at", str(_ROUTERS_NOTES_PY)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, (
            f"Expected zero matches for 'last_accessed_at' in {_ROUTERS_NOTES_PY}, "
            f"but rg returned exit {result.returncode} with matches:\n{result.stdout}"
        )

    def test_routers_notes_has_no_defer_embedding(self):
        """
        Oracle: /features/7/oracle/assertions/6 (defer(Note.embedding) reference)
        rg for 'defer' in routers/notes.py must return exit 1.
        Contract: /features/7/contract/routers_notes_py/list_query_defer_embedding_removed == true
        """
        assert _ROUTERS_NOTES_PY.exists(), f"notes.py not found at {_ROUTERS_NOTES_PY}"

        result = subprocess.run(
            ["rg", "-n", r"defer\(Note\.embedding\)", str(_ROUTERS_NOTES_PY)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, (
            f"Expected zero matches for 'defer(Note.embedding)' in {_ROUTERS_NOTES_PY}, "
            f"but rg returned exit {result.returncode} with matches:\n{result.stdout}"
        )


# ---------------------------------------------------------------------------
# /features/7/oracle/assertions/7
# ---------------------------------------------------------------------------


class TestSchemasPyNoDroppedResponseFields:
    """
    Static check: schemas/schemas.py has no accessCount / lastAccessedAt fields.
    Contract: /features/7/contract/schemas_py/NoteResponse_fields_removed
    """

    def test_schemas_py_has_no_accessCount_field(self):
        """
        Oracle: /features/7/oracle/assertions/7 (accessCount)
        rg for 'accessCount' in schemas.py must return exit 1.
        """
        assert _SCHEMAS_PY.exists(), f"schemas.py not found at {_SCHEMAS_PY}"

        result = subprocess.run(
            ["rg", "-n", "accessCount", str(_SCHEMAS_PY)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, (
            f"Expected zero matches for 'accessCount' in {_SCHEMAS_PY}, "
            f"but rg returned exit {result.returncode} with matches:\n{result.stdout}"
        )

    def test_schemas_py_has_no_lastAccessedAt_field(self):
        """
        Oracle: /features/7/oracle/assertions/7 (lastAccessedAt)
        rg for 'lastAccessedAt' in schemas.py must return exit 1.
        """
        assert _SCHEMAS_PY.exists(), f"schemas.py not found at {_SCHEMAS_PY}"

        result = subprocess.run(
            ["rg", "-n", "lastAccessedAt", str(_SCHEMAS_PY)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, (
            f"Expected zero matches for 'lastAccessedAt' in {_SCHEMAS_PY}, "
            f"but rg returned exit {result.returncode} with matches:\n{result.stdout}"
        )


# ---------------------------------------------------------------------------
# /features/7/oracle/assertions/8 — runtime CRUD against post-migration schema
# ---------------------------------------------------------------------------


class TestNotesCRUDPayloadHasNoDroppedFields:
    """
    Runtime CRUD verification: all Note endpoints return non-error status and
    serialized note payloads contain no 'accessCount' or 'lastAccessedAt' fields.

    Oracle: /features/7/oracle/assertions/8
    Contract: /features/7/contract/routers_notes_py and /features/7/contract/schemas_py

    Uses the standard conftest fixtures (client, auth_headers, sample_note_data,
    sample_note) which operate against the post-migration schema via testcontainers.
    """

    _DROPPED_FIELDS = {"accessCount", "lastAccessedAt"}

    def test_post_note_returns_201_or_200_without_dropped_fields(
        self, client: TestClient, auth_headers, sample_note_data
    ):
        """POST /api/notes/ returns 200 and payload has no accessCount/lastAccessedAt."""
        response = client.post("/api/notes/", headers=auth_headers, json=sample_note_data)
        assert (
            response.status_code == status.HTTP_200_OK
        ), f"POST /api/notes/ returned {response.status_code}: {response.text}"
        payload = response.json()
        present = self._DROPPED_FIELDS & set(payload.keys())
        assert present == set(), (
            f"POST /api/notes/ response contained dropped fields: {present}. "
            f"Full payload keys: {set(payload.keys())}"
        )

    def test_get_notes_list_returns_200_without_dropped_fields(self, client: TestClient, auth_headers, sample_note):
        """GET /api/notes/ returns 200 and each note payload has no accessCount/lastAccessedAt."""
        response = client.get("/api/notes/", headers=auth_headers)
        assert (
            response.status_code == status.HTTP_200_OK
        ), f"GET /api/notes/ returned {response.status_code}: {response.text}"
        notes = response.json()
        assert isinstance(notes, list)
        assert len(notes) >= 1
        for note in notes:
            present = self._DROPPED_FIELDS & set(note.keys())
            assert present == set(), (
                f"GET /api/notes/ note payload contained dropped fields: {present}. "
                f"Full payload keys: {set(note.keys())}"
            )

    def test_get_note_by_id_returns_200_without_dropped_fields(self, client: TestClient, auth_headers, sample_note):
        """GET /api/notes/{id} returns 200 and payload has no accessCount/lastAccessedAt."""
        response = client.get(f"/api/notes/{sample_note.id}", headers=auth_headers)
        assert (
            response.status_code == status.HTTP_200_OK
        ), f"GET /api/notes/{sample_note.id} returned {response.status_code}: {response.text}"
        payload = response.json()
        present = self._DROPPED_FIELDS & set(payload.keys())
        assert present == set(), (
            f"GET /api/notes/{{id}} response contained dropped fields: {present}. "
            f"Full payload keys: {set(payload.keys())}"
        )

    def test_put_note_returns_200_without_dropped_fields(self, client: TestClient, auth_headers, sample_note):
        """PUT /api/notes/{id} returns 200 and payload has no accessCount/lastAccessedAt."""
        update_data = {"title": "Updated Title F19", "content": "# Updated Title F19\n\nContent."}
        response = client.put(f"/api/notes/{sample_note.id}", headers=auth_headers, json=update_data)
        assert (
            response.status_code == status.HTTP_200_OK
        ), f"PUT /api/notes/{sample_note.id} returned {response.status_code}: {response.text}"
        payload = response.json()
        present = self._DROPPED_FIELDS & set(payload.keys())
        assert present == set(), (
            f"PUT /api/notes/{{id}} response contained dropped fields: {present}. "
            f"Full payload keys: {set(payload.keys())}"
        )

    def test_delete_note_returns_200_or_204(self, client: TestClient, auth_headers, sample_note):
        """DELETE /api/notes/{id} returns 200 or 204 (non-error status)."""
        response = client.delete(f"/api/notes/{sample_note.id}", headers=auth_headers)
        assert response.status_code in (
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
        ), f"DELETE /api/notes/{sample_note.id} returned {response.status_code}: {response.text}"
