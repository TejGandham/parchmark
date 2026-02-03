"""
Authentication service for business logic related to user authentication.
Extracts business logic from routers for better testability and reusability.

This service is a singleton - it uses contextvars to access the request-scoped
database session without requiring it to be passed as a parameter.
"""

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import cast

from sqlalchemy import select

from app.auth.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    verify_user_password,
)
from app.database.context import get_db
from app.models.models import User
from app.schemas.schemas import TokenData

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(message)


class InvalidRefreshTokenError(Exception):
    """Raised when refresh token is invalid or expired."""

    def __init__(self, message: str = "Could not validate refresh token"):
        super().__init__(message)


@dataclass
class LoginInput:
    """Input data for user login."""

    username: str
    password: str


@dataclass
class TokenResult:
    """Result of successful authentication containing tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthService:
    """
    Service for authentication-related business logic.

    Handles user authentication, token generation, and token refresh
    with proper separation from HTTP layer concerns.

    This is a singleton service - database session is obtained from context
    for each operation, ensuring request isolation.
    """

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Retrieve a user by their username.

        Args:
            username: The username to look up.

        Returns:
            User object if found, None otherwise.
        """
        db = get_db()
        result = await db.execute(select(User).filter(User.username == username))
        return result.scalar_one_or_none()

    async def get_user_by_oidc_sub(self, oidc_sub: str) -> User | None:
        """
        Retrieve a user by their OIDC subject claim.

        Args:
            oidc_sub: The OIDC subject identifier.

        Returns:
            User object if found, None otherwise.
        """
        db = get_db()
        result = await db.execute(select(User).filter(User.oidc_sub == oidc_sub))
        return result.scalar_one_or_none()

    async def create_oidc_user(self, user_info: dict) -> User:
        """
        Create a new OIDC user.

        Args:
            user_info: Dictionary with 'oidc_sub', 'username', and optional 'email'.

        Returns:
            The created User object.

        Note:
            Uses flush() not commit() - middleware handles transaction.
            Caller should handle IntegrityError for race conditions.
        """
        db = get_db()
        user = User(
            username=user_info["username"],
            email=user_info.get("email"),
            oidc_sub=user_info["oidc_sub"],
            auth_provider="oidc",
            password_hash=None,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    def _create_tokens(self, username: str) -> TokenResult:
        """
        Create access and refresh tokens for a user.

        Args:
            username: The username to encode in the tokens.

        Returns:
            TokenResult containing access and refresh tokens.
        """
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = create_access_token(data={"sub": username}, expires_delta=access_token_expires)
        refresh_token = create_refresh_token(data={"sub": username}, expires_delta=refresh_token_expires)

        return TokenResult(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def login(self, input_data: LoginInput) -> TokenResult:
        """
        Authenticate a user and return tokens.

        Args:
            input_data: Login credentials (username and password).

        Returns:
            TokenResult containing access and refresh tokens.

        Raises:
            AuthenticationError: If credentials are invalid.
        """
        user = await self.get_user_by_username(input_data.username)
        authenticated_user = verify_user_password(user, input_data.password)

        if not authenticated_user:
            raise AuthenticationError()

        return self._create_tokens(cast(str, authenticated_user.username))

    async def refresh_tokens(self, refresh_token: str) -> TokenResult:
        """
        Refresh tokens using a valid refresh token.

        Args:
            refresh_token: The refresh token to validate.

        Returns:
            TokenResult containing new access and refresh tokens.

        Raises:
            InvalidRefreshTokenError: If refresh token is invalid or expired.
        """
        # Create a dummy exception for the verify function
        # (we'll catch the actual error and re-raise our own)
        from fastapi import HTTPException, status

        dummy_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            token_data: TokenData = verify_refresh_token(refresh_token, dummy_exception)
        except HTTPException:
            raise InvalidRefreshTokenError() from None

        if not token_data.username:
            raise InvalidRefreshTokenError()

        # Verify user still exists
        user = await self.get_user_by_username(token_data.username)
        if not user:
            raise InvalidRefreshTokenError()

        return self._create_tokens(cast(str, user.username))


# Singleton instance - use this instead of creating new instances
auth_service = AuthService()
