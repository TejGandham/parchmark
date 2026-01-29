"""
Unit tests for transaction error handling in notes router.
Tests that database commit failures are properly handled with rollback and 500 responses.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.models.models import Note, User
from app.routers.notes import create_note, delete_note, update_note
from app.schemas.schemas import NoteCreate, NoteUpdate


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    return user


@pytest.fixture
def mock_db_session():
    """Create a mock async database session."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock()
    return session


class TestCreateNoteTransactionError:
    """Test transaction error handling in create_note endpoint."""

    @pytest.mark.asyncio
    async def test_create_note_commit_failure_returns_500(self, mock_user, mock_db_session):
        """Test that commit failure returns 500 and triggers rollback."""
        # Arrange
        note_data = NoteCreate(title="Test Note", content="# Test Note\n\nContent here.")
        mock_db_session.commit.side_effect = SQLAlchemyError("Database commit failed")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await create_note(note_data, mock_user, mock_db_session)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Database error" in exc_info.value.detail
        mock_db_session.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_note_refresh_failure_returns_500(self, mock_user, mock_db_session):
        """Test that refresh failure after commit returns 500 and triggers rollback."""
        # Arrange
        note_data = NoteCreate(title="Test Note", content="# Test Note\n\nContent here.")
        mock_db_session.refresh.side_effect = SQLAlchemyError("Database refresh failed")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await create_note(note_data, mock_user, mock_db_session)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Database error" in exc_info.value.detail
        mock_db_session.rollback.assert_awaited_once()


class TestUpdateNoteTransactionError:
    """Test transaction error handling in update_note endpoint."""

    @pytest.fixture
    def mock_existing_note(self):
        """Create a mock existing note."""
        note = MagicMock(spec=Note)
        note.id = "test-note-1"
        note.user_id = 1
        note.title = "Original Title"
        note.content = "# Original Title\n\nOriginal content."
        note.created_at = MagicMock()
        note.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        note.updated_at = MagicMock()
        note.updated_at.isoformat.return_value = "2024-01-01T00:00:00"
        return note

    @pytest.mark.asyncio
    async def test_update_note_commit_failure_returns_500(self, mock_user, mock_db_session, mock_existing_note):
        """Test that commit failure returns 500 and triggers rollback."""
        # Arrange
        note_data = NoteUpdate(content="# Updated Title\n\nUpdated content.")

        # Mock execute to return the existing note
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_existing_note
        mock_db_session.execute.return_value = mock_result

        mock_db_session.commit.side_effect = SQLAlchemyError("Database commit failed")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_note("test-note-1", note_data, mock_user, mock_db_session)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Database error" in exc_info.value.detail
        mock_db_session.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_note_refresh_failure_returns_500(self, mock_user, mock_db_session, mock_existing_note):
        """Test that refresh failure after commit returns 500 and triggers rollback."""
        # Arrange
        note_data = NoteUpdate(content="# Updated Title\n\nUpdated content.")

        # Mock execute to return the existing note
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_existing_note
        mock_db_session.execute.return_value = mock_result

        mock_db_session.refresh.side_effect = SQLAlchemyError("Database refresh failed")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_note("test-note-1", note_data, mock_user, mock_db_session)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Database error" in exc_info.value.detail
        mock_db_session.rollback.assert_awaited_once()


class TestDeleteNoteTransactionError:
    """Test transaction error handling in delete_note endpoint."""

    @pytest.fixture
    def mock_existing_note(self):
        """Create a mock existing note."""
        note = MagicMock(spec=Note)
        note.id = "test-note-1"
        note.user_id = 1
        note.title = "Test Note"
        note.content = "# Test Note\n\nContent."
        return note

    @pytest.mark.asyncio
    async def test_delete_note_commit_failure_returns_500(self, mock_user, mock_db_session, mock_existing_note):
        """Test that commit failure returns 500 and triggers rollback."""
        # Arrange
        # Mock execute to return the existing note
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_existing_note
        mock_db_session.execute.return_value = mock_result

        mock_db_session.commit.side_effect = SQLAlchemyError("Database commit failed")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await delete_note("test-note-1", mock_user, mock_db_session)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Database error" in exc_info.value.detail
        mock_db_session.rollback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_note_delete_failure_returns_500(self, mock_user, mock_db_session, mock_existing_note):
        """Test that delete failure returns 500 and triggers rollback."""
        # Arrange
        # Mock execute to return the existing note
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_existing_note
        mock_db_session.execute.return_value = mock_result

        mock_db_session.delete.side_effect = SQLAlchemyError("Database delete failed")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await delete_note("test-note-1", mock_user, mock_db_session)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Database error" in exc_info.value.detail
        mock_db_session.rollback.assert_awaited_once()
