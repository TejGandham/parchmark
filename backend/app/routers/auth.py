"""
Authentication routes for ParchMark backend API.
Handles user login and logout operations with JWT token management.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.auth.dependencies import get_current_user
from app.database.database import get_async_db
from app.models.models import User
from app.schemas.schemas import MessageResponse, RefreshTokenRequest, Token, UserLogin, UserResponse

# Create router for authentication endpoints
router = APIRouter(prefix="/auth", tags=["authentication"])

# Security scheme for logout endpoint
security = HTTPBearer()


async def _get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """Async helper to get user by username."""
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalar_one_or_none()


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: AsyncSession = Depends(get_async_db)):
    """
    Authenticate user and return JWT access token.

    This endpoint:
    1. Validates the provided username and password
    2. Returns a JWT token if credentials are valid
    3. Returns an error if credentials are invalid

    Matches the frontend auth flow from the auth store.

    Args:
        user_credentials: UserLogin schema with username and password
        db: Async database session dependency

    Returns:
        Token: JWT access token and token type

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Get user from database
    user = await _get_user_by_username(db, user_credentials.username)

    # Define a sync helper for authenticate_user (it expects a sync callable)
    def get_user_from_result(username: str):
        return user if user and user.username == username else None

    # Authenticate user using the auth utility function
    authenticated_user = authenticate_user(
        username=user_credentials.username,
        password=user_credentials.password,
        user_db_check_func=get_user_from_result,
    )

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

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_request: RefreshTokenRequest, db: AsyncSession = Depends(get_async_db)):
    """
    Refresh an access token using a valid refresh token.

    This endpoint:
    1. Validates the provided refresh token
    2. Generates a new access token with a fresh expiration
    3. Returns both new access and refresh tokens

    Args:
        refresh_request: RefreshTokenRequest with refresh_token
        db: Async database session dependency

    Returns:
        Token: New JWT access and refresh tokens

    Raises:
        HTTPException: 401 if refresh token is invalid or expired
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
    user = await _get_user_by_username(db, token_data.username)
    if not user:
        raise credentials_exception

    # Create new tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    new_access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    new_refresh_token = create_refresh_token(data={"sub": user.username}, expires_delta=refresh_token_expires)

    return {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout endpoint for client-side token removal.

    Since JWT tokens are stateless, logout is primarily handled on the client side
    by removing the token from storage. This endpoint serves to:
    1. Validate that the user is currently authenticated
    2. Provide a consistent API for the frontend logout flow
    3. Allow for future server-side logout logic (token blacklisting, etc.)

    Matches the frontend auth flow where logout clears the authentication state.

    Args:
        current_user: Current authenticated user from JWT token

    Returns:
        MessageResponse: Confirmation message for successful logout
    """
    return {"message": f"User {current_user.username} logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    This endpoint allows the frontend to retrieve user information
    when a valid JWT token is provided. Useful for:
    1. Verifying token validity
    2. Getting user details for the UI
    3. Refreshing user state after page reload

    Args:
        current_user: Current authenticated user from JWT token

    Returns:
        UserResponse: User information (without password)
    """
    return UserResponse.model_validate(current_user)


# Health check endpoint for authentication service
@router.get("/health")
async def auth_health_check():
    """
    Health check endpoint for authentication service.

    Returns:
        dict: Status message indicating auth service is operational
    """
    return {"status": "Authentication service is healthy"}
