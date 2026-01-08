"""
Unit tests for OIDC token validation.
Tests OIDC token validation, claim extraction, and JWKS caching.
"""

import json
import pytest
from datetime import datetime, UTC, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from jose import jwt

from app.auth.oidc_validator import OIDCValidator


@pytest.fixture
def oidc_validator():
    """Create an OIDC validator instance."""
    return OIDCValidator()


@pytest.fixture
def mock_jwks():
    """Mock JWKS response."""
    return {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-key-1",
                "use": "sig",
                "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINHaQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw",
                "e": "AQAB",
            }
        ]
    }


@pytest.fixture
def mock_discovery_endpoint():
    """Mock OIDC discovery endpoint."""
    return {
        "issuer": "https://auth.engen.tech",
        "authorization_endpoint": "https://auth.engen.tech/authorization",
        "token_endpoint": "https://auth.engen.tech/token",
        "userinfo_endpoint": "https://auth.engen.tech/userinfo",
        "jwks_uri": "https://auth.engen.tech/.well-known/openid-configuration/jwks",
        "end_session_endpoint": "https://auth.engen.tech/end_session",
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_jwks_success(oidc_validator, mock_jwks, mock_discovery_endpoint):
    """Test successful JWKS fetch."""
    with patch("app.auth.oidc_validator.httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        mock_client.return_value.__aenter__.return_value.get = mock_get

        # First call: discovery endpoint
        discovery_response = AsyncMock()
        discovery_response.json.return_value = mock_discovery_endpoint

        # Second call: JWKS endpoint
        jwks_response = AsyncMock()
        jwks_response.json.return_value = mock_jwks

        mock_get.side_effect = [discovery_response, jwks_response]

        result = await oidc_validator.get_jwks()

        assert result == mock_jwks
        assert mock_get.call_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_jwks_caching(oidc_validator, mock_jwks, mock_discovery_endpoint):
    """Test JWKS caching - second call should use cached result."""
    with patch("app.auth.oidc_validator.httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        mock_client.return_value.__aenter__.return_value.get = mock_get

        # Setup responses
        discovery_response = AsyncMock()
        discovery_response.json.return_value = mock_discovery_endpoint

        jwks_response = AsyncMock()
        jwks_response.json.return_value = mock_jwks

        mock_get.side_effect = [discovery_response, jwks_response]

        # First call
        result1 = await oidc_validator.get_jwks()
        assert result1 == mock_jwks

        # Second call - should use cache, no new HTTP calls
        result2 = await oidc_validator.get_jwks()
        assert result2 == mock_jwks

        # Should only have been called twice (discovery + jwks), not 4 times
        assert mock_get.call_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_jwks_failure(oidc_validator, mock_discovery_endpoint):
    """Test JWKS fetch failure."""
    with patch("app.auth.oidc_validator.httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        mock_client.return_value.__aenter__.return_value.get = mock_get

        # Discovery succeeds, but JWKS fails
        discovery_response = AsyncMock()
        discovery_response.json.return_value = mock_discovery_endpoint

        mock_get.side_effect = [discovery_response, Exception("JWKS fetch failed")]

        with pytest.raises(Exception):
            await oidc_validator.get_jwks()


@pytest.mark.unit
def test_extract_username_preferred(oidc_validator):
    """Test extracting username from preferred_username claim."""
    claims = {
        "sub": "user-123",
        "preferred_username": "testuser",
        "email": "test@example.com",
    }

    username = oidc_validator.extract_username(claims)
    assert username == "testuser"


@pytest.mark.unit
def test_extract_username_email_fallback(oidc_validator):
    """Test extracting username falls back to email."""
    claims = {
        "sub": "user-123",
        "email": "test@example.com",
    }

    username = oidc_validator.extract_username(claims)
    assert username == "test@example.com"


@pytest.mark.unit
def test_extract_username_none(oidc_validator):
    """Test extracting username returns None when not available."""
    claims = {"sub": "user-123"}

    username = oidc_validator.extract_username(claims)
    assert username is None


@pytest.mark.unit
def test_extract_user_info(oidc_validator):
    """Test extracting complete user info."""
    claims = {
        "sub": "user-123",
        "preferred_username": "testuser",
        "email": "test@example.com",
    }

    user_info = oidc_validator.extract_user_info(claims)

    assert user_info["oidc_sub"] == "user-123"
    assert user_info["username"] == "testuser"
    assert user_info["email"] == "test@example.com"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_oidc_token_success(oidc_validator, mock_jwks, mock_discovery_endpoint):
    """Test successful OIDC token validation."""
    # Create a valid token
    payload = {
        "sub": "user-123",
        "preferred_username": "testuser",
        "email": "test@example.com",
        "aud": "parchmark-web",
        "iss": "https://auth.engen.tech",
        "exp": (datetime.now(UTC) + timedelta(hours=1)).timestamp(),
    }

    # Mock JWT decode to return valid payload
    with patch("app.auth.oidc_validator.httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        mock_client.return_value.__aenter__.return_value.get = mock_get

        discovery_response = AsyncMock()
        discovery_response.json.return_value = mock_discovery_endpoint

        jwks_response = AsyncMock()
        jwks_response.json.return_value = mock_jwks

        mock_get.side_effect = [discovery_response, jwks_response]

        # Mock JWT decode
        with patch("app.auth.oidc_validator.jwt.decode") as mock_decode:
            mock_decode.return_value = payload
            with patch("app.auth.oidc_validator.jwt.get_unverified_header") as mock_header:
                mock_header.return_value = {"kid": "test-key-1"}

                result = await oidc_validator.validate_oidc_token("valid_token")

                assert result == payload


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_oidc_token_expired(oidc_validator):
    """Test validation of expired OIDC token."""
    # Create an expired token
    payload = {
        "sub": "user-123",
        "exp": (datetime.now(UTC) - timedelta(hours=1)).timestamp(),
    }

    with patch("app.auth.oidc_validator.jwt.get_unverified_header") as mock_header:
        with patch("app.auth.oidc_validator.jwt.decode") as mock_decode:
            mock_header.return_value = {"kid": "test-key-1"}
            from jose import JWTError

            mock_decode.side_effect = JWTError("Token expired")

            with pytest.raises(JWTError):
                await oidc_validator.validate_oidc_token("expired_token")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_oidc_token_invalid_kid(oidc_validator):
    """Test validation fails when key ID is not found."""
    with patch("app.auth.oidc_validator.jwt.get_unverified_header") as mock_header:
        mock_header.return_value = {"kid": "invalid-key"}

        with patch("app.auth.oidc_validator.httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock()
            mock_client.return_value.__aenter__.return_value.get = mock_get

            mock_discovery_endpoint = {
                "issuer": "https://auth.engen.tech",
                "jwks_uri": "https://auth.engen.tech/.well-known/openid-configuration/jwks",
            }

            mock_jwks = {"keys": []}

            discovery_response = AsyncMock()
            discovery_response.json.return_value = mock_discovery_endpoint

            jwks_response = AsyncMock()
            jwks_response.json.return_value = mock_jwks

            mock_get.side_effect = [discovery_response, jwks_response]

            from jose import JWTError

            with pytest.raises(JWTError, match="not found in JWKS"):
                await oidc_validator.validate_oidc_token("invalid_token")
