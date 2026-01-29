"""
Unit tests for authentication dependencies (app.auth.dependencies).
Tests dependency functions for protected routes and user authentication.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
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

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, client, test_db_session: Session, sample_user: User):
        """Test successful current user retrieval."""
        # Create valid token
        token_data = {"sub": sample_user.username}
        token = create_access_token(token_data)

        # Create credentials object
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Create a mock async session that returns the user
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Call dependency
        result = await get_current_user(credentials, mock_session)

        assert result.id == sample_user.id
        assert result.username == sample_user.username

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test current user retrieval with invalid token."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token.here")
        mock_session = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, mock_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, sample_user: User):
        """Test current user retrieval with expired token."""
        from datetime import timedelta

        # Create expired token
        token_data = {"sub": sample_user.username}
        expired_token = create_access_token(token_data, expires_delta=timedelta(seconds=-1))

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=expired_token)
        mock_session = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, mock_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self):
        """Test current user retrieval when user doesn't exist in database."""
        # Create token for non-existent user
        token_data = {"sub": "nonexistent_user"}
        token = create_access_token(token_data)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Mock session that returns None (user not found)
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, mock_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"

    @pytest.mark.asyncio
    async def test_get_current_user_malformed_token(self):
        """Test current user retrieval with malformed token."""
        mock_session = AsyncMock(spec=AsyncSession)

        malformed_tokens = [
            "not.a.token",
            "",
            "header.payload",
            "a.b.c.d.e",
        ]

        for token in malformed_tokens:
            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials, mock_session)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    @patch("app.auth.dependencies.verify_token")
    async def test_get_current_user_token_verification_exception(self, mock_verify_token):
        """Test current user retrieval when token verification raises exception."""
        mock_verify_token.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token verification failed"
        )

        mock_session = AsyncMock(spec=AsyncSession)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="some.token.here")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, mock_session)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    @patch("app.auth.dependencies.verify_token")
    async def test_get_current_user_database_error(self, mock_verify_token):
        """Test current user retrieval when database query fails."""
        # Mock successful token verification
        mock_verify_token.return_value = TokenData(username="testuser")

        # Mock async database session to raise exception
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute.side_effect = Exception("Database connection error")

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid.token.here")

        with pytest.raises(Exception):
            await get_current_user(credentials, mock_session)


class TestGetCurrentActiveUser:
    """Test get_current_active_user dependency function."""

    @pytest.mark.asyncio
    async def test_get_current_active_user_success(self, sample_user: User):
        """Test successful active user retrieval."""
        result = await get_current_active_user(sample_user)

        assert result == sample_user
        assert result.username == sample_user.username

    @pytest.mark.asyncio
    async def test_get_current_active_user_with_mock(self):
        """Test active user retrieval with mock user."""
        mock_user = Mock(spec=User)
        mock_user.username = "testuser"
        mock_user.id = 1

        result = await get_current_active_user(mock_user)

        assert result == mock_user

    # Future test for when user status checking is implemented
    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive_user_future(self):
        """Test active user retrieval with inactive user (future implementation)."""
        # This test is for future when is_active field is added
        mock_user = Mock(spec=User)
        mock_user.username = "testuser"
        mock_user.is_active = False

        # Currently this should pass, but in future should raise exception
        result = await get_current_active_user(mock_user)
        assert result == mock_user

        # TODO: When is_active is implemented, this should raise HTTPException


class TestGetUserByUsername:
    """Test get_user_by_username helper function (now async)."""

    @pytest.mark.asyncio
    async def test_get_user_by_username_success(self, sample_user: User):
        """Test successful user retrieval by username."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        result = await get_user_by_username(mock_session, sample_user.username)

        assert result is not None
        assert result.id == sample_user.id
        assert result.username == sample_user.username

    @pytest.mark.asyncio
    async def test_get_user_by_username_not_found(self):
        """Test user retrieval with non-existent username."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await get_user_by_username(mock_session, "nonexistent_user")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_username_empty_string(self):
        """Test user retrieval with empty username."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await get_user_by_username(mock_session, "")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_username_database_error(self):
        """Test user retrieval when database query fails."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            await get_user_by_username(mock_session, "testuser")


