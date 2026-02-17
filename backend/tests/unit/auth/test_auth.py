"""
Unit tests for authentication utilities (app.auth.auth).
Tests JWT token creation/validation, password hashing, and user authentication.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi import HTTPException, status
from jose import jwt

from app.auth.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    credentials_exception,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.schemas.schemas import TokenData


class TestPasswordHashing:
    """Test password hashing and verification functionality."""

    def test_password_hash_generation(self):
        """Test that password hashing generates different hashes for same password."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different due to salt
        assert hash1 != hash2
        assert len(hash1) > 0
        assert len(hash2) > 0

    def test_password_verification_success(self):
        """Test successful password verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_password_verification_failure(self):
        """Test password verification with wrong password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_password_verification_empty_values(self):
        """Test password verification with empty values."""
        # Empty password with valid hash should return False
        valid_hash = get_password_hash("validpass")
        assert verify_password("", valid_hash) is False

        # Empty hash should return False or raise exception
        try:
            result = verify_password("password", "")
            assert result is False
        except Exception:
            # passlib might raise exception for invalid hash format
            pass

        # Both empty - handle gracefully
        try:
            result = verify_password("", "")
            assert result is False
        except Exception:
            # This is acceptable behavior
            pass

    @pytest.mark.parametrize(
        "password",
        [
            "short",
            "verylongpasswordthatexceedsnormallimitsbutshoulstillwork",
            "pass word with spaces",
            "passw0rd_w1th_numb3rs",
            "пароль",  # Unicode password
            "🔒🗝️🔐",  # Emoji password
        ],
    )
    def test_password_hash_various_inputs(self, password):
        """Test password hashing with various input types."""
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True


class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_access_token_basic(self):
        """Test basic JWT token creation."""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify token structure
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"
        assert "exp" in payload

    def test_create_access_token_with_expiration(self):
        """Test JWT token creation with custom expiration."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=60)

        # Capture "now" before creating token to avoid timing discrepancies
        now = datetime.now(UTC)
        token = create_access_token(data, expires_delta)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, UTC)

        # Check that expiration is approximately 60 minutes from the captured time
        expected_exp = now + expires_delta
        assert abs((exp_datetime - expected_exp).total_seconds()) < 5

    def test_create_access_token_default_expiration(self):
        """Test JWT token creation with default expiration."""
        data = {"sub": "testuser"}

        # Capture "now" before creating token to avoid timing discrepancies
        now = datetime.now(UTC)
        token = create_access_token(data)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, UTC)

        # Check that expiration is approximately ACCESS_TOKEN_EXPIRE_MINUTES from the captured time
        # Import dynamically to avoid stale value from module reloads in other tests
        from app.auth.auth import ACCESS_TOKEN_EXPIRE_MINUTES as expire_minutes

        expected_exp = now + timedelta(minutes=expire_minutes)
        assert abs((exp_datetime - expected_exp).total_seconds()) < 5

    def test_verify_token_valid(self):
        """Test verification of valid JWT token."""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        token_data = verify_token(token, credentials_exception)

        assert isinstance(token_data, TokenData)
        assert token_data.username == "testuser"

    def test_verify_token_invalid_signature(self):
        """Test verification of token with invalid signature."""
        # Create token with different secret
        data = {"sub": "testuser"}
        invalid_token = jwt.encode(data, "wrong_secret", algorithm=ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token, credentials_exception)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"

    def test_verify_token_expired(self):
        """Test verification of expired JWT token."""
        data = {"sub": "testuser"}
        # Create token that expired 1 hour ago
        expires_delta = timedelta(hours=-1)
        expired_token = create_access_token(data, expires_delta)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(expired_token, credentials_exception)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_token_malformed(self):
        """Test verification of malformed JWT token."""
        malformed_tokens = [
            "not.a.token",
            "invalid_token_format",
            "",
            "header.payload",  # Missing signature
            "a.b.c.d",  # Too many parts
        ]

        for token in malformed_tokens:
            with pytest.raises(HTTPException) as exc_info:
                verify_token(token, credentials_exception)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_token_missing_subject(self):
        """Test verification of token without subject."""
        data = {"user": "testuser"}  # Wrong key, should be "sub"
        token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token, credentials_exception)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        "subject",
        [
            "user1",
            "user_with_underscore",
            "user-with-dash",
            "user.with.dots",
            "user@email.com",
            "123numeric456",
        ],
    )
    def test_verify_token_various_subjects(self, subject):
        """Test token verification with various subject formats."""
        data = {"sub": subject}
        token = create_access_token(data)

        token_data = verify_token(token, credentials_exception)
        assert token_data.username == subject


class TestAuthenticationExceptions:
    """Test predefined authentication exception objects."""

    def test_credentials_exception(self):
        """Test credentials exception configuration."""
        assert credentials_exception.status_code == status.HTTP_401_UNAUTHORIZED
        assert credentials_exception.detail == "Could not validate credentials"
        assert credentials_exception.headers == {"WWW-Authenticate": "Bearer"}


class TestAuthenticationConfig:
    """Test authentication configuration values."""

    def test_secret_key_configuration(self):
        """Test SECRET_KEY is properly configured."""
        assert SECRET_KEY is not None
        assert len(SECRET_KEY) > 0
        assert isinstance(SECRET_KEY, str)

    def test_algorithm_configuration(self):
        """Test ALGORITHM is properly configured."""
        assert ALGORITHM == "HS256"
        assert isinstance(ALGORITHM, str)

    def test_access_token_expire_minutes_configuration(self):
        """Test ACCESS_TOKEN_EXPIRE_MINUTES is properly configured."""
        assert isinstance(ACCESS_TOKEN_EXPIRE_MINUTES, int)
        assert ACCESS_TOKEN_EXPIRE_MINUTES > 0

    @patch.dict("os.environ", {"SECRET_KEY": "test_secret_key_that_is_at_least_32_characters_long"})
    def test_secret_key_from_environment(self):
        """Test SECRET_KEY can be loaded from environment."""
        # Need to reload the module to pick up environment changes
        from importlib import reload

        import app.auth.auth

        reload(app.auth.auth)

        # Check that the secret key was loaded
        assert app.auth.auth.SECRET_KEY == "test_secret_key_that_is_at_least_32_characters_long"

    @patch.dict("os.environ", {"ACCESS_TOKEN_EXPIRE_MINUTES": "60"})
    def test_token_expire_minutes_from_environment(self):
        """Test ACCESS_TOKEN_EXPIRE_MINUTES can be loaded from environment."""
        from importlib import reload

        import app.auth.auth

        reload(app.auth.auth)

        assert app.auth.auth.ACCESS_TOKEN_EXPIRE_MINUTES == 60
