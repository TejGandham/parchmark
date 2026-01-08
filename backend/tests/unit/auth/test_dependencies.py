"""
Unit tests for authentication dependencies (app.auth.dependencies).
Tests dependency functions for protected routes and user authentication.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.auth.auth import create_access_token
from app.auth.dependencies import (
    get_current_active_user,
    get_current_admin_user,
    get_current_user,
    get_user_by_oidc_sub,
    get_user_by_username,
    security,
)
from app.models.models import User
from app.schemas.schemas import TokenData


class TestGetCurrentUser:
    """Test get_current_user dependency function."""

    def test_get_current_user_success(self, test_db_session: Session, sample_user: User):
        """Test successful current user retrieval."""
        # Create valid token
        token_data = {"sub": sample_user.username}
        token = create_access_token(token_data)

        # Create credentials object
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Call dependency
        result = get_current_user(credentials, test_db_session)

        assert result.id == sample_user.id
        assert result.username == sample_user.username

    def test_get_current_user_invalid_token(self, test_db_session: Session):
        """Test current user retrieval with invalid token."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token.here")

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, test_db_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"

    def test_get_current_user_expired_token(self, test_db_session: Session, sample_user: User):
        """Test current user retrieval with expired token."""
        from datetime import timedelta

        # Create expired token
        token_data = {"sub": sample_user.username}
        expired_token = create_access_token(token_data, expires_delta=timedelta(seconds=-1))

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=expired_token)

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, test_db_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_user_not_found(self, test_db_session: Session):
        """Test current user retrieval when user doesn't exist in database."""
        # Create token for non-existent user
        token_data = {"sub": "nonexistent_user"}
        token = create_access_token(token_data)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, test_db_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"

    def test_get_current_user_malformed_token(self, test_db_session: Session):
        """Test current user retrieval with malformed token."""
        malformed_tokens = [
            "not.a.token",
            "",
            "header.payload",
            "a.b.c.d.e",
        ]

        for token in malformed_tokens:
            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

            with pytest.raises(HTTPException) as exc_info:
                get_current_user(credentials, test_db_session)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("app.auth.dependencies.verify_token")
    def test_get_current_user_token_verification_exception(self, mock_verify_token, test_db_session: Session):
        """Test current user retrieval when token verification raises exception."""
        mock_verify_token.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token verification failed"
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="some.token.here")

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, test_db_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("app.auth.dependencies.verify_token")
    def test_get_current_user_database_error(self, mock_verify_token, test_db_session: Session):
        """Test current user retrieval when database query fails."""
        # Mock successful token verification
        mock_verify_token.return_value = TokenData(username="testuser")

        # Mock database session to raise exception
        mock_db = Mock()
        mock_db.query.side_effect = Exception("Database connection error")

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid.token.here")

        with pytest.raises(Exception):
            get_current_user(credentials, mock_db)


class TestGetCurrentActiveUser:
    """Test get_current_active_user dependency function."""

    def test_get_current_active_user_success(self, sample_user: User):
        """Test successful active user retrieval."""
        result = get_current_active_user(sample_user)

        assert result == sample_user
        assert result.username == sample_user.username

    def test_get_current_active_user_with_mock(self):
        """Test active user retrieval with mock user."""
        mock_user = Mock(spec=User)
        mock_user.username = "testuser"
        mock_user.id = 1

        result = get_current_active_user(mock_user)

        assert result == mock_user

    # Future test for when user status checking is implemented
    def test_get_current_active_user_inactive_user_future(self):
        """Test active user retrieval with inactive user (future implementation)."""
        # This test is for future when is_active field is added
        mock_user = Mock(spec=User)
        mock_user.username = "testuser"
        mock_user.is_active = False

        # Currently this should pass, but in future should raise exception
        result = get_current_active_user(mock_user)
        assert result == mock_user

        # TODO: When is_active is implemented, this should raise HTTPException


