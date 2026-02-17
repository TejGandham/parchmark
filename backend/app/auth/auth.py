"""
JWT authentication utilities for ParchMark backend.
Handles JWT token creation/validation and password hashing using bcrypt.
"""

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import cast

from dotenv import load_dotenv
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.models.models import User
from app.schemas.schemas import TokenData

# Load environment variables from .env file
load_dotenv()

# Module-level logger
logger = logging.getLogger(__name__)

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration from environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "CRITICAL SECURITY ERROR: SECRET_KEY environment variable is not set.\n"
        "A strong SECRET_KEY is required for production security.\n"
        "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'\n"
        "Then set it in your .env file: SECRET_KEY=<generated-key>"
    )
if len(SECRET_KEY) < 32:
    raise ValueError(
        f"SECURITY ERROR: SECRET_KEY must be at least 32 characters for security.\n"
        f"Current length: {len(SECRET_KEY)} characters\n"
        f"Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    )

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to compare against

    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plain password using bcrypt.

    Args:
        password: The plain text password to hash

    Returns:
        str: The hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: The data to encode in the token (typically {"sub": username})
        expires_delta: Optional custom expiration time

    Returns:
        str: The encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: The data to encode in the token (typically {"sub": username})
        expires_delta: Optional custom expiration time

    Returns:
        str: The encoded JWT refresh token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, credentials_exception: HTTPException, token_type: str = "access") -> TokenData:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT token to verify
        credentials_exception: Exception to raise if verification fails
        token_type: Expected token type ("access" or "refresh")

    Returns:
        TokenData: The decoded token data

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type_in_payload: str = payload.get("type", "access")

        if username is None:
            raise credentials_exception
        if token_type_in_payload != token_type:
            raise credentials_exception

        token_data = TokenData(username=username)
        return token_data
    except JWTError as e:
        raise credentials_exception from e


def verify_refresh_token(token: str, credentials_exception: HTTPException) -> TokenData:
    """
    Verify and decode a JWT refresh token.

    Args:
        token: The JWT refresh token to verify
        credentials_exception: Exception to raise if verification fails

    Returns:
        TokenData: The decoded token data

    Raises:
        HTTPException: If token is invalid or expired
    """
    return verify_token(token, credentials_exception, token_type="refresh")


def verify_user_password(user: "User | None", password: str) -> "User | None":
    """
    Verify password for a user object.

    Args:
        user: User object (or None if not found)
        password: The plain text password to verify

    Returns:
        User: User model if password verification successful, None otherwise
    """
    if not user:
        return None

    # Prevent local login for OIDC-only users
    if user.password_hash is None:
        logger.debug(f"Local login attempted for OIDC user: {user.username} (auth_provider={user.auth_provider})")
        return None

    # Verify the password hash (cast needed for mypy - SQLAlchemy types as Column[str])
    if not verify_password(password, cast(str, user.password_hash)):
        return None

    return user


# Common HTTP exceptions for authentication
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)
