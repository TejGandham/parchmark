"""
Authentication dependencies for FastAPI routes.
Provides dependency functions for protected routes and user authentication.
Supports both local JWT and OIDC federated authentication.
"""

import logging

import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import credentials_exception, verify_token
from app.auth.oidc_validator import oidc_validator
from app.database.database import get_async_db
from app.models.models import User
from app.schemas.schemas import TokenData

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme for FastAPI
security = HTTPBearer()


async def _query_user_by_username(db: AsyncSession, username: str) -> User | None:
    """Async helper to query user by username."""
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalar_one_or_none()


async def _query_user_by_oidc_sub(db: AsyncSession, oidc_sub: str) -> User | None:
    """Async helper to query user by OIDC subject."""
    result = await db.execute(select(User).filter(User.oidc_sub == oidc_sub))
    return result.scalar_one_or_none()


async def _create_oidc_user(db: AsyncSession, user_info: dict) -> User:
    """Async helper to create OIDC user. Raises IntegrityError on race condition."""
    user = User(
        username=user_info["username"],
        email=user_info.get("email"),
        oidc_sub=user_info["oidc_sub"],
        auth_provider="oidc",
        password_hash=None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
) -> User:
    """
    Dependency function to get the current authenticated user.

    Supports hybrid authentication:
    1. Attempts to verify as local JWT first
    2. If local JWT fails, attempts OIDC validation
    3. For OIDC users, creates user if missing (with race condition handling)
    4. Returns the user object for use in protected routes

    Args:
        credentials: HTTP Bearer credentials containing the JWT token
        db: Async database session dependency

    Returns:
        User: The authenticated user object

    Raises:
        HTTPException: If token is invalid, expired, or user not found
    """
    token = credentials.credentials

    # Try local JWT first
    try:
        token_data: TokenData = verify_token(token, credentials_exception)
        if token_data.username is None:
            raise credentials_exception
        # Run async DB operation
        user = await _query_user_by_username(db, token_data.username)
        if user is not None:
            return user
    except HTTPException as e:
        # Local JWT failed, log reason and try OIDC fallback
        logger.debug(f"Local JWT validation failed (will try OIDC): status={e.status_code}, detail={e.detail}")

    # Try OIDC validation (supports both JWT and opaque access tokens)
    try:
        if oidc_validator.is_opaque_token(token):
            logger.debug("Opaque token detected, validating via userinfo endpoint")
            oidc_claims = await oidc_validator.validate_opaque_token(token)
        else:
            oidc_claims = await oidc_validator.validate_oidc_token(token)
        user_info = oidc_validator.extract_user_info(oidc_claims)

        # Validate required OIDC claims
        if not user_info.get("oidc_sub"):
            logger.error("OIDC token missing required 'sub' claim")
            raise credentials_exception

        # Look up user by oidc_sub
        user = await _query_user_by_oidc_sub(db, user_info["oidc_sub"])

        if user is None and not user_info.get("username"):
            # Access token doesn't have user claims - fetch from userinfo endpoint
            logger.info("Access token lacks user claims, fetching from userinfo endpoint")
            try:
                userinfo_data = await oidc_validator.get_userinfo(token)
                # Merge userinfo into user_info
                user_info["username"] = (
                    userinfo_data.get("preferred_username") or userinfo_data.get("email") or userinfo_data.get("name")
                )
                user_info["email"] = userinfo_data.get("email")
                logger.info(f"Got userinfo: username={user_info.get('username')}, email={user_info.get('email')}")
            except Exception as e:
                logger.warning(f"Failed to fetch userinfo: {e}")

        if user is None and not user_info.get("username"):
            # Still no username after userinfo fetch
            logger.warning(
                f"OIDC token has valid 'sub' but no username/email claim: oidc_sub={user_info['oidc_sub']}. "
                "Check OIDC provider configuration to include preferred_username or email claims."
            )
            raise credentials_exception

        if user is None and user_info.get("username"):
            # Auto-create OIDC user on first login
            # Handle race condition where concurrent requests both try to create the same user
            try:
                user = await _create_oidc_user(db, user_info)
                logger.info(f"Auto-created OIDC user: {user_info['username']} (oidc_sub={user_info['oidc_sub']})")
            except IntegrityError as e:
                # Another concurrent request created the user; rollback and retry lookup
                logger.debug(f"OIDC user creation race condition detected for oidc_sub={user_info['oidc_sub']}: {e}")
                await db.rollback()
                # Re-fetch the user created by the other request
                user = await _query_user_by_oidc_sub(db, user_info["oidc_sub"])
                if user is None:
                    logger.error(
                        f"Failed to retrieve OIDC user after race condition recovery: oidc_sub={user_info['oidc_sub']}"
                    )
                    raise credentials_exception from e

        if user is not None:
            return user
        else:
            # This should not happen - user creation should have succeeded or raised
            logger.error(
                f"OIDC user creation completed but user is None: oidc_sub={user_info['oidc_sub']}, "
                f"username={user_info.get('username')}"
            )
            raise credentials_exception

    except (JWTError, httpx.TimeoutException, httpx.HTTPError, ValueError) as e:
        # Expected OIDC validation failures - log at debug level
        logger.debug(f"OIDC token validation failed (expected): {type(e).__name__}: {e}")
    except IntegrityError as e:
        # Already handled in user creation block, but catch if it occurs elsewhere
        logger.error(f"Database integrity error during OIDC validation: {e}")
        await db.rollback()
    except HTTPException:
        # HTTPException (credentials_exception) is explicitly raised in the code above; re-raise it
        raise
    except Exception as e:
        # Unexpected errors - log at error level for investigation
        logger.error(f"Unexpected error during OIDC validation: {type(e).__name__}: {e}", exc_info=True)

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


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """
    Helper function to get a user by username from the database.

    This function is used by the authentication system to validate credentials.

    Args:
        db: Async database session
        username: Username to search for

    Returns:
        User: User object if found, None otherwise
    """
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_oidc_sub(db: AsyncSession, oidc_sub: str) -> User | None:
    """
    Helper function to get a user by OIDC subject claim from the database.

    Args:
        db: Async database session
        oidc_sub: OIDC subject identifier

    Returns:
        User: User object if found, None otherwise
    """
    result = await db.execute(select(User).filter(User.oidc_sub == oidc_sub))
    return result.scalar_one_or_none()


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
