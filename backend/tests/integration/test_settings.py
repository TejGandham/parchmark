"""
Integration tests for settings endpoints.
Tests user info, password change, note export, and account deletion.
"""

import io
import json
import zipfile

from fastapi import status

from app.auth.auth import verify_password


def test_get_user_info(client, sample_user, sample_user_data, auth_headers, multiple_notes):
    """Test getting user information with statistics."""
    response = client.get("/api/settings/user-info", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Check user info fields
    assert data["username"] == sample_user_data["username"]
    assert "created_at" in data
    assert data["notes_count"] == len(multiple_notes)


def test_get_user_info_unauthorized(client):
    """Test that user info endpoint requires authentication."""
    response = client.get("/api/settings/user-info")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_change_password_success(client, sample_user, sample_user_data, auth_headers, test_db_session):
    """Test changing password with correct current password."""
    new_password = "newSecurePassword123"

    response = client.post(
        "/api/settings/change-password",
        headers=auth_headers,
        json={"current_password": sample_user_data["password"], "new_password": new_password},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Password changed successfully"

    # Verify password was actually changed in database
    test_db_session.refresh(sample_user)
    assert verify_password(new_password, sample_user.password_hash)
    assert not verify_password(sample_user_data["password"], sample_user.password_hash)


def test_change_password_wrong_current_password(client, auth_headers):
    """Test that changing password fails with incorrect current password."""
    response = client.post(
        "/api/settings/change-password",
        headers=auth_headers,
        json={"current_password": "wrongpassword", "new_password": "newSecurePassword123"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Current password is incorrect"


def test_change_password_same_as_current(client, sample_user_data, auth_headers):
    """Test that new password must be different from current password."""
    response = client.post(
        "/api/settings/change-password",
        headers=auth_headers,
        json={"current_password": sample_user_data["password"], "new_password": sample_user_data["password"]},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "New password must be different from current password"


def test_change_password_unauthorized(client):
    """Test that password change requires authentication."""
    response = client.post(
        "/api/settings/change-password", json={"current_password": "anypass", "new_password": "newpass"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_export_notes_success(client, auth_headers, multiple_notes):
    """Test exporting notes as ZIP file."""
    response = client.get("/api/settings/export-notes", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/zip"
    assert "attachment" in response.headers["content-disposition"]
    assert "parchmark_notes_" in response.headers["content-disposition"]

    # Verify ZIP file contents
    zip_content = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_content, "r") as zip_file:
        file_list = zip_file.namelist()

        # Should have markdown files for each note plus metadata
        assert len(file_list) == len(multiple_notes) + 1  # notes + metadata.json
        assert "notes_metadata.json" in file_list

        # Verify metadata JSON
        metadata_content = zip_file.read("notes_metadata.json")
        metadata = json.loads(metadata_content)
        assert len(metadata) == len(multiple_notes)

        # Check metadata structure
        for note_data in metadata:
            assert "id" in note_data
            assert "title" in note_data
            assert "content" in note_data
            assert "createdAt" in note_data
            assert "updatedAt" in note_data


def test_export_notes_empty(client, auth_headers):
    """Test exporting notes when user has no notes."""
    response = client.get("/api/settings/export-notes", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK

    # Verify ZIP file has only metadata
    zip_content = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_content, "r") as zip_file:
        file_list = zip_file.namelist()
        assert len(file_list) == 1
        assert "notes_metadata.json" in file_list

        # Verify empty metadata
        metadata_content = zip_file.read("notes_metadata.json")
        metadata = json.loads(metadata_content)
        assert len(metadata) == 0


def test_export_notes_unauthorized(client):
    """Test that note export requires authentication."""
    response = client.get("/api/settings/export-notes")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_account_success(client, sample_user, sample_user_data, auth_headers, test_db_session):
    """Test deleting account with correct password."""
    from app.models.models import User

    # Verify user exists before deletion
    user_before = test_db_session.query(User).filter(User.id == sample_user.id).first()
    assert user_before is not None

    response = client.delete(
        "/api/settings/delete-account", headers=auth_headers, json={"password": sample_user_data["password"]}
    )

    assert response.status_code == status.HTTP_200_OK
    assert sample_user_data["username"] in response.json()["message"]
    assert "deleted successfully" in response.json()["message"]

    # Verify user was actually deleted from database
    user_after = test_db_session.query(User).filter(User.id == sample_user.id).first()
    assert user_after is None


def test_delete_account_wrong_password(client, auth_headers):
    """Test that account deletion fails with incorrect password."""
    response = client.delete("/api/settings/delete-account", headers=auth_headers, json={"password": "wrongpassword"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Password is incorrect"


def test_delete_account_unauthorized(client):
    """Test that account deletion requires authentication."""
    response = client.delete("/api/settings/delete-account", json={"password": "anypass"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_account_cascades_notes(
    client, sample_user, sample_user_data, auth_headers, multiple_notes, test_db_session
):
    """Test that deleting account also deletes all user's notes."""
    from app.models.models import Note

    # Verify notes exist before deletion
    notes_before = test_db_session.query(Note).filter(Note.user_id == sample_user.id).all()
    assert len(notes_before) == len(multiple_notes)

    # Delete account
    response = client.delete(
        "/api/settings/delete-account", headers=auth_headers, json={"password": sample_user_data["password"]}
    )

    assert response.status_code == status.HTTP_200_OK

    # Verify notes were cascade deleted
    notes_after = test_db_session.query(Note).filter(Note.user_id == sample_user.id).all()
    assert len(notes_after) == 0


def test_password_validation_min_length(client, auth_headers):
    """Test that password validation requires minimum length."""
    response = client.post(
        "/api/settings/change-password", headers=auth_headers, json={"current_password": "test", "new_password": "abc"}
    )

    # Should fail validation (422 Unprocessable Entity)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
