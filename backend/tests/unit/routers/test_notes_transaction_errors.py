"""
Unit tests for transaction error handling in notes router.
Tests that service-layer database exceptions are properly handled by the router with 500 responses.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.models.models import User
from app.services.note_service import NoteServiceError


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    return user


class TestCreateNoteTransactionError:
    """Test transaction error handling in create_note endpoint."""

    @patch("app.routers.notes.note_service")
    def test_create_note_commit_failure_returns_500(self, mock_service, client: TestClient, auth_headers):
        """Test that NoteServiceError returns 500."""
        # Arrange
        mock_service.create_note = AsyncMock(side_effect=NoteServiceError("Database commit failed"))

        # Act
        response = client.post("/api/notes/", json={"content": "# Test\n\nContent"}, headers=auth_headers)

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Database error" in response.json()["detail"]

    @patch("app.routers.notes.note_service")
    def test_create_note_refresh_failure_returns_500(self, mock_service, client: TestClient, auth_headers):
        """Test that refresh failure (via NoteServiceError) returns 500."""
        # Arrange
        mock_service.create_note = AsyncMock(side_effect=NoteServiceError("Database refresh failed"))

        # Act
        response = client.post("/api/notes/", json={"content": "# Test\n\nContent"}, headers=auth_headers)

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Database error" in response.json()["detail"]


class TestUpdateNoteTransactionError:
    """Test transaction error handling in update_note endpoint."""

    @patch("app.routers.notes.note_service")
    def test_update_note_commit_failure_returns_500(self, mock_service, client: TestClient, auth_headers, sample_note):
        """Test that commit failure returns 500."""
        # Arrange
        mock_service.update_note = AsyncMock(side_effect=NoteServiceError("Database commit failed"))

        # Act
        response = client.put(
            f"/api/notes/{sample_note.id}",
            json={"content": "# Updated\n\nUpdated content."},
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Database error" in response.json()["detail"]

    @patch("app.routers.notes.note_service")
    def test_update_note_refresh_failure_returns_500(self, mock_service, client: TestClient, auth_headers, sample_note):
        """Test that refresh failure after commit returns 500."""
        # Arrange
        mock_service.update_note = AsyncMock(side_effect=NoteServiceError("Database refresh failed"))

        # Act
        response = client.put(
            f"/api/notes/{sample_note.id}",
            json={"content": "# Updated\n\nUpdated content."},
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Database error" in response.json()["detail"]


class TestDeleteNoteTransactionError:
    """Test transaction error handling in delete_note endpoint."""

    @patch("app.routers.notes.note_service")
    def test_delete_note_commit_failure_returns_500(self, mock_service, client: TestClient, auth_headers, sample_note):
        """Test that commit failure returns 500."""
        # Arrange
        mock_service.delete_note = AsyncMock(side_effect=NoteServiceError("Database commit failed"))

        # Act
        response = client.delete(f"/api/notes/{sample_note.id}", headers=auth_headers)

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Database error" in response.json()["detail"]

    @patch("app.routers.notes.note_service")
    def test_delete_note_delete_failure_returns_500(self, mock_service, client: TestClient, auth_headers, sample_note):
        """Test that delete failure returns 500."""
        # Arrange
        mock_service.delete_note = AsyncMock(side_effect=NoteServiceError("Database delete failed"))

        # Act
        response = client.delete(f"/api/notes/{sample_note.id}", headers=auth_headers)

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Database error" in response.json()["detail"]
