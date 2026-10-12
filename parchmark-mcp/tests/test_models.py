"""Tests for Pydantic models."""

from datetime import UTC, datetime


def test_note_summary_from_api_response() -> None:
    """NoteSummary parses API response correctly."""
    from parchmark_mcp.models import NoteSummary

    data = {
        "id": "note-123",
        "title": "Test Note",
        "createdAt": "2026-01-28T10:00:00",
        "updatedAt": "2026-01-28T11:00:00",
    }
    note = NoteSummary.model_validate(data)
    assert note.id == "note-123"
    assert note.title == "Test Note"
    assert isinstance(note.createdAt, datetime)


def test_note_includes_content() -> None:
    """Note extends NoteSummary with content."""
    from parchmark_mcp.models import Note

    data = {
        "id": "note-123",
        "title": "Test Note",
        "content": "# Test Note\n\nBody text",
        "createdAt": "2026-01-28T10:00:00",
        "updatedAt": "2026-01-28T11:00:00",
    }
    note = Note.model_validate(data)
    assert note.content == "# Test Note\n\nBody text"


def test_notes_list_response() -> None:
    """NotesListResponse contains notes and count."""
    from parchmark_mcp.models import NotesListResponse, NoteSummary

    summary = NoteSummary(
        id="note-1",
        title="Note 1",
        createdAt=datetime.now(UTC),
        updatedAt=datetime.now(UTC),
    )
    response = NotesListResponse(notes=[summary], count=1)
    assert response.count == 1
    assert len(response.notes) == 1


def test_delete_response() -> None:
    """DeleteResponse contains success and message."""
    from parchmark_mcp.models import DeleteResponse

    response = DeleteResponse(success=True, message="Note deleted")
    assert response.success is True
    assert response.message == "Note deleted"
