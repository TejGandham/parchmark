"""Integration tests for note access tracking endpoint (POST /notes/{note_id}/access)."""

from datetime import UTC, datetime, timedelta

from fastapi import status
from fastapi.testclient import TestClient


class TestTrackNoteAccessEndpoint:
    """Test POST /notes/{note_id}/access endpoint."""

    def test_track_access_increments_count(self, client: TestClient, auth_headers, sample_note):
        response = client.post(f"/api/notes/{sample_note.id}/access", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["accessCount"] == 1
        assert data["lastAccessedAt"] is not None

    def test_track_access_multiple_increments(self, client: TestClient, auth_headers, sample_note):
        response = None
        for _ in range(3):
            response = client.post(f"/api/notes/{sample_note.id}/access", headers=auth_headers)
            assert response.status_code == status.HTTP_200_OK

        assert response is not None
        data = response.json()
        assert data["accessCount"] == 3
        assert data["lastAccessedAt"] is not None

        last_accessed = datetime.fromisoformat(data["lastAccessedAt"])
        assert datetime.now(UTC) - last_accessed < timedelta(seconds=10)

    def test_track_access_returns_full_note_response(self, client: TestClient, auth_headers, sample_note):
        response = client.post(f"/api/notes/{sample_note.id}/access", headers=auth_headers)

        data = response.json()
        assert data["id"] == sample_note.id
        assert data["title"] == sample_note.title
        assert data["content"] == sample_note.content
        assert "createdAt" in data
        assert "updatedAt" in data
        assert "accessCount" in data
        assert "lastAccessedAt" in data

    def test_track_access_not_found(self, client: TestClient, auth_headers):
        response = client.post("/api/notes/non-existent-id/access", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Note not found"

    def test_track_access_no_auth(self, client: TestClient, sample_note):
        response = client.post(f"/api/notes/{sample_note.id}/access")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_track_access_invalid_token(self, client: TestClient, sample_note):
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.post(f"/api/notes/{sample_note.id}/access", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_track_access_user_isolation(self, client: TestClient, test_db_session):
        from datetime import timedelta as td

        from app.auth.auth import create_access_token, get_password_hash
        from app.models.models import Note, User

        user1 = User(username="user1", password_hash=get_password_hash("pass1"))
        user2 = User(username="user2", password_hash=get_password_hash("pass2"))
        test_db_session.add_all([user1, user2])
        test_db_session.commit()
        test_db_session.refresh(user1)
        test_db_session.refresh(user2)

        note = Note(id="user1-note", user_id=user1.id, title="User 1 Note", content="# User 1 Note\n\nContent")
        test_db_session.add(note)
        test_db_session.commit()

        token2 = create_access_token({"sub": user2.username}, td(minutes=30))
        headers2 = {"Authorization": f"Bearer {token2}"}

        response = client.post(f"/api/notes/{note.id}/access", headers=headers2)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_track_access_does_not_modify_content(self, client: TestClient, auth_headers, sample_note):
        original_title = sample_note.title
        original_content = sample_note.content

        client.post(f"/api/notes/{sample_note.id}/access", headers=auth_headers)

        get_response = client.get(f"/api/notes/{sample_note.id}", headers=auth_headers)
        data = get_response.json()
        assert data["title"] == original_title
        assert data["content"] == original_content

    def test_existing_endpoints_include_access_fields(self, client: TestClient, auth_headers, sample_note):
        get_response = client.get(f"/api/notes/{sample_note.id}", headers=auth_headers)
        data = get_response.json()
        assert "accessCount" in data
        assert data["accessCount"] == 0
        assert data["lastAccessedAt"] is None

    def test_create_note_has_default_access_fields(self, client: TestClient, auth_headers):
        create_data = {"title": "New Note", "content": "# New Note\n\nContent here."}
        response = client.post("/api/notes/", headers=auth_headers, json=create_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["accessCount"] == 0
        assert data["lastAccessedAt"] is None