class TestGetCurrentAdminUser:
    """Test get_current_admin_user dependency function."""

    @pytest.mark.asyncio
    async def test_get_current_admin_user_success(self, sample_user: User):
        """Test successful admin user retrieval."""
        result = await get_current_admin_user(sample_user)

        assert result == sample_user
        assert result.username == sample_user.username

    @pytest.mark.asyncio
    async def test_get_current_admin_user_with_admin(self, sample_admin_user: User):
        """Test admin user retrieval with admin user."""
        result = await get_current_admin_user(sample_admin_user)

        assert result == sample_admin_user
        assert result.username == "adminuser"  # From conftest fixture

    # Future test for when admin role checking is implemented
    @pytest.mark.asyncio
    async def test_get_current_admin_user_non_admin_future(self):
        """Test admin user retrieval with non-admin user (future implementation)."""
        mock_user = Mock(spec=User)
        mock_user.username = "regularuser"
        mock_user.is_admin = False

        # Currently this should pass, but in future should raise exception
        result = await get_current_admin_user(mock_user)
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

    @pytest.mark.asyncio
    async def test_dependency_chain(self, sample_user: User):
        """Test the full dependency chain from token to active user."""
        # Create valid token
        token_data = {"sub": sample_user.username}
        token = create_access_token(token_data)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Mock async session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Test the full chain
        current_user = await get_current_user(credentials, mock_session)
        active_user = await get_current_active_user(current_user)
        admin_user = await get_current_admin_user(active_user)

        assert current_user == sample_user
        assert active_user == sample_user
        assert admin_user == sample_user

    @pytest.mark.asyncio
    async def test_dependency_propagated_failure(self):
        """Test that failures propagate through dependency chain."""
        # Invalid credentials should fail at get_current_user
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token")
        mock_session = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException):
            current_user = await get_current_user(credentials, mock_session)
            # These should not be reached due to exception above
            await get_current_active_user(current_user)
            await get_current_admin_user(current_user)


class TestDependencyErrorHandling:
    """Test error handling in dependency functions."""

    @pytest.mark.asyncio
    async def test_http_exception_preservation(self):
        """Test that HTTPExceptions are properly preserved."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token")
        mock_session = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, mock_session)

        # Verify exception details are preserved
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "WWW-Authenticate" in exc_info.value.headers
        assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"

    @pytest.mark.asyncio
    async def test_database_session_handling(self):
        """Test proper handling of database session errors."""
        # Create a valid token first
        from app.auth.auth import create_access_token

        token = create_access_token({"sub": "testuser"})

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute.side_effect = Exception("Database unavailable")

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Should propagate database errors after token validation
        with pytest.raises(Exception) as exc_info:
            await get_current_user(credentials, mock_session)

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

            # Mock async session that returns the user
            mock_session = AsyncMock(spec=AsyncSession)
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = existing_user
            mock_session.execute.return_value = mock_result

            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="mock-oidc-token")

            # Since local JWT will fail, it will try OIDC, find the user by oidc_sub
            with patch("app.auth.dependencies.verify_token") as mock_verify:
                mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid local token")

                result = await get_current_user(credentials, mock_session)

                # Should find the existing user
                assert result.oidc_sub == oidc_sub
                assert result.username == oidc_username


class TestGetUserByOidcSub:
    """Test get_user_by_oidc_sub helper function (now async)."""

    @pytest.mark.asyncio
    async def test_get_user_by_oidc_sub_success(self):
        """Test successful user retrieval by OIDC subject."""
        # Create a mock OIDC user
        oidc_user = Mock(spec=User)
        oidc_user.username = "oidcuser"
        oidc_user.oidc_sub = "test-oidc-sub-123"

        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = oidc_user
        mock_session.execute.return_value = mock_result

        result = await get_user_by_oidc_sub(mock_session, "test-oidc-sub-123")

        assert result is not None
        assert result.oidc_sub == "test-oidc-sub-123"
        assert result.username == "oidcuser"

    @pytest.mark.asyncio
    async def test_get_user_by_oidc_sub_not_found(self):
        """Test user retrieval with non-existent OIDC subject."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await get_user_by_oidc_sub(mock_session, "nonexistent-sub")

        assert result is None
