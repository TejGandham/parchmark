"""
JWT authentication utilities for ParchMark backend.
Handles JWT token creation/validation and password hashing using bcrypt.
"""

import os
from datetime import UTC, datetime, timedelta

from dotenv import load_dotenv
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.models.models import User
from app.schemas.schemas import TokenData

# Load environment variables from .env file
load_dotenv()

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
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


def authenticate_user(username: str, password: str, user_db_check_func) -> User | None:
    """
    Authenticate a user with username and password.

    Args:
        username: The username to authenticate
        password: The plain text password
        user_db_check_func: Function to get user from database by username

    Returns:
        User: User model if authentication successful, None otherwise
    """
    user = user_db_check_func(username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# Common HTTP exceptions for authentication
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

invalid_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid username or password",
    headers={"WWW-Authenticate": "Bearer"},
)
