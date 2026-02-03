"""Unit tests for the auth service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.models import User
from app.services.auth_service import (
    AuthenticationError,
    AuthService,
    InvalidRefreshTokenError,
    LoginInput,
    TokenResult,
)


class TestAuthServiceGetUserByUsername:
    """Tests for AuthService.get_user_by_username."""

    @pytest.mark.asyncio
    async def test_get_user_by_username_found(self):
        """Should return user when found."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_user = MagicMock(spec=User)
        mock_user.username = "testuser"
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.auth_service.get_db", return_value=mock_db):
            service = AuthService()
            result = await service.get_user_by_username("testuser")

        assert result == mock_user
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_username_not_found(self):
        """Should return None when user not found."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.auth_service.get_db", return_value=mock_db):
            service = AuthService()
            result = await service.get_user_by_username("nonexistent")

        assert result is None


class TestAuthServiceLogin:
    """Tests for AuthService.login."""

    @pytest.mark.asyncio
    async def test_login_success(self):
        """Should return tokens on successful authentication."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_user = MagicMock(spec=User)
        mock_user.username = "testuser"
        mock_user.password_hash = "hashed_password"
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.auth_service.get_db", return_value=mock_db):
            service = AuthService()
            input_data = LoginInput(username="testuser", password="password123")

            with patch("app.services.auth_service.verify_user_password", return_value=mock_user):
                result = await service.login(input_data)

        assert isinstance(result, TokenResult)
        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_login_user_not_found(self):
        """Should raise AuthenticationError when user doesn't exist."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.auth_service.get_db", return_value=mock_db):
            service = AuthService()
            input_data = LoginInput(username="nonexistent", password="password123")

            with patch("app.services.auth_service.verify_user_password", return_value=None):
                with pytest.raises(AuthenticationError):
                    await service.login(input_data)

    @pytest.mark.asyncio
    async def test_login_invalid_password(self):
        """Should raise AuthenticationError when password is wrong."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_user = MagicMock(spec=User)
        mock_user.username = "testuser"
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.auth_service.get_db", return_value=mock_db):
            service = AuthService()
            input_data = LoginInput(username="testuser", password="wrongpassword")

            with patch("app.services.auth_service.verify_user_password", return_value=None):
                with pytest.raises(AuthenticationError):
                    await service.login(input_data)


class TestAuthServiceRefreshTokens:
    """Tests for AuthService.refresh_tokens."""

    @pytest.mark.asyncio
    async def test_refresh_tokens_success(self):
        """Should return new tokens on successful refresh."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_user = MagicMock(spec=User)
        mock_user.username = "testuser"
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Create a mock TokenData
        mock_token_data = MagicMock()
        mock_token_data.username = "testuser"

        with patch("app.services.auth_service.get_db", return_value=mock_db):
            service = AuthService()

            with patch("app.services.auth_service.verify_refresh_token", return_value=mock_token_data):
                result = await service.refresh_tokens("valid_refresh_token")

        assert isinstance(result, TokenResult)
        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_tokens_invalid_token(self):
        """Should raise InvalidRefreshTokenError when token is invalid."""
        mock_db = MagicMock()

        from fastapi import HTTPException

        with patch("app.services.auth_service.get_db", return_value=mock_db):
            service = AuthService()

            with patch(
                "app.services.auth_service.verify_refresh_token",
                side_effect=HTTPException(status_code=401, detail="Invalid token"),
            ):
                with pytest.raises(InvalidRefreshTokenError):
                    await service.refresh_tokens("invalid_token")

    @pytest.mark.asyncio
    async def test_refresh_tokens_no_username_in_token(self):
        """Should raise InvalidRefreshTokenError when token has no username."""
        mock_db = MagicMock()

        mock_token_data = MagicMock()
        mock_token_data.username = None

        with patch("app.services.auth_service.get_db", return_value=mock_db):
            service = AuthService()

            with patch("app.services.auth_service.verify_refresh_token", return_value=mock_token_data):
                with pytest.raises(InvalidRefreshTokenError):
                    await service.refresh_tokens("token_without_username")

    @pytest.mark.asyncio
    async def test_refresh_tokens_user_not_found(self):
        """Should raise InvalidRefreshTokenError when user no longer exists."""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        mock_token_data = MagicMock()
        mock_token_data.username = "deleteduser"

        with patch("app.services.auth_service.get_db", return_value=mock_db):
            service = AuthService()

            with patch("app.services.auth_service.verify_refresh_token", return_value=mock_token_data):
                with pytest.raises(InvalidRefreshTokenError):
                    await service.refresh_tokens("valid_token_deleted_user")


class TestAuthServiceCreateTokens:
    """Tests for AuthService._create_tokens."""

    @pytest.mark.asyncio
    async def test_create_tokens_returns_token_result(self):
        """Should return TokenResult with all fields populated."""
        service = AuthService()

        result = service._create_tokens("testuser")

        assert isinstance(result, TokenResult)
        assert result.access_token is not None
        assert len(result.access_token) > 0
        assert result.refresh_token is not None
        assert len(result.refresh_token) > 0
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_create_tokens_different_tokens(self):
        """Access and refresh tokens should be different."""
        service = AuthService()

        result = service._create_tokens("testuser")

        assert result.access_token != result.refresh_token


class TestAuthenticationError:
    """Tests for AuthenticationError exception."""

    def test_default_message(self):
        """Should have default error message."""
        error = AuthenticationError()
        assert "Invalid username or password" in str(error)

    def test_custom_message(self):
        """Should accept custom error message."""
        error = AuthenticationError("Custom auth error")
        assert "Custom auth error" in str(error)


class TestInvalidRefreshTokenError:
    """Tests for InvalidRefreshTokenError exception."""

    def test_default_message(self):
        """Should have default error message."""
        error = InvalidRefreshTokenError()
        assert "Could not validate refresh token" in str(error)

    def test_custom_message(self):
        """Should accept custom error message."""
        error = InvalidRefreshTokenError("Token expired")
        assert "Token expired" in str(error)


class TestLoginInput:
    """Tests for LoginInput dataclass."""

    def test_login_input_fields(self):
        """Should store username and password."""
        input_data = LoginInput(username="user", password="pass")
        assert input_data.username == "user"
        assert input_data.password == "pass"


class TestTokenResult:
    """Tests for TokenResult dataclass."""

    def test_token_result_fields(self):
        """Should store all token fields."""
        result = TokenResult(access_token="access", refresh_token="refresh", token_type="bearer")
        assert result.access_token == "access"
        assert result.refresh_token == "refresh"
        assert result.token_type == "bearer"

    def test_token_result_default_type(self):
        """Should default to bearer token type."""
        result = TokenResult(access_token="access", refresh_token="refresh")
        assert result.token_type == "bearer"
