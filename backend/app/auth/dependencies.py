"""
Authentication dependencies for FastAPI routes.
Provides dependency functions for protected routes and user authentication.
Supports both local JWT and OIDC federated authentication.
"""

import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.auth import credentials_exception, verify_token
from app.auth.oidc_validator import oidc_validator
from app.database.database import get_db
from app.models.models import User
from app.schemas.schemas import TokenData

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme for FastAPI
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency function to get the current authenticated user.

    Supports hybrid authentication:
    1. Attempts to verify as local JWT first
    2. If local JWT fails, attempts OIDC validation
    3. For OIDC users, creates user if missing
    4. Returns the user object for use in protected routes

    Args:
        credentials: HTTP Bearer credentials containing the JWT token
        db: Database session dependency

    Returns:
        User: The authenticated user object

    Raises:
        HTTPException: If token is invalid, expired, or user not found
    """
    token = credentials.credentials

    # Try local JWT first
    try:
        token_data: TokenData = verify_token(token, credentials_exception)
        user = db.query(User).filter(User.username == token_data.username).first()
        if user is not None:
            return user
    except HTTPException:
        pass  # Local JWT failed, try OIDC

    # Try OIDC validation
    try:
        oidc_claims = await oidc_validator.validate_oidc_token(token)
        user_info = oidc_validator.extract_user_info(oidc_claims)

        # Look up user by oidc_sub
        user = db.query(User).filter(User.oidc_sub == user_info["oidc_sub"]).first()

        if user is None and user_info["username"]:
            # Auto-create OIDC user on first login
            user = User(
                username=user_info["username"],
                email=user_info.get("email"),
                oidc_sub=user_info["oidc_sub"],
                auth_provider="oidc",
                password_hash=None,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        if user is not None:
            return user
    except Exception as e:
        logger.debug(f"OIDC validation failed: {e}")

    raise credentials_exception


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
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


def get_user_by_username(db: Session, username: str) -> User | None:
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


def get_user_by_oidc_sub(db: Session, oidc_sub: str) -> User | None:
    """
    Helper function to get a user by OIDC subject claim from the database.

    Args:
        db: Database session
        oidc_sub: OIDC subject identifier

    Returns:
        User: User object if found, None otherwise
    """
    return db.query(User).filter(User.oidc_sub == oidc_sub).first()


# Optional: Dependency for admin users (future use)
async def get_current_admin_user(
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