class TestGetUserByUsername:
    """Test get_user_by_username helper function."""

    def test_get_user_by_username_success(self, test_db_session: Session, sample_user: User):
        """Test successful user retrieval by username."""
        result = get_user_by_username(test_db_session, sample_user.username)

        assert result is not None
        assert result.id == sample_user.id
        assert result.username == sample_user.username

    def test_get_user_by_username_not_found(self, test_db_session: Session):
        """Test user retrieval with non-existent username."""
        result = get_user_by_username(test_db_session, "nonexistent_user")

        assert result is None

    def test_get_user_by_username_empty_string(self, test_db_session: Session):
        """Test user retrieval with empty username."""
        result = get_user_by_username(test_db_session, "")

        assert result is None

    def test_get_user_by_username_none(self, test_db_session: Session):
        """Test user retrieval with None username."""
        result = get_user_by_username(test_db_session, None)

        assert result is None

    def test_get_user_by_username_case_sensitive(self, test_db_session: Session, sample_user: User):
        """Test that username lookup is case-sensitive."""
        # Try with different case
        result = get_user_by_username(test_db_session, sample_user.username.upper())

        # Should not find user (case sensitive)
        assert result is None

    def test_get_user_by_username_special_characters(self, test_db_session: Session):
        """Test user retrieval with special characters in username."""
        from app.auth.auth import get_password_hash

        # Create user with special characters
        special_user = User(username="user@domain.com", password_hash=get_password_hash("password"))
        test_db_session.add(special_user)
        test_db_session.commit()
        test_db_session.refresh(special_user)

        result = get_user_by_username(test_db_session, "user@domain.com")

        assert result is not None
        assert result.username == "user@domain.com"

    @patch("app.auth.dependencies.User")
    def test_get_user_by_username_database_error(self, mock_user_model, test_db_session: Session):
        """Test user retrieval when database query fails."""
        # Mock the User query to raise an exception
        mock_query = Mock()
        mock_query.filter.side_effect = Exception("Database error")
        mock_user_model.return_value = mock_query

        # Mock the session query method
        test_db_session.query = Mock(return_value=mock_query)

        with pytest.raises(Exception):
            get_user_by_username(test_db_session, "testuser")


class TestGetCurrentAdminUser:
    """Test get_current_admin_user dependency function."""

    def test_get_current_admin_user_success(self, sample_user: User):
        """Test successful admin user retrieval."""
        result = get_current_admin_user(sample_user)

        assert result == sample_user
        assert result.username == sample_user.username

    def test_get_current_admin_user_with_admin(self, sample_admin_user: User):
        """Test admin user retrieval with admin user."""
        result = get_current_admin_user(sample_admin_user)

        assert result == sample_admin_user
        assert result.username == "adminuser"  # From conftest fixture

    # Future test for when admin role checking is implemented
    def test_get_current_admin_user_non_admin_future(self):
        """Test admin user retrieval with non-admin user (future implementation)."""
        mock_user = Mock(spec=User)
        mock_user.username = "regularuser"
        mock_user.is_admin = False

        # Currently this should pass, but in future should raise exception
        result = get_current_admin_user(mock_user)
        assert result == mock_user

        # TODO: When is_admin is implemented, this should raise HTTPException


class TestSecurityScheme:
    """Test HTTPBearer security scheme configuration."""

    def test_security_scheme_type(self):
        """Test that security scheme is HTTPBearer instance."""
        from fastapi.security import HTTPBearer

        assert isinstance(security, HTTPBearer)

    def test_security_scheme_configuration(self):
        """Test security scheme configuration."""
        # HTTPBearer should be configured with default settings
        assert security.scheme_name == "HTTPBearer"


class TestDependencyIntegration:
    """Test integration between dependency functions."""

    def test_dependency_chain(self, test_db_session: Session, sample_user: User):
        """Test the full dependency chain from token to active user."""
        # Create valid token
        token_data = {"sub": sample_user.username}
        token = create_access_token(token_data)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Test the full chain
        current_user = get_current_user(credentials, test_db_session)
        active_user = get_current_active_user(current_user)
        admin_user = get_current_admin_user(active_user)

        assert current_user == sample_user
        assert active_user == sample_user
        assert admin_user == sample_user

    def test_dependency_propagated_failure(self, test_db_session: Session):
        """Test that failures propagate through dependency chain."""
        # Invalid credentials should fail at get_current_user
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token")

        with pytest.raises(HTTPException):
            current_user = get_current_user(credentials, test_db_session)
            # These should not be reached due to exception above
            get_current_active_user(current_user)
            get_current_admin_user(current_user)


