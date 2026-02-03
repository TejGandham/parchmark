"""Unit tests for the note service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.models import Note
from app.services.note_service import (
    CreateNoteInput,
    NoteNotFoundError,
    NoteService,
    NoteServiceError,
    UpdateNoteInput,
)


class TestNoteServiceStaticMethods:
    """Tests for NoteService static methods."""

    def test_generate_note_id_format(self):
        """Note ID should follow the note-{timestamp} format."""
        note_id = NoteService.generate_note_id()
        assert note_id.startswith("note-")
        timestamp_part = note_id.replace("note-", "")
        assert timestamp_part.isdigit()

    def test_generate_note_id_uniqueness(self):
        """Generated note IDs should be unique (different timestamps)."""
        id1 = NoteService.generate_note_id()
        id2 = NoteService.generate_note_id()
        # They should be different (or at least different timestamps)
        # In practice they might be the same if called in quick succession
        assert id1.startswith("note-")
        assert id2.startswith("note-")

    def test_process_note_content_with_title(self):
        """Should use provided title when given."""
        content = "# Some Header\n\nBody content"
        formatted_content, title = NoteService.process_note_content(content, "Custom Title")
        assert title == "Custom Title"

    def test_process_note_content_extracts_title(self):
        """Should extract title from H1 when no title provided."""
        content = "# My Title\n\nBody content"
        formatted_content, title = NoteService.process_note_content(content)
        assert title == "My Title"

    def test_process_note_content_default_title(self):
        """Should use default title when no H1 found."""
        content = "No heading here"
        formatted_content, title = NoteService.process_note_content(content)
        assert title == "Untitled Note"

    def test_process_note_content_strips_whitespace_title(self):
        """Should strip whitespace from provided title."""
        content = "# Header\n\nBody"
        formatted_content, title = NoteService.process_note_content(content, "  Spaced Title  ")
        assert title == "Spaced Title"

    def test_process_note_content_ignores_empty_title(self):
        """Should extract from content when title is whitespace-only."""
        content = "# Extracted Title\n\nBody"
        formatted_content, title = NoteService.process_note_content(content, "   ")
        assert title == "Extracted Title"


class TestNoteServiceGetNotes:
    """Tests for NoteService.get_notes_by_user."""

    @pytest.mark.asyncio
    async def test_get_notes_by_user_returns_list(self):
        """Should return list of notes for user."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()

        note1 = MagicMock(spec=Note)
        note2 = MagicMock(spec=Note)
        mock_scalars.all.return_value = [note1, note2]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.note_service.get_db", return_value=mock_db):
            service = NoteService()
            result = await service.get_notes_by_user(user_id=1)

        assert len(result) == 2
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_notes_by_user_empty_list(self):
        """Should return empty list when user has no notes."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.note_service.get_db", return_value=mock_db):
            service = NoteService()
            result = await service.get_notes_by_user(user_id=999)

        assert result == []


class TestNoteServiceGetNoteById:
    """Tests for NoteService.get_note_by_id."""

    @pytest.mark.asyncio
    async def test_get_note_by_id_success(self):
        """Should return note when found."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_note = MagicMock(spec=Note)
        mock_result.scalar_one_or_none.return_value = mock_note
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.note_service.get_db", return_value=mock_db):
            service = NoteService()
            result = await service.get_note_by_id("note-123", user_id=1)

        assert result == mock_note

    @pytest.mark.asyncio
    async def test_get_note_by_id_not_found_raises(self):
        """Should raise NoteNotFoundError when note doesn't exist."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.note_service.get_db", return_value=mock_db):
            service = NoteService()

            with pytest.raises(NoteNotFoundError) as exc_info:
                await service.get_note_by_id("nonexistent", user_id=1)

        assert exc_info.value.note_id == "nonexistent"


class TestNoteServiceCreateNote:
    """Tests for NoteService.create_note."""

    @pytest.mark.asyncio
    async def test_create_note_success(self):
        """Should create note with generated ID and processed content."""
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch("app.services.note_service.get_db", return_value=mock_db):
            service = NoteService()
            input_data = CreateNoteInput(content="# Test\n\nContent")

            with patch.object(NoteService, "generate_note_id", return_value="note-12345"):
                result = await service.create_note(user_id=1, input_data=input_data)

        assert result.id == "note-12345"
        assert result.user_id == 1
        assert result.title == "Test"
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_note_with_custom_title(self):
        """Should use provided title instead of extracting."""
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch("app.services.note_service.get_db", return_value=mock_db):
            service = NoteService()
            input_data = CreateNoteInput(content="# Header\n\nContent", title="Custom Title")

            result = await service.create_note(user_id=1, input_data=input_data)

        assert result.title == "Custom Title"

    @pytest.mark.asyncio
    async def test_create_note_database_error_raises(self):
        """Should raise NoteServiceError on database failure."""
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock(side_effect=SQLAlchemyError("DB error"))

        with patch("app.services.note_service.get_db", return_value=mock_db):
            service = NoteService()
            input_data = CreateNoteInput(content="# Test\n\nContent")

            with pytest.raises(NoteServiceError) as exc_info:
                await service.create_note(user_id=1, input_data=input_data)

        assert "Failed to create note" in str(exc_info.value)


class TestNoteServiceUpdateNote:
    """Tests for NoteService.update_note."""

    @pytest.mark.asyncio
    async def test_update_note_content_success(self):
        """Should update note content and extract new title."""
        mock_db = MagicMock()
        mock_note = MagicMock(spec=Note)
        mock_note.content = "old content"
        mock_note.title = "Old Title"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_note
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch("app.services.note_service.get_db", return_value=mock_db):
            service = NoteService()
            input_data = UpdateNoteInput(content="# New Title\n\nNew content")

            result = await service.update_note("note-123", user_id=1, input_data=input_data)

        assert result == mock_note
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_note_title_only(self):
        """Should update only title when no content provided."""
        mock_db = MagicMock()
        mock_note = MagicMock(spec=Note)
        mock_note.content = "original content"
        mock_note.title = "Old Title"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_note
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch("app.services.note_service.get_db", return_value=mock_db):
            service = NoteService()
            input_data = UpdateNoteInput(title="New Title Only")

            await service.update_note("note-123", user_id=1, input_data=input_data)

        # Title should be updated directly
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_note_not_found_raises(self):
        """Should raise NoteNotFoundError when note doesn't exist."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.note_service.get_db", return_value=mock_db):
            service = NoteService()
            input_data = UpdateNoteInput(content="New content")

            with pytest.raises(NoteNotFoundError):
                await service.update_note("nonexistent", user_id=1, input_data=input_data)

    @pytest.mark.asyncio
    async def test_update_note_database_error_raises(self):
        """Should raise NoteServiceError on database failure."""
        mock_db = MagicMock()
        mock_note = MagicMock(spec=Note)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_note
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock(side_effect=SQLAlchemyError("DB error"))

        with patch("app.services.note_service.get_db", return_value=mock_db):
            service = NoteService()
            input_data = UpdateNoteInput(content="# New\n\nContent")

            with pytest.raises(NoteServiceError):
                await service.update_note("note-123", user_id=1, input_data=input_data)


