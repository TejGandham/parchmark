"""
Integration tests for settings endpoints.
Tests user info, password change, note export, and account deletion.
Includes tests for both local and OIDC authentication users.
"""

import io
import json
import zipfile
from datetime import timedelta

import pytest
from fastapi import status

from app.auth.auth import create_access_token, verify_password
from app.models.models import Note, User


class TestGetUserInfo:
    """Tests for GET /api/settings/user-info endpoint."""

    def test_get_user_info_success(self, client, sample_user, sample_user_data, auth_headers, multiple_notes):
        """Test getting user information with statistics."""
        response = client.get("/api/settings/user-info", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check user info fields
        assert data["username"] == sample_user_data["username"]
        assert "created_at" in data
        assert data["notes_count"] == len(multiple_notes)
        assert data["auth_provider"] == "local"
        assert data["email"] is None  # Local users don't have email by default

    def test_get_user_info_no_notes(self, client, sample_user, sample_user_data, auth_headers):
        """Test getting user info when user has no notes."""
        response = client.get("/api/settings/user-info", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["notes_count"] == 0

    def test_get_user_info_unauthorized(self, client):
        """Test that user info endpoint requires authentication."""
        response = client.get("/api/settings/user-info")

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestChangePassword:
    """Tests for POST /api/settings/change-password endpoint."""

    def test_change_password_success(self, client, sample_user, sample_user_data, auth_headers, test_db_session):
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

    def test_change_password_wrong_current_password(self, client, auth_headers):
        """Test that changing password fails with incorrect current password."""
        response = client.post(
            "/api/settings/change-password",
            headers=auth_headers,
            json={"current_password": "wrongpassword", "new_password": "newSecurePassword123"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Current password is incorrect"

    def test_change_password_same_as_current(self, client, sample_user_data, auth_headers):
        """Test that new password must be different from current password."""
        response = client.post(
            "/api/settings/change-password",
            headers=auth_headers,
            json={"current_password": sample_user_data["password"], "new_password": sample_user_data["password"]},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "New password must be different from current password"

    def test_change_password_unauthorized(self, client):
        """Test that password change requires authentication."""
        response = client.post(
            "/api/settings/change-password", json={"current_password": "anypass", "new_password": "newpass"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_password_validation_min_length(self, client, auth_headers):
        """Test that password validation requires minimum length."""
        response = client.post(
            "/api/settings/change-password",
            headers=auth_headers,
            json={"current_password": "test", "new_password": "abc"},
        )

        # Should fail validation (422 Unprocessable Entity)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestChangePasswordOIDC:
    """Tests for password change with OIDC users."""

    @pytest.fixture
    def oidc_user(self, test_db_session):
        """Create an OIDC user without password hash."""
        user = User(
            username="oidc_user",
            password_hash=None,
            email="oidc@example.com",
            oidc_sub="oidc|123456789",
            auth_provider="oidc",
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        return user

    @pytest.fixture
    def oidc_auth_headers(self, oidc_user):
        """Generate auth headers for OIDC user."""
        token = create_access_token(data={"sub": oidc_user.username}, expires_delta=timedelta(minutes=30))
        return {"Authorization": f"Bearer {token}"}

    def test_change_password_fails_for_oidc_user(self, client, oidc_user, oidc_auth_headers):
        """Test that OIDC users cannot change password."""
        response = client.post(
            "/api/settings/change-password",
            headers=oidc_auth_headers,
            json={"current_password": "test", "new_password": "newpass123"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "OIDC" in response.json()["detail"]
        assert "identity provider" in response.json()["detail"]


class TestExportNotes:
    """Tests for GET /api/settings/export-notes endpoint."""

    def test_export_notes_success(self, client, auth_headers, multiple_notes):
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

    def test_export_notes_empty(self, client, auth_headers):
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

    def test_export_notes_unauthorized(self, client):
        """Test that note export requires authentication."""
        response = client.get("/api/settings/export-notes")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_export_notes_handles_duplicate_titles(self, client, auth_headers, sample_user, test_db_session):
        """Test that export handles notes with duplicate titles."""
        # Create notes with same title
        for i in range(3):
            note = Note(
                id=f"dup-note-{i}",
                user_id=sample_user.id,
                title="Same Title",
                content=f"# Same Title\n\nContent {i}",
            )
            test_db_session.add(note)
        test_db_session.commit()

        response = client.get("/api/settings/export-notes", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        # Verify all files have unique names
        zip_content = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_content, "r") as zip_file:
            file_list = [f for f in zip_file.namelist() if f.endswith(".md")]
            # All filenames should be unique
            assert len(file_list) == len(set(file_list))


class TestDeleteAccount:
    """Tests for DELETE /api/settings/delete-account endpoint."""

    def test_delete_account_success(self, client, sample_user, sample_user_data, auth_headers, test_db_session):
        """Test deleting account with correct password."""
        # Verify user exists before deletion
        user_before = test_db_session.query(User).filter(User.id == sample_user.id).first()
        assert user_before is not None

        response = client.request(
            "DELETE",
            "/api/settings/delete-account",
            headers=auth_headers,
            json={"password": sample_user_data["password"]},
        )

        assert response.status_code == status.HTTP_200_OK
        assert sample_user_data["username"] in response.json()["message"]
        assert "deleted successfully" in response.json()["message"]

        # Verify user was actually deleted from database
        user_after = test_db_session.query(User).filter(User.id == sample_user.id).first()
        assert user_after is None

    def test_delete_account_wrong_password(self, client, auth_headers):
        """Test that account deletion fails with incorrect password."""
        response = client.request(
            "DELETE", "/api/settings/delete-account", headers=auth_headers, json={"password": "wrongpassword"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Password is incorrect"

    def test_delete_account_unauthorized(self, client):
        """Test that account deletion requires authentication."""
        response = client.request("DELETE", "/api/settings/delete-account", json={"password": "anypass"})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_account_cascades_notes(
        self, client, sample_user, sample_user_data, auth_headers, multiple_notes, test_db_session
    ):
        """Test that deleting account also deletes all user's notes."""
        # Verify notes exist before deletion
        notes_before = test_db_session.query(Note).filter(Note.user_id == sample_user.id).all()
        assert len(notes_before) == len(multiple_notes)

        # Delete account
        response = client.request(
            "DELETE",
            "/api/settings/delete-account",
            headers=auth_headers,
            json={"password": sample_user_data["password"]},
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify notes were cascade deleted
        notes_after = test_db_session.query(Note).filter(Note.user_id == sample_user.id).all()
        assert len(notes_after) == 0


class TestDeleteAccountOIDC:
    """Tests for account deletion with OIDC users."""

    @pytest.fixture
    def oidc_user(self, test_db_session):
        """Create an OIDC user without password hash."""
        user = User(
            username="oidc_delete_user",
            password_hash=None,
            email="oidc_delete@example.com",
            oidc_sub="oidc|delete123456",
            auth_provider="oidc",
        )
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        return user

    @pytest.fixture
    def oidc_auth_headers(self, oidc_user):
        """Generate auth headers for OIDC user."""
        token = create_access_token(data={"sub": oidc_user.username}, expires_delta=timedelta(minutes=30))
        return {"Authorization": f"Bearer {token}"}

    def test_delete_oidc_account_success(self, client, oidc_user, oidc_auth_headers, test_db_session):
        """Test that OIDC users can delete their account with confirmation."""
        user_id = oidc_user.id

        # For OIDC users without password, any password acts as confirmation
        response = client.request(
            "DELETE",
            "/api/settings/delete-account",
            headers=oidc_auth_headers,
            json={"password": "DELETE"},  # Confirmation word
        )

        assert response.status_code == status.HTTP_200_OK
        assert "deleted successfully" in response.json()["message"]

        # Verify user was deleted
        user_after = test_db_session.query(User).filter(User.id == user_id).first()
        assert user_after is None
