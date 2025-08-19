"""
Authentication dependencies for FastAPI routes.
Provides dependency functions for protected routes and user authentication.
"""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.auth import credentials_exception, verify_token
from app.database.database import get_db
from app.models.models import User
from app.schemas.schemas import TokenData

# HTTP Bearer token scheme for FastAPI
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency function to get the current authenticated user.

    This function:
    1. Extracts the JWT token from the Authorization header
    2. Verifies and decodes the token
    3. Retrieves the user from the database
    4. Returns the user object for use in protected routes

    Args:
        credentials: HTTP Bearer credentials containing the JWT token
        db: Database session dependency

    Returns:
        User: The authenticated user object

    Raises:
        HTTPException: If token is invalid, expired, or user not found
    """
    # Extract token from credentials
    token = credentials.credentials

    # Verify and decode the token
    token_data: TokenData = verify_token(token, credentials_exception)

    # Get user from database
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency function to get the current active user.

    This is an extension point for future user status checks (e.g., account disabled).
    Currently, it just returns the authenticated user.

    Args:
        current_user: The authenticated user from get_current_user dependency

    Returns:
        User: The active user object

    Raises:
        HTTPException: If user account is inactive (future implementation)
    """
    # Future: Add checks for user.is_active, user.is_verified, etc.
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")

    return current_user


def get_user_by_username(db: Session, username: str) -> User:
    """
    Helper function to get a user by username from the database.

    This function is used by the authentication system to validate credentials.

    Args:
        db: Database session
        username: Username to search for

    Returns:
        User: User object if found, None otherwise
    """
    return db.query(User).filter(User.username == username).first()


# Optional: Dependency for admin users (future use)
def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency function to get the current admin user.

    This is a placeholder for future admin functionality.
    Currently not used but provided for extensibility.

    Args:
        current_user: The authenticated active user

    Returns:
        User: The admin user object

    Raises:
        HTTPException: If user is not an admin
    """
    # Future: Add admin role checking
    # if not current_user.is_admin:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Not enough permissions"
    #     )

    return current_user