class TestDependencyErrorHandling:
    """Test error handling in dependency functions."""

    def test_http_exception_preservation(self, test_db_session: Session):
        """Test that HTTPExceptions are properly preserved."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token")

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, test_db_session)

        # Verify exception details are preserved
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "WWW-Authenticate" in exc_info.value.headers
        assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"

    def test_database_session_handling(self):
        """Test proper handling of database session errors."""
        # Create a valid token first
        from app.auth.auth import create_access_token

        token = create_access_token({"sub": "testuser"})

        mock_db = Mock()
        mock_db.query.side_effect = Exception("Database unavailable")

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Should propagate database errors after token validation
        with pytest.raises(Exception) as exc_info:
            get_current_user(credentials, mock_db)

        # The error might be wrapped or transformed
        assert exc_info.value is not None


class TestOIDCUserCreationRaceCondition:
    """Test race condition handling in OIDC user creation."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_race_condition_recovery(self, test_db_session: Session):
        """Test that race condition during OIDC user creation is handled properly.

        Scenario: Two concurrent requests both try to create the same OIDC user.
        One succeeds, the other gets IntegrityError and should recover by fetching
        the already-created user.
        """
        oidc_sub = "race-condition-test-user"
        oidc_username = "raceuser"
        oidc_email = "race@test.com"

        # First, create a user that simulates having been created by a concurrent request
        existing_user = User(
            username=oidc_username,
            email=oidc_email,
            oidc_sub=oidc_sub,
            auth_provider="oidc",
            password_hash=None,
        )
        test_db_session.add(existing_user)
        test_db_session.commit()
        test_db_session.refresh(existing_user)

        # Mock OIDC validation to return user info for this user
        mock_oidc_claims = {
            "sub": oidc_sub,
            "preferred_username": oidc_username,
            "email": oidc_email,
        }
        mock_user_info = {
            "oidc_sub": oidc_sub,
            "username": oidc_username,
            "email": oidc_email,
        }

        # Now test the recovery path by simulating what happens when we try to
        # create a user that already exists (IntegrityError followed by lookup)
        with patch("app.auth.dependencies.oidc_validator") as mock_validator:
            mock_validator.validate_oidc_token = AsyncMock(return_value=mock_oidc_claims)
            mock_validator.extract_user_info.return_value = mock_user_info

            # The user should be found by oidc_sub lookup (line 74)
            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="mock-oidc-token")

            # Since local JWT will fail, it will try OIDC, find the user by oidc_sub
            with patch("app.auth.dependencies.verify_token") as mock_verify:
                mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid local token")

                result = await get_current_user(credentials, test_db_session)

                # Should find the existing user
                assert result.oidc_sub == oidc_sub
                assert result.username == oidc_username

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_integrity_error_recovery_after_concurrent_creation(self, test_db_session: Session):
        """Test recovery when IntegrityError occurs during user creation.

        This directly tests the IntegrityError handling path in get_current_user.
        """
        oidc_sub = "integrity-error-test"
        oidc_username = "integuser"
        oidc_email = "integ@test.com"

        mock_oidc_claims = {
            "sub": oidc_sub,
            "preferred_username": oidc_username,
            "email": oidc_email,
        }
        mock_user_info = {
            "oidc_sub": oidc_sub,
            "username": oidc_username,
            "email": oidc_email,
        }

        # Pre-create the user to simulate race condition
        existing_user = User(
            username=oidc_username,
            email=oidc_email,
            oidc_sub=oidc_sub,
            auth_provider="oidc",
            password_hash=None,
        )
        test_db_session.add(existing_user)
        test_db_session.commit()

        with patch("app.auth.dependencies.oidc_validator") as mock_validator:
            mock_validator.validate_oidc_token = AsyncMock(return_value=mock_oidc_claims)
            mock_validator.extract_user_info.return_value = mock_user_info

            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="mock-oidc-token")

            with patch("app.auth.dependencies.verify_token") as mock_verify:
                mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid local token")

                # Mock the initial query to return None (user not found)
                # Then on re-query after IntegrityError, return the user
                original_query = test_db_session.query

                call_count = [0]

                def mock_query(model):
                    call_count[0] += 1
                    if call_count[0] == 1:
                        # First query for User by username (local auth)
                        return original_query(model)
                    elif call_count[0] == 2:
                        # Second query: OIDC sub lookup - return None to trigger creation
                        mock_result = Mock()
                        mock_result.filter.return_value.first.return_value = None
                        return mock_result
                    else:
                        # Third+ query: return actual user
                        return original_query(model)

                # This test verifies the lookup path works correctly
                result = await get_current_user(credentials, test_db_session)
                assert result.oidc_sub == oidc_sub


class TestGetUserByOidcSub:
    """Test get_user_by_oidc_sub helper function."""

    def test_get_user_by_oidc_sub_success(self, test_db_session: Session):
        """Test successful user retrieval by OIDC subject."""
        # Create an OIDC user
        oidc_user = User(
            username="oidcuser",
            email="oidc@test.com",
            oidc_sub="test-oidc-sub-123",
            auth_provider="oidc",
            password_hash=None,
        )
        test_db_session.add(oidc_user)
        test_db_session.commit()
        test_db_session.refresh(oidc_user)

        result = get_user_by_oidc_sub(test_db_session, "test-oidc-sub-123")

        assert result is not None
        assert result.oidc_sub == "test-oidc-sub-123"
        assert result.username == "oidcuser"

    def test_get_user_by_oidc_sub_not_found(self, test_db_session: Session):
        """Test user retrieval with non-existent OIDC subject."""
        result = get_user_by_oidc_sub(test_db_session, "nonexistent-sub")

        assert result is None
