"""
Authentication routes for ParchMark backend API.
Handles user login and logout operations with JWT token management.
This router is a thin controller that delegates business logic to AuthService.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.database import get_async_db
from app.models.models import User
from app.schemas.schemas import MessageResponse, RefreshTokenRequest, Token, UserLogin, UserResponse
from app.services.auth_service import (
    AuthenticationError,
    AuthService,
    InvalidRefreshTokenError,
    LoginInput,
)

# Create router for authentication endpoints
router = APIRouter(prefix="/auth", tags=["authentication"])

# Security scheme for logout endpoint
security = HTTPBearer()


def get_auth_service(db: AsyncSession = Depends(get_async_db)) -> AuthService:
    """Dependency to get AuthService instance."""
    return AuthService(db)


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    service: AuthService = Depends(get_auth_service),
):
    """
    Authenticate user and return JWT access token.

    This endpoint:
    1. Validates the provided username and password
    2. Returns a JWT token if credentials are valid
    3. Returns an error if credentials are invalid

    Matches the frontend auth flow from the auth store.

    Args:
        user_credentials: UserLogin schema with username and password
        service: AuthService instance

    Returns:
        Token: JWT access token and token type

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    try:
        input_data = LoginInput(username=user_credentials.username, password=user_credentials.password)
        result = await service.login(input_data)
        return {
            "access_token": result.access_token,
            "refresh_token": result.refresh_token,
            "token_type": result.token_type,
        }
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
):
    """
    Refresh an access token using a valid refresh token.

    This endpoint:
    1. Validates the provided refresh token
    2. Generates a new access token with a fresh expiration
    3. Returns both new access and refresh tokens

    Args:
        refresh_request: RefreshTokenRequest with refresh_token
        service: AuthService instance

    Returns:
        Token: New JWT access and refresh tokens

    Raises:
        HTTPException: 401 if refresh token is invalid or expired
    """
    try:
        result = await service.refresh_tokens(refresh_request.refresh_token)
        return {
            "access_token": result.access_token,
            "refresh_token": result.refresh_token,
            "token_type": result.token_type,
        }
    except InvalidRefreshTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


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
