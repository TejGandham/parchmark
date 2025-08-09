"""
Authentication routes for ParchMark backend API.
Handles user login and logout operations with JWT token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database.database import get_db
from app.models.models import User
from app.schemas.schemas import UserLogin, Token, UserResponse, MessageResponse
from app.auth.auth import (
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.auth.dependencies import get_user_by_username, get_current_user

# Create router for authentication endpoints
router = APIRouter(prefix="/auth", tags=["authentication"])

# Security scheme for logout endpoint
security = HTTPBearer()


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT access token.

    This endpoint:
    1. Validates the provided username and password
    2. Returns a JWT token if credentials are valid
    3. Returns an error if credentials are invalid

    Matches the frontend auth flow from the auth store.

    Args:
        user_credentials: UserLogin schema with username and password
        db: Database session dependency

    Returns:
        Token: JWT access token and token type

    Raises:
        HTTPException: 401 if credentials are invalid
    """

    # Define a helper function for database user lookup
    def get_user_from_db(username: str):
        return get_user_by_username(db, username)

    # Authenticate user using the auth utility function
    user = authenticate_user(
        username=user_credentials.username,
        password=user_credentials.password,
        user_db_check_func=get_user_from_db,
    )

    if not user:
        # Return the same error message as the frontend expects
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token with user's username as subject
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


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
    return UserResponse(username=current_user.username)


# Health check endpoint for authentication service
@router.get("/health")
async def auth_health_check():
    """
    Health check endpoint for authentication service.

    Returns:
        dict: Status message indicating auth service is operational
    """
    return {"status": "Authentication service is healthy"}
