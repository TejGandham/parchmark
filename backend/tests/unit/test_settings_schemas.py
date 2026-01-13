"""
Unit tests for settings-related Pydantic schemas.
Tests validation for PasswordChangeRequest, AccountDeleteRequest, and UserInfoResponse.
"""

import pytest
from pydantic import ValidationError

from app.schemas.schemas import AccountDeleteRequest, PasswordChangeRequest, UserInfoResponse


class TestPasswordChangeRequest:
    """Tests for PasswordChangeRequest schema."""

    def test_valid_password_change_request(self):
        """Test creating valid password change request."""
        data = {"current_password": "oldpass123", "new_password": "newpass456"}
        request = PasswordChangeRequest(**data)

        assert request.current_password == "oldpass123"
        assert request.new_password == "newpass456"

    def test_password_minimum_length_validation(self):
        """Test that passwords must meet minimum length requirement."""
        # Current password too short
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(current_password="abc", new_password="validpass123")

        assert "at least 4 characters" in str(exc_info.value)

        # New password too short
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(current_password="validpass123", new_password="abc")

        assert "at least 4 characters" in str(exc_info.value)

    def test_missing_required_fields(self):
        """Test that all required fields must be provided."""
        # Missing current_password
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(new_password="newpass123")

        assert "current_password" in str(exc_info.value)

        # Missing new_password
        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(current_password="oldpass123")

        assert "new_password" in str(exc_info.value)

    def test_empty_passwords_rejected(self):
        """Test that empty passwords are rejected."""
        with pytest.raises(ValidationError):
            PasswordChangeRequest(current_password="", new_password="newpass123")

        with pytest.raises(ValidationError):
            PasswordChangeRequest(current_password="oldpass123", new_password="")


class TestAccountDeleteRequest:
    """Tests for AccountDeleteRequest schema."""

    def test_valid_account_delete_request(self):
        """Test creating valid account delete request."""
        data = {"password": "mypassword123"}
        request = AccountDeleteRequest(**data)

        assert request.password == "mypassword123"

    def test_password_minimum_length_validation(self):
        """Test that password must meet minimum length requirement."""
        with pytest.raises(ValidationError) as exc_info:
            AccountDeleteRequest(password="abc")

        assert "at least 4 characters" in str(exc_info.value)

    def test_missing_password_field(self):
        """Test that password field is required."""
        with pytest.raises(ValidationError) as exc_info:
            AccountDeleteRequest()

        assert "password" in str(exc_info.value)

    def test_empty_password_rejected(self):
        """Test that empty password is rejected."""
        with pytest.raises(ValidationError):
            AccountDeleteRequest(password="")


class TestUserInfoResponse:
    """Tests for UserInfoResponse schema."""

    def test_valid_user_info_response(self):
        """Test creating valid user info response."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "created_at": "2025-01-01T00:00:00Z",
            "notes_count": 5,
            "auth_provider": "local",
        }
        response = UserInfoResponse(**data)

        assert response.username == "testuser"
        assert response.email == "test@example.com"
        assert response.created_at == "2025-01-01T00:00:00Z"
        assert response.notes_count == 5
        assert response.auth_provider == "local"

    def test_user_info_response_without_email(self):
        """Test creating user info response without email (local user)."""
        data = {
            "username": "localuser",
            "created_at": "2025-01-01T00:00:00Z",
            "notes_count": 10,
            "auth_provider": "local",
        }
        response = UserInfoResponse(**data)

        assert response.username == "localuser"
        assert response.email is None
        assert response.auth_provider == "local"

    def test_user_info_response_oidc_user(self):
        """Test creating user info response for OIDC user."""
        data = {
            "username": "oidcuser",
            "email": "oidc@provider.com",
            "created_at": "2025-01-01T00:00:00Z",
            "notes_count": 3,
            "auth_provider": "oidc",
        }
        response = UserInfoResponse(**data)

        assert response.username == "oidcuser"
        assert response.email == "oidc@provider.com"
        assert response.auth_provider == "oidc"

    def test_notes_count_validation(self):
        """Test that notes_count must be provided."""
        with pytest.raises(ValidationError) as exc_info:
            UserInfoResponse(
                username="testuser",
                created_at="2025-01-01T00:00:00Z",
                auth_provider="local",
            )

        assert "notes_count" in str(exc_info.value)

    def test_missing_required_fields(self):
        """Test that all required fields must be provided."""
        # Missing username
        with pytest.raises(ValidationError) as exc_info:
            UserInfoResponse(
                created_at="2025-01-01T00:00:00Z",
                notes_count=5,
                auth_provider="local",
            )

        assert "username" in str(exc_info.value)

        # Missing created_at
        with pytest.raises(ValidationError) as exc_info:
            UserInfoResponse(
                username="testuser",
                notes_count=5,
                auth_provider="local",
            )

        assert "created_at" in str(exc_info.value)

        # Missing auth_provider
        with pytest.raises(ValidationError) as exc_info:
            UserInfoResponse(
                username="testuser",
                created_at="2025-01-01T00:00:00Z",
                notes_count=5,
            )

        assert "auth_provider" in str(exc_info.value)

    def test_notes_count_must_be_integer(self):
        """Test that notes_count must be an integer."""
        # String should be coerced to int if valid
        response = UserInfoResponse(
            username="testuser",
            created_at="2025-01-01T00:00:00Z",
            notes_count="5",
            auth_provider="local",
        )
        assert response.notes_count == 5

        # Invalid string should fail
        with pytest.raises(ValidationError):
            UserInfoResponse(
                username="testuser",
                created_at="2025-01-01T00:00:00Z",
                notes_count="invalid",
                auth_provider="local",
            )

    def test_model_config_from_attributes(self):
        """Test that model can be created from ORM objects."""

        # This tests the from_attributes=True config
        class MockUser:
            """Mock ORM user object."""

            username = "testuser"
            email = "test@example.com"
            created_at = "2025-01-01T00:00:00Z"
            notes_count = 10
            auth_provider = "local"

        # Should be able to create from object attributes
        response = UserInfoResponse.model_validate(MockUser())
        assert response.username == "testuser"
        assert response.email == "test@example.com"
        assert response.created_at == "2025-01-01T00:00:00Z"
        assert response.notes_count == 10
        assert response.auth_provider == "local"