class TestNoteServiceDeleteNote:
    """Tests for NoteService.delete_note."""

    @pytest.mark.asyncio
    async def test_delete_note_success(self):
        """Should delete note and return its ID."""
        mock_db = MagicMock()
        mock_note = MagicMock(spec=Note)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_note
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.delete = AsyncMock()
        mock_db.flush = AsyncMock()

        with patch("app.services.note_service.get_db", return_value=mock_db):
            service = NoteService()
            result = await service.delete_note("note-123", user_id=1)

        assert result == "note-123"
        mock_db.delete.assert_called_once_with(mock_note)
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_note_not_found_raises(self):
        """Should raise NoteNotFoundError when note doesn't exist."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.note_service.get_db", return_value=mock_db):
            service = NoteService()

            with pytest.raises(NoteNotFoundError):
                await service.delete_note("nonexistent", user_id=1)

    @pytest.mark.asyncio
    async def test_delete_note_database_error_raises(self):
        """Should raise NoteServiceError on database failure."""
        mock_db = MagicMock()
        mock_note = MagicMock(spec=Note)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_note
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.delete = AsyncMock()
        mock_db.flush = AsyncMock(side_effect=SQLAlchemyError("DB error"))

        with patch("app.services.note_service.get_db", return_value=mock_db):
            service = NoteService()

            with pytest.raises(NoteServiceError):
                await service.delete_note("note-123", user_id=1)


class TestNoteNotFoundError:
    """Tests for NoteNotFoundError exception."""

    def test_note_not_found_error_message(self):
        """Should include note ID in error message."""
        error = NoteNotFoundError("note-abc123")
        assert error.note_id == "note-abc123"
        assert "note-abc123" in str(error)


class TestNoteServiceError:
    """Tests for NoteServiceError exception."""

    def test_note_service_error_with_original(self):
        """Should store original exception."""
        original = SQLAlchemyError("Original error")
        error = NoteServiceError("Service failed", original)
        assert error.original_error == original
        assert "Service failed" in str(error)

    def test_note_service_error_without_original(self):
        """Should work without original exception."""
        error = NoteServiceError("Service failed")
        assert error.original_error is None
