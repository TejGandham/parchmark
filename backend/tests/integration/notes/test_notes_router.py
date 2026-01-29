"""
Integration tests for notes router (app.routers.notes).
Tests notes CRUD endpoints with real FastAPI client and database.
"""

from datetime import datetime

from fastapi import status
from fastapi.testclient import TestClient


class TestGetNotesEndpoint:
    """Test GET /notes/ endpoint."""

    def test_get_notes_empty_list(self, client: TestClient, auth_headers):
        """Test getting notes when user has no notes."""
        response = client.get("/api/notes/", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_notes_with_notes(self, client: TestClient, auth_headers, multiple_notes):
        """Test getting notes when user has notes."""
        response = client.get("/api/notes/", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == len(multiple_notes)

        # Verify response format
        for note_data in data:
            assert "id" in note_data
            assert "title" in note_data
            assert "content" in note_data
            assert "createdAt" in note_data
            assert "updatedAt" in note_data

    def test_get_notes_no_auth(self, client: TestClient):
        """Test getting notes without authentication."""
        response = client.get("/api/notes/")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_notes_invalid_token(self, client: TestClient):
        """Test getting notes with invalid token."""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/notes/", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_notes_user_isolation(self, client: TestClient, test_db_session):
        """Test that users only see their own notes."""
        from datetime import timedelta

        from app.auth.auth import create_access_token, get_password_hash
        from app.models.models import Note, User

        # Create two users
        user1 = User(username="user1", password_hash=get_password_hash("pass1"))
        user2 = User(username="user2", password_hash=get_password_hash("pass2"))
        test_db_session.add_all([user1, user2])
        test_db_session.commit()
        test_db_session.refresh(user1)
        test_db_session.refresh(user2)

        # Create notes for each user
        note1 = Note(id="user1-note", user_id=user1.id, title="User 1 Note", content="# User 1 Note\n\nContent 1")
        note2 = Note(id="user2-note", user_id=user2.id, title="User 2 Note", content="# User 2 Note\n\nContent 2")
        test_db_session.add_all([note1, note2])
        test_db_session.commit()

        # Test user1 only sees their note
        token1 = create_access_token({"sub": user1.username}, timedelta(minutes=30))
        headers1 = {"Authorization": f"Bearer {token1}"}
        response1 = client.get("/api/notes/", headers=headers1)

        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        assert len(data1) == 1
        assert data1[0]["id"] == "user1-note"

        # Test user2 only sees their note
        token2 = create_access_token({"sub": user2.username}, timedelta(minutes=30))
        headers2 = {"Authorization": f"Bearer {token2}"}
        response2 = client.get("/api/notes/", headers=headers2)

        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert len(data2) == 1
        assert data2[0]["id"] == "user2-note"

    def test_get_notes_response_format(self, client: TestClient, auth_headers, sample_note):
        """Test that notes response follows NoteResponse schema."""
        response = client.get("/api/notes/", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data) == 1

        note = data[0]
        required_fields = {"id", "title", "content", "createdAt", "updatedAt"}
        assert set(note.keys()) == required_fields

        # Verify datetime fields are ISO format strings
        datetime.fromisoformat(note["createdAt"])
        datetime.fromisoformat(note["updatedAt"])


class TestCreateNoteEndpoint:
    """Test POST /notes/ endpoint."""

    def test_create_note_success(self, client: TestClient, auth_headers, sample_note_data):
        """Test successful note creation."""
        response = client.post("/api/notes/", headers=auth_headers, json=sample_note_data)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "id" in data
        assert data["title"] == sample_note_data["title"]
        assert data["content"] == sample_note_data["content"]
        assert "createdAt" in data
        assert "updatedAt" in data

        # Verify ID format (note-{timestamp})
        assert data["id"].startswith("note-")
        assert len(data["id"]) > 5

    def test_create_note_with_explicit_title(self, client: TestClient, auth_headers):
        """Test note creation honors client-provided title."""
        note_data = {"title": "Explicit Title", "content": "# H1 Title\n\nContent here."}

        response = client.post("/api/notes/", headers=auth_headers, json=note_data)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Client-provided title should be used, not extracted from H1
        assert data["title"] == "Explicit Title"

    def test_create_note_without_title_extracts_from_h1(self, client: TestClient, auth_headers):
        """Test note creation extracts title from H1 when not provided."""
        note_data = {"content": "# Extracted Title\n\nContent here."}

        response = client.post("/api/notes/", headers=auth_headers, json=note_data)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Title should be extracted from markdown content H1
        assert data["title"] == "Extracted Title"

    def test_create_note_whitespace_title_extracts_from_h1(self, client: TestClient, auth_headers):
        """Test note creation treats whitespace-only title as absent."""
        note_data = {"title": "    ", "content": "# Extracted Title\n\nContent here."}

        response = client.post("/api/notes/", headers=auth_headers, json=note_data)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Whitespace-only title should be ignored, extract from H1 instead
        assert data["title"] == "Extracted Title"

    def test_create_note_title_whitespace_trimmed(self, client: TestClient, auth_headers):
        """Test note creation trims whitespace from valid titles."""
        note_data = {"title": "  Padded Title  ", "content": "# H1 Title\n\nContent here."}

        response = client.post("/api/notes/", headers=auth_headers, json=note_data)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Title should be trimmed
        assert data["title"] == "Padded Title"

    def test_create_note_content_formatting(self, client: TestClient, auth_headers):
        """Test note creation with content formatting."""
        note_data = {"title": "Test", "content": "# Title Only"}

        response = client.post("/api/notes/", headers=auth_headers, json=note_data)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Content should be formatted with proper spacing
        assert data["content"] == "# Title Only\n\n"

    def test_create_note_no_auth(self, client: TestClient, sample_note_data):
        """Test creating note without authentication."""
        response = client.post("/api/notes/", json=sample_note_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_note_invalid_token(self, client: TestClient, sample_note_data):
        """Test creating note with invalid token."""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.post("/api/notes/", headers=headers, json=sample_note_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_note_missing_title_succeeds(self, client: TestClient, auth_headers):
        """Test creating note with missing title succeeds (title extracted from content)."""
        note_data = {"content": "# Test Note\n\nContent here."}

        response = client.post("/api/notes/", headers=auth_headers, json=note_data)

        # Title is optional - should succeed with title extracted from H1
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Test Note"

    def test_create_note_missing_content(self, client: TestClient, auth_headers):
        """Test creating note with missing content."""
        note_data = {"title": "Test Note"}

        response = client.post("/api/notes/", headers=auth_headers, json=note_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_note_empty_title_fails_validation(self, client: TestClient, auth_headers):
        """Test creating note with empty title fails validation (min_length=4)."""
        note_data = {"title": "", "content": "# Test Note\n\nContent here."}

        response = client.post("/api/notes/", headers=auth_headers, json=note_data)

        # Empty string fails min_length=4 validation
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_note_empty_content(self, client: TestClient, auth_headers):
        """Test creating note with empty content - should fail validation."""
        note_data = {"title": "Test Note", "content": ""}

        response = client.post("/api/notes/", headers=auth_headers, json=note_data)

        # Empty content should fail validation (min length 4)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_note_large_content(self, client: TestClient, auth_headers):
        """Test creating note with large content."""
        large_content = "# Large Note\n\n" + ("Content line.\n" * 1000)
        note_data = {"title": "Large Note", "content": large_content}

        response = client.post("/api/notes/", headers=auth_headers, json=note_data)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Content might have trailing newline stripped or normalized
        assert data["content"].strip() == large_content.strip()

    def test_create_note_unique_ids(self, client: TestClient, auth_headers):
        """Test that created notes have unique IDs."""
        note_data = {"title": "Test Note", "content": "# Test Note\n\nContent."}

        # Create multiple notes
        ids = []
        for _ in range(3):
            response = client.post("/api/notes/", headers=auth_headers, json=note_data)
            assert response.status_code == status.HTTP_200_OK
            ids.append(response.json()["id"])

        # All IDs should be unique
        assert len(set(ids)) == len(ids)


class TestUpdateNoteEndpoint:
    """Test PUT /notes/{note_id} endpoint."""

    def test_update_note_success(self, client: TestClient, auth_headers, sample_note):
        """Test successful note update."""
        update_data = {"title": "Updated Title", "content": "# Updated Title\n\nUpdated content."}

        response = client.put(f"/api/notes/{sample_note.id}", headers=auth_headers, json=update_data)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == sample_note.id
        assert data["title"] == "Updated Title"
        assert data["content"] == "# Updated Title\n\nUpdated content."
        # Just verify updatedAt exists, timestamps might be same in fast test
        assert "updatedAt" in data
        assert "createdAt" in data

    def test_update_note_content_only(self, client: TestClient, auth_headers, sample_note):
        """Test updating note with only content."""
        update_data = {"content": "# New Title From Content\n\nNew content."}

        response = client.put(f"/api/notes/{sample_note.id}", headers=auth_headers, json=update_data)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Title should be extracted from new content
        assert data["title"] == "New Title From Content"
        assert data["content"] == "# New Title From Content\n\nNew content."

    def test_update_note_title_only(self, client: TestClient, auth_headers, sample_note):
        """Test updating note with only title."""
        update_data = {"title": "Only Title Update"}

        response = client.put(f"/api/notes/{sample_note.id}", headers=auth_headers, json=update_data)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["title"] == "Only Title Update"
        # Content should remain unchanged
        assert data["content"] == sample_note.content

    def test_update_note_not_found(self, client: TestClient, auth_headers):
        """Test updating non-existent note."""
        update_data = {"title": "Updated Title", "content": "Updated content."}

        response = client.put("/api/notes/non-existent-id", headers=auth_headers, json=update_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

        data = response.json()
        assert data["detail"] == "Note not found"

    def test_update_note_no_auth(self, client: TestClient, sample_note):
        """Test updating note without authentication."""
        update_data = {"title": "Updated Title"}

        response = client.put(f"/api/notes/{sample_note.id}", json=update_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_note_invalid_token(self, client: TestClient, sample_note):
        """Test updating note with invalid token."""
        headers = {"Authorization": "Bearer invalid.token.here"}
        update_data = {"title": "Updated Title"}

        response = client.put(f"/api/notes/{sample_note.id}", headers=headers, json=update_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_note_user_isolation(self, client: TestClient, test_db_session):
        """Test that users can only update their own notes."""
        from datetime import timedelta

        from app.auth.auth import create_access_token, get_password_hash
        from app.models.models import Note, User

        # Create two users
        user1 = User(username="user1", password_hash=get_password_hash("pass1"))
        user2 = User(username="user2", password_hash=get_password_hash("pass2"))
        test_db_session.add_all([user1, user2])
        test_db_session.commit()
        test_db_session.refresh(user1)
        test_db_session.refresh(user2)

        # Create note for user1
        note = Note(id="user1-note", user_id=user1.id, title="User 1 Note", content="# User 1 Note\n\nContent")
        test_db_session.add(note)
        test_db_session.commit()

        # Try to update with user2's token
        token2 = create_access_token({"sub": user2.username}, timedelta(minutes=30))
        headers2 = {"Authorization": f"Bearer {token2}"}

        update_data = {"title": "Hacked Title"}
        response = client.put(f"/api/notes/{note.id}", headers=headers2, json=update_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_note_empty_data(self, client: TestClient, auth_headers, sample_note):
        """Test updating note with empty data."""
        update_data = {}

        response = client.put(f"/api/notes/{sample_note.id}", headers=auth_headers, json=update_data)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Note should remain unchanged
        assert data["title"] == sample_note.title
        assert data["content"] == sample_note.content


class TestDeleteNoteEndpoint:
    """Test DELETE /notes/{note_id} endpoint."""

    def test_delete_note_success(self, client: TestClient, auth_headers, sample_note):
        """Test successful note deletion."""
        response = client.delete(f"/api/notes/{sample_note.id}", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "message" in data
        assert "deleted_id" in data
        assert data["deleted_id"] == sample_note.id
        assert "deleted successfully" in data["message"]

    def test_delete_note_not_found(self, client: TestClient, auth_headers):
        """Test deleting non-existent note."""
        response = client.delete("/api/notes/non-existent-id", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

        data = response.json()
        assert data["detail"] == "Note not found"

    def test_delete_note_no_auth(self, client: TestClient, sample_note):
        """Test deleting note without authentication."""
        response = client.delete(f"/api/notes/{sample_note.id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_note_invalid_token(self, client: TestClient, sample_note):
        """Test deleting note with invalid token."""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.delete(f"/api/notes/{sample_note.id}", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_note_user_isolation(self, client: TestClient, test_db_session):
        """Test that users can only delete their own notes."""
        from datetime import timedelta

        from app.auth.auth import create_access_token, get_password_hash
        from app.models.models import Note, User

        # Create two users
        user1 = User(username="user1", password_hash=get_password_hash("pass1"))
        user2 = User(username="user2", password_hash=get_password_hash("pass2"))
        test_db_session.add_all([user1, user2])
        test_db_session.commit()
        test_db_session.refresh(user1)
        test_db_session.refresh(user2)

        # Create note for user1
        note = Note(id="user1-note", user_id=user1.id, title="User 1 Note", content="# User 1 Note\n\nContent")
        test_db_session.add(note)
        test_db_session.commit()

        # Try to delete with user2's token
        token2 = create_access_token({"sub": user2.username}, timedelta(minutes=30))
        headers2 = {"Authorization": f"Bearer {token2}"}

        response = client.delete(f"/api/notes/{note.id}", headers=headers2)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_note_persistence(self, client: TestClient, auth_headers, sample_note, test_db_session):
        """Test that note is actually deleted from database."""
        from app.models.models import Note

        note_id = sample_note.id

        # Verify note exists
        existing_note = test_db_session.query(Note).filter(Note.id == note_id).first()
        assert existing_note is not None

        # Delete note
        response = client.delete(f"/api/notes/{note_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        # Verify note is deleted from database
        deleted_note = test_db_session.query(Note).filter(Note.id == note_id).first()
        assert deleted_note is None


class TestGetSingleNoteEndpoint:
    """Test GET /notes/{note_id} endpoint."""

    def test_get_note_success(self, client: TestClient, auth_headers, sample_note):
        """Test successful single note retrieval."""
        response = client.get(f"/api/notes/{sample_note.id}", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == sample_note.id
        assert data["title"] == sample_note.title
        assert data["content"] == sample_note.content
        assert "createdAt" in data
        assert "updatedAt" in data

    def test_get_note_not_found(self, client: TestClient, auth_headers):
        """Test getting non-existent note."""
        response = client.get("/api/notes/non-existent-id", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

        data = response.json()
        assert data["detail"] == "Note not found"

    def test_get_note_no_auth(self, client: TestClient, sample_note):
        """Test getting note without authentication."""
        response = client.get(f"/api/notes/{sample_note.id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_note_invalid_token(self, client: TestClient, sample_note):
        """Test getting note with invalid token."""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get(f"/api/notes/{sample_note.id}", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_note_user_isolation(self, client: TestClient, test_db_session):
        """Test that users can only get their own notes."""
        from datetime import timedelta

        from app.auth.auth import create_access_token, get_password_hash
        from app.models.models import Note, User

        # Create two users
        user1 = User(username="user1", password_hash=get_password_hash("pass1"))
        user2 = User(username="user2", password_hash=get_password_hash("pass2"))
        test_db_session.add_all([user1, user2])
        test_db_session.commit()
        test_db_session.refresh(user1)
        test_db_session.refresh(user2)

        # Create note for user1
        note = Note(id="user1-note", user_id=user1.id, title="User 1 Note", content="# User 1 Note\n\nContent")
        test_db_session.add(note)
        test_db_session.commit()

        # Try to get with user2's token
        token2 = create_access_token({"sub": user2.username}, timedelta(minutes=30))
        headers2 = {"Authorization": f"Bearer {token2}"}

        response = client.get(f"/api/notes/{note.id}", headers=headers2)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestNotesHealthEndpoint:
    """Test /notes/health/check endpoint."""

    def test_notes_health_check(self, client: TestClient):
        """Test notes service health check."""
        response = client.get("/api/notes/health/check")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "status" in data
        assert data["status"] == "Notes service is healthy"

    def test_notes_health_check_no_auth_required(self, client: TestClient):
        """Test that health check doesn't require authentication."""
        response = client.get("/api/notes/health/check")

        assert response.status_code == status.HTTP_200_OK


class TestNotesRouterIntegration:
    """Test integration between notes router endpoints."""

    def test_full_notes_crud_flow(self, client: TestClient, auth_headers):
        """Test complete CRUD flow: create -> read -> update -> delete."""
        # Step 1: Create note
        create_data = {"title": "Test Note", "content": "# Test Note\n\nOriginal content."}
        create_response = client.post("/api/notes/", headers=auth_headers, json=create_data)
        assert create_response.status_code == status.HTTP_200_OK

        note_id = create_response.json()["id"]

        # Step 2: Read note
        get_response = client.get(f"/api/notes/{note_id}", headers=auth_headers)
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["title"] == "Test Note"

        # Step 3: Update note
        update_data = {"content": "# Updated Note\n\nUpdated content."}
        update_response = client.put(f"/api/notes/{note_id}", headers=auth_headers, json=update_data)
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["title"] == "Updated Note"

        # Step 4: Delete note
        delete_response = client.delete(f"/api/notes/{note_id}", headers=auth_headers)
        assert delete_response.status_code == status.HTTP_200_OK

        # Step 5: Verify note is deleted
        get_after_delete = client.get(f"/api/notes/{note_id}", headers=auth_headers)
        assert get_after_delete.status_code == status.HTTP_404_NOT_FOUND

    def test_notes_list_reflects_operations(self, client: TestClient, auth_headers):
        """Test that notes list reflects create/delete operations."""
        # Initial state - no notes
        list_response = client.get("/api/notes/", headers=auth_headers)
        assert len(list_response.json()) == 0

        # Create multiple notes
        note_ids = []
        for i in range(3):
            create_data = {"title": f"Note {i}", "content": f"# Note {i}\n\nContent {i}."}
            response = client.post("/api/notes/", headers=auth_headers, json=create_data)
            note_ids.append(response.json()["id"])

        # List should show all notes
        list_response = client.get("/api/notes/", headers=auth_headers)
        assert len(list_response.json()) == 3

        # Delete one note
        client.delete(f"/api/notes/{note_ids[0]}", headers=auth_headers)

        # List should show remaining notes
        list_response = client.get("/api/notes/", headers=auth_headers)
        assert len(list_response.json()) == 2

        # Verify correct notes remain
        remaining_ids = {note["id"] for note in list_response.json()}
        assert note_ids[0] not in remaining_ids
        assert note_ids[1] in remaining_ids
        assert note_ids[2] in remaining_ids

    def test_concurrent_note_operations(self, client: TestClient, auth_headers):
        """Test concurrent note operations."""
        # Create base note
        create_data = {"title": "Base Note", "content": "# Base Note\n\nBase content."}
        response = client.post("/api/notes/", headers=auth_headers, json=create_data)
        note_id = response.json()["id"]

        # Simulate concurrent updates (in real scenario these would be parallel)
        update_results = []
        for i in range(3):
            update_data = {"content": f"# Updated Note {i}\n\nUpdate {i}."}
            response = client.put(f"/api/notes/{note_id}", headers=auth_headers, json=update_data)
            update_results.append(response.status_code)

        # All updates should succeed
        assert all(status_code == status.HTTP_200_OK for status_code in update_results)

        # Final state should reflect last update
        final_response = client.get(f"/api/notes/{note_id}", headers=auth_headers)
        assert "Update 2" in final_response.json()["content"]


class TestNotesRouterErrorHandling:
    """Test error handling in notes router."""

    def test_malformed_json_requests(self, client: TestClient, auth_headers):
        """Test handling of malformed JSON in requests."""
        endpoints = [
            ("POST", "/api/notes/"),
            ("PUT", "/api/notes/test-id"),
        ]

        for method, endpoint in endpoints:
            response = client.request(
                method,
                endpoint,
                headers=auth_headers,
                content="invalid json",
                # Note: not setting content-type to application/json
            )

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_note_ids(self, client: TestClient, auth_headers):
        """Test handling of various invalid note IDs."""
        invalid_ids = [
            "",
            " ",
            "../../etc/passwd",
            "<script>alert('xss')</script>",
            "note with spaces",
            "very-long-" + "x" * 1000 + "-id",
        ]

        for invalid_id in invalid_ids:
            # Test GET - response depends on the invalid_id format
            get_response = client.get(f"/api/notes/{invalid_id}", headers=auth_headers)
            # Some IDs might pass validation but not exist (404), others might be invalid format (422 or 200), or method not allowed (405)
            assert get_response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_405_METHOD_NOT_ALLOWED,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ]

            # Test PUT
            update_data = {"title": "Test"}
            put_response = client.put(f"/api/notes/{invalid_id}", headers=auth_headers, json=update_data)
            assert put_response.status_code in [
                status.HTTP_404_NOT_FOUND,
                status.HTTP_405_METHOD_NOT_ALLOWED,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ]

            # Test DELETE
            delete_response = client.delete(f"/api/notes/{invalid_id}", headers=auth_headers)
            assert delete_response.status_code in [
                status.HTTP_404_NOT_FOUND,
                status.HTTP_405_METHOD_NOT_ALLOWED,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ]
