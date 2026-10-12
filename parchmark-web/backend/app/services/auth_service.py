"""Authentication business logic: login, token issuance, and user lookup."""

from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    verify_user_password,
)
from app.models.models import User
from app.schemas.schemas import RefreshTokenRequest, Token, UserLogin


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """Query a user by username."""
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalar_one_or_none()


async def login(db: AsyncSession, user_credentials: UserLogin) -> Token:
    """Authenticate a user and issue access and refresh tokens.

    Verifies the supplied credentials and, on success, mints a fresh
    access/refresh token pair. Raises HTTP 401 with the frontend-expected
    message when the username is unknown or the password does not match.
    """
    # Get user from database and verify password
    user = await get_user_by_username(db, user_credentials.username)
    authenticated_user = verify_user_password(user, user_credentials.password)

    if not authenticated_user:
        # Return the same error message as the frontend expects
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT tokens with user's username as subject
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(data={"sub": authenticated_user.username}, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data={"sub": authenticated_user.username}, expires_delta=refresh_token_expires)

    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


async def refresh_access_token(db: AsyncSession, refresh_request: RefreshTokenRequest) -> Token:
    """Issue a new token pair from a valid refresh token.

    Validates the refresh token, confirms the referenced user still exists,
    and mints a fresh access/refresh token pair. Raises HTTP 401 when the
    token is invalid, carries no subject, or the user is not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Verify the refresh token
    token_data = verify_refresh_token(refresh_request.refresh_token, credentials_exception)

    # Ensure username is present in token
    if not token_data.username:
        raise credentials_exception

    # Get the user from database
    user = await get_user_by_username(db, token_data.username)
    if not user:
        raise credentials_exception

    # Create new tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    new_access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    new_refresh_token = create_refresh_token(data={"sub": user.username}, expires_delta=refresh_token_expires)

    return Token(access_token=new_access_token, refresh_token=new_refresh_token, token_type="bearer")
