"""
Authentication routes for ParchMark backend API.
Handles user login and logout operations with JWT token management, and
issuing, listing and revoking personal API tokens.
"""

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.database import get_async_db
from app.models.models import User
from app.schemas.api_token import ApiTokenCreate, ApiTokenCreated, ApiTokenResponse
from app.schemas.schemas import DeleteResponse, MessageResponse, RefreshTokenRequest, Token, UserLogin, UserResponse
from app.services import api_token_service, auth_service

# Create router for authentication endpoints
router = APIRouter(prefix="/auth", tags=["authentication"])

# Security scheme for logout endpoint
security = HTTPBearer()


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
    return await auth_service.login(db, user_credentials)


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
    return await auth_service.refresh_access_token(db, refresh_request)


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


@router.post("/tokens", response_model=ApiTokenCreated, status_code=status.HTTP_201_CREATED)
async def create_api_token(
    request: ApiTokenCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create a personal API token for the current user.

    The plaintext token is in this response only; it is never returned again.
    Send it as ``Authorization: Bearer <token>`` from non-browser clients.
    """
    return await api_token_service.create_token(db, current_user, request)


@router.get("/tokens", response_model=list[ApiTokenResponse])
async def list_api_tokens(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """List metadata for the current user's API tokens, newest first."""
    return await api_token_service.list_tokens(db, current_user)


@router.delete("/tokens/{token_id}", response_model=DeleteResponse)
async def revoke_api_token(
    token_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Revoke one of the current user's API tokens.

    Raises:
        HTTPException: 404 if the token does not exist or belongs to another user
    """
    return await api_token_service.revoke_token(db, current_user, token_id)
