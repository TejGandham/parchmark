"""
Integration tests for persisted note tags in the notes API.
"""

from datetime import timedelta

from fastapi import status
from fastapi.testclient import TestClient

from app.auth.auth import create_access_token, get_password_hash
from app.models.models import Note, NoteTag, User


def test_get_notes_returns_tags(client: TestClient, auth_headers, sample_note, test_db_session):
    sample_note.tags = [NoteTag(tag="work"), NoteTag(tag="draft")]
    test_db_session.commit()

    response = client.get("/api/notes/", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["tags"] == ["draft", "work"]


def test_get_note_returns_empty_tags_for_untagged_note(client: TestClient, auth_headers, sample_note):
    response = client.get(f"/api/notes/{sample_note.id}", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["tags"] == []


def test_create_note_normalizes_and_deduplicates_tags(client: TestClient, auth_headers):
    response = client.post(
        "/api/notes/",
        headers=auth_headers,
        json={
            "content": "# Tagged Note\n\nContent",
            "tags": [" Work ", "#work", "Daily Log", "daily_log"],
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["tags"] == ["daily-log", "daily_log", "work"]


def test_create_note_without_tags_returns_empty_tags(client: TestClient, auth_headers):
    response = client.post(
        "/api/notes/",
        headers=auth_headers,
        json={"content": "# Untagged Note\n\nContent"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["tags"] == []


def test_update_note_replaces_clears_and_preserves_tags(client: TestClient, auth_headers, sample_note, test_db_session):
    sample_note.tags = [NoteTag(tag="draft")]
    test_db_session.commit()

    replace_response = client.put(
        f"/api/notes/{sample_note.id}",
        headers=auth_headers,
        json={"tags": ["Work", "Ideas"]},
    )
    assert replace_response.status_code == status.HTTP_200_OK
    assert replace_response.json()["tags"] == ["ideas", "work"]

    keep_response = client.put(
        f"/api/notes/{sample_note.id}",
        headers=auth_headers,
        json={"title": "Title Only Update"},
    )
    assert keep_response.status_code == status.HTTP_200_OK
    assert keep_response.json()["tags"] == ["ideas", "work"]

    clear_response = client.put(
        f"/api/notes/{sample_note.id}",
        headers=auth_headers,
        json={"tags": []},
    )
    assert clear_response.status_code == status.HTTP_200_OK
    assert clear_response.json()["tags"] == []


def test_invalid_tag_values_fail_validation(client: TestClient, auth_headers):
    response = client.post(
        "/api/notes/",
        headers=auth_headers,
        json={"content": "# Bad Tag\n\nContent", "tags": ["valid", "bad/tag"]},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_user_cannot_see_another_users_tags(client: TestClient, test_db_session):
    user1 = User(username="tag-user-1", password_hash=get_password_hash("pass1"))
    user2 = User(username="tag-user-2", password_hash=get_password_hash("pass2"))
    test_db_session.add_all([user1, user2])
    test_db_session.commit()
    test_db_session.refresh(user1)
    test_db_session.refresh(user2)

    note1 = Note(id="tag-user-1-note", user_id=user1.id, title="User 1", content="# User 1\n\nContent")
    note1.tags = [NoteTag(tag="private")]
    note2 = Note(id="tag-user-2-note", user_id=user2.id, title="User 2", content="# User 2\n\nContent")
    note2.tags = [NoteTag(tag="shared-name")]
    test_db_session.add_all([note1, note2])
    test_db_session.commit()

    token2 = create_access_token({"sub": user2.username}, timedelta(minutes=30))
    headers2 = {"Authorization": f"Bearer {token2}"}

    response = client.get("/api/notes/", headers=headers2)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "tag-user-2-note"
    assert data[0]["tags"] == ["shared-name"]
    assert "private" not in data[0]["tags"]
