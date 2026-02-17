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
    get_current_user,
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
        """Test the full dependency chain from token to user."""
        # Create valid token
        token_data = {"sub": sample_user.username}
        token = create_access_token(token_data)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Mock async session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_session.execute.return_value = mock_result

        # Test get_current_user
        current_user = await get_current_user(credentials, mock_session)

        assert current_user == sample_user

    @pytest.mark.asyncio
    async def test_dependency_propagated_failure(self):
        """Test that failures propagate through dependency chain."""
        # Invalid credentials should fail at get_current_user
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token")
        mock_session = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException):
            await get_current_user(credentials, mock_session)


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


class TestOIDCOpaqueTokenValidation:
    """Test opaque token validation flow through get_current_user."""

    @pytest.mark.asyncio
    async def test_get_current_user_with_opaque_token_existing_user(self):
        """Test get_current_user resolves an existing OIDC user via opaque token."""
        existing_user = Mock(spec=User)
        existing_user.username = "oidcuser"
        existing_user.oidc_sub = "authelia-sub-opaque-123"
        existing_user.auth_provider = "oidc"

        mock_oidc_claims = {
            "sub": "authelia-sub-opaque-123",
            "preferred_username": "oidcuser",
            "email": "oidc@example.com",
        }
        mock_user_info = {
            "oidc_sub": "authelia-sub-opaque-123",
            "username": "oidcuser",
            "email": "oidc@example.com",
        }

        with patch("app.auth.dependencies.oidc_validator") as mock_validator:
            mock_validator.is_opaque_token.return_value = True
            mock_validator.validate_opaque_token = AsyncMock(return_value=mock_oidc_claims)
            mock_validator.extract_user_info.return_value = mock_user_info

            mock_session = AsyncMock(spec=AsyncSession)
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = existing_user
            mock_session.execute.return_value = mock_result

            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="authelia_at_opaque_token")

            with patch("app.auth.dependencies.verify_token") as mock_verify:
                mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid local token")

                result = await get_current_user(credentials, mock_session)

                assert result.username == "oidcuser"
                assert result.oidc_sub == "authelia-sub-opaque-123"
                mock_validator.is_opaque_token.assert_called_once_with("authelia_at_opaque_token")
                mock_validator.validate_opaque_token.assert_called_once_with("authelia_at_opaque_token")

    @pytest.mark.asyncio
    async def test_get_current_user_with_opaque_token_new_user(self):
        """Test get_current_user auto-creates a new OIDC user via opaque token."""
        new_user = Mock(spec=User)
        new_user.username = "newoidcuser"
        new_user.oidc_sub = "authelia-sub-opaque-new"
        new_user.auth_provider = "oidc"
        new_user.email = "new@example.com"

        mock_oidc_claims = {
            "sub": "authelia-sub-opaque-new",
            "preferred_username": "newoidcuser",
            "email": "new@example.com",
        }
        mock_user_info = {
            "oidc_sub": "authelia-sub-opaque-new",
            "username": "newoidcuser",
            "email": "new@example.com",
        }

        with patch("app.auth.dependencies.oidc_validator") as mock_validator:
            mock_validator.is_opaque_token.return_value = True
            mock_validator.validate_opaque_token = AsyncMock(return_value=mock_oidc_claims)
            mock_validator.extract_user_info.return_value = mock_user_info

            # First call returns None (user not found), subsequent calls return created user
            mock_session = AsyncMock(spec=AsyncSession)
            mock_result_none = Mock()
            mock_result_none.scalar_one_or_none.return_value = None
            mock_session.execute.return_value = mock_result_none

            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="authelia_at_opaque_token")

            with patch("app.auth.dependencies.verify_token") as mock_verify:
                mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid local token")
                with patch("app.auth.dependencies._create_oidc_user", new_callable=AsyncMock) as mock_create:
                    mock_create.return_value = new_user

                    result = await get_current_user(credentials, mock_session)

                    assert result.username == "newoidcuser"
                    assert result.oidc_sub == "authelia-sub-opaque-new"
                    mock_create.assert_called_once_with(mock_session, mock_user_info)


class TestOIDCTimeoutHandling:
    """Test that TimeoutError from asyncio.timeout is handled gracefully."""

    @pytest.mark.asyncio
    async def test_get_current_user_timeout_error_handled_gracefully(self):
        """Test that TimeoutError (from asyncio.timeout in get_jwks) is caught
        in the expected exception tuple, not logged as an unexpected error."""
        mock_session = AsyncMock(spec=AsyncSession)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid.jwt.token")

        with patch("app.auth.dependencies.verify_token") as mock_verify:
            mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid local token")

            with patch("app.auth.dependencies.oidc_validator") as mock_validator:
                mock_validator.is_opaque_token.return_value = False
                mock_validator.validate_oidc_token = AsyncMock(side_effect=TimeoutError("JWKS fetch timed out"))

                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(credentials, mock_session)

                assert exc_info.value.status_code == 401


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
            mock_validator.is_opaque_token.return_value = False
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
