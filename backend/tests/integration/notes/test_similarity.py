from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient

from app.models.models import Note

DIMS = 1536


def _pad(vec: list[float]) -> list[float]:
    return vec + [0.0] * (DIMS - len(vec))


EMBEDDING_A = _pad([1.0, 0.0, 0.0])
EMBEDDING_B = _pad([0.9, 0.1, 0.0])
EMBEDDING_C = _pad([0.0, 1.0, 0.0])


def create_note_with_embedding(test_db_session, sample_user, note_id: str, title: str, embedding: list[float] | None):
    note = Note(
        id=note_id,
        user_id=sample_user.id,
        title=title,
        content=f"# {title}\n\nContent",
        embedding=embedding,
    )
    test_db_session.add(note)
    test_db_session.commit()
    test_db_session.refresh(note)
    return note


class TestSimilarNotesEndpoint:
    def test_get_similar_notes_returns_sorted_results(
        self, client: TestClient, auth_headers, test_db_session, sample_user
    ):
        target = create_note_with_embedding(test_db_session, sample_user, "target-note", "Target", EMBEDDING_A)
        most_similar = create_note_with_embedding(test_db_session, sample_user, "similar-1", "Similar 1", EMBEDDING_B)
        somewhat_similar = create_note_with_embedding(
            test_db_session,
            sample_user,
            "similar-2",
            "Similar 2",
            _pad([0.6, 0.4, 0.0]),
        )

        response = client.get(f"/api/notes/{target.id}/similar", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == most_similar.id
        assert data[1]["id"] == somewhat_similar.id
        assert data[0]["similarity"] > data[1]["similarity"]

    def test_get_similar_notes_returns_empty_when_target_has_no_embedding(
        self, client: TestClient, auth_headers, test_db_session, sample_user
    ):
        target = create_note_with_embedding(test_db_session, sample_user, "target-no-embedding", "Target", None)

        response = client.get(f"/api/notes/{target.id}/similar", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_similar_notes_returns_empty_when_no_other_embedded_notes(
        self, client: TestClient, auth_headers, test_db_session, sample_user
    ):
        target = create_note_with_embedding(test_db_session, sample_user, "target-only", "Target", EMBEDDING_A)
        create_note_with_embedding(test_db_session, sample_user, "other-no-embedding", "Other", None)

        response = client.get(f"/api/notes/{target.id}/similar", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_similar_notes_respects_count(self, client: TestClient, auth_headers, test_db_session, sample_user):
        target = create_note_with_embedding(test_db_session, sample_user, "target-count", "Target", EMBEDDING_A)
        create_note_with_embedding(test_db_session, sample_user, "note-1", "Note 1", EMBEDDING_B)
        create_note_with_embedding(test_db_session, sample_user, "note-2", "Note 2", _pad([0.8, 0.2, 0.0]))
        create_note_with_embedding(test_db_session, sample_user, "note-3", "Note 3", _pad([0.7, 0.3, 0.0]))
        create_note_with_embedding(test_db_session, sample_user, "note-4", "Note 4", _pad([0.6, 0.4, 0.0]))

        response = client.get(f"/api/notes/{target.id}/similar?count=2", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["similarity"] >= data[1]["similarity"]

    def test_get_similar_notes_requires_auth(self, client: TestClient, test_db_session, sample_user):
        target = create_note_with_embedding(test_db_session, sample_user, "target-auth", "Target", EMBEDDING_A)

        response = client.get(f"/api/notes/{target.id}/similar")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_similar_notes_not_found(self, client: TestClient, auth_headers):
        response = client.get("/api/notes/non-existent-note/similar", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Note not found"


class TestEmbeddingGenerationOnMutations:
    @patch("app.routers.notes.generate_embedding")
    def test_create_note_generates_embedding(
        self, mock_generate_embedding, client: TestClient, auth_headers, test_db_session, sample_user
    ):
        expected_embedding = _pad([0.1, 0.2, 0.3])
        mock_generate_embedding.return_value = expected_embedding

        response = client.post(
            "/api/notes/",
            headers=auth_headers,
            json={"title": "Embedding Note", "content": "# Embedding Note\n\nBody"},
        )

        assert response.status_code == status.HTTP_200_OK
        created_id = response.json()["id"]

        stored = test_db_session.query(Note).filter(Note.id == created_id, Note.user_id == sample_user.id).first()
        assert stored is not None
        assert stored.embedding is not None
        mock_generate_embedding.assert_called_once()

    @patch("app.routers.notes.generate_embedding")
    def test_update_note_regenerates_embedding_on_content_update(
        self, mock_generate_embedding, client: TestClient, auth_headers, test_db_session, sample_user
    ):
        note = create_note_with_embedding(test_db_session, sample_user, "update-note", "Update Note", EMBEDDING_A)
        new_embedding = EMBEDDING_C
        mock_generate_embedding.return_value = new_embedding

        response = client.put(
            f"/api/notes/{note.id}",
            headers=auth_headers,
            json={"content": "# Updated\n\nUpdated body"},
        )

        assert response.status_code == status.HTTP_200_OK
        test_db_session.expire_all()
        updated = test_db_session.query(Note).filter(Note.id == note.id, Note.user_id == sample_user.id).first()
        assert updated is not None
        assert updated.embedding is not None
        mock_generate_embedding.assert_called_once()

    @patch("app.routers.notes.generate_embedding")
    def test_create_note_succeeds_when_embedding_generation_returns_none(
        self, mock_generate_embedding, client: TestClient, auth_headers, test_db_session, sample_user
    ):
        mock_generate_embedding.return_value = None

        response = client.post(
            "/api/notes/",
            headers=auth_headers,
            json={"title": "No Embedding", "content": "# No Embedding\n\nBody"},
        )

        assert response.status_code == status.HTTP_200_OK
        created_id = response.json()["id"]
        stored = test_db_session.query(Note).filter(Note.id == created_id, Note.user_id == sample_user.id).first()
        assert stored is not None
        assert stored.embedding is None
        mock_generate_embedding.assert_called_once()
