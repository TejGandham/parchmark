"""
Unit tests for OIDC token validation.
Tests OIDC token validation, claim extraction, and JWKS caching.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

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

        # First call: discovery endpoint (use Mock, not AsyncMock - json() is sync)
        discovery_response = Mock()
        discovery_response.json.return_value = mock_discovery_endpoint

        # Second call: JWKS endpoint
        jwks_response = Mock()
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

        # Setup responses (use Mock, not AsyncMock - json() is sync)
        discovery_response = Mock()
        discovery_response.json.return_value = mock_discovery_endpoint

        jwks_response = Mock()
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

        # Discovery succeeds, but JWKS fails (use Mock - json() is sync)
        discovery_response = Mock()
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

        # Use Mock, not AsyncMock - json() is sync
        discovery_response = Mock()
        discovery_response.json.return_value = mock_discovery_endpoint

        jwks_response = Mock()
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
async def test_validate_oidc_token_expired(oidc_validator, mock_jwks, mock_discovery_endpoint):
    """Test validation of expired OIDC token."""
    with patch("app.auth.oidc_validator.httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        mock_client.return_value.__aenter__.return_value.get = mock_get

        # Mock HTTP responses for JWKS fetch
        discovery_response = Mock()
        discovery_response.json.return_value = mock_discovery_endpoint

        jwks_response = Mock()
        jwks_response.json.return_value = mock_jwks

        mock_get.side_effect = [discovery_response, jwks_response]

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

            # Use Mock, not AsyncMock - json() is sync
            discovery_response = Mock()
            discovery_response.json.return_value = mock_discovery_endpoint

            jwks_response = Mock()
            jwks_response.json.return_value = mock_jwks

            mock_get.side_effect = [discovery_response, jwks_response]

            from jose import JWTError

            with pytest.raises(JWTError, match="not found in JWKS"):
                await oidc_validator.validate_oidc_token("invalid_token")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_concurrent_jwks_fetch_uses_lock(mock_jwks, mock_discovery_endpoint):
    """Test that concurrent JWKS fetches use the lock correctly.

    When multiple coroutines try to fetch JWKS simultaneously (cache expired),
    only one should actually make the HTTP request while others wait and
    reuse the result (double-checked locking pattern).
    """
    validator = OIDCValidator()

    # Track how many times the HTTP client is created
    http_call_count = [0]

    async def mock_get_with_delay(url, **kwargs):
        """Simulate a slow HTTP request to allow concurrent access."""
        http_call_count[0] += 1
        await asyncio.sleep(0.1)  # Small delay to allow other coroutines to attempt access

        # Create a mock response with sync json() method
        class MockResponse:
            def json(self):
                # Check if it's the discovery endpoint (ends with openid-configuration)
                if url.endswith("/.well-known/openid-configuration"):
                    return mock_discovery_endpoint
                # Otherwise it's the JWKS endpoint
                return mock_jwks

            def raise_for_status(self):
                pass

        return MockResponse()

    with patch("app.auth.oidc_validator.httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.get = mock_get_with_delay
        mock_client.return_value.__aenter__.return_value = mock_instance

        # Launch 5 concurrent JWKS fetch requests
        tasks = [validator.get_jwks() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # All results should be the same JWKS
        for result in results:
            assert result == mock_jwks

        # Due to double-checked locking, only 2 HTTP calls should be made
        # (1 for discovery + 1 for JWKS), not 10 (5 * 2)
        assert http_call_count[0] == 2, f"Expected 2 HTTP calls, got {http_call_count[0]}"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_jwks_cache_expiration_triggers_single_refresh(mock_jwks, mock_discovery_endpoint):
    """Test that cache expiration triggers exactly one refresh with concurrent requests."""
    validator = OIDCValidator()
    validator.jwks_cache_ttl_seconds = 0.1  # Very short TTL for testing

    http_call_count = [0]

    async def mock_get(url, **kwargs):
        http_call_count[0] += 1
        await asyncio.sleep(0.05)

        # Create a mock response with sync json() method
        class MockResponse:
            def json(self):
                # Check if it's the discovery endpoint (ends with openid-configuration)
                if url.endswith("/.well-known/openid-configuration"):
                    return mock_discovery_endpoint
                # Otherwise it's the JWKS endpoint
                return mock_jwks

            def raise_for_status(self):
                pass

        return MockResponse()

    with patch("app.auth.oidc_validator.httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.get = mock_get
        mock_client.return_value.__aenter__.return_value = mock_instance

        # First fetch - populates cache
        result1 = await validator.get_jwks()
        assert result1 == mock_jwks
        assert http_call_count[0] == 2

        # Wait for cache to expire
        await asyncio.sleep(0.15)

        # Launch concurrent requests after cache expired
        http_call_count[0] = 0  # Reset counter
        tasks = [validator.get_jwks() for _ in range(3)]
        results = await asyncio.gather(*tasks)

        # All should get the same result
        for result in results:
            assert result == mock_jwks

        # Only one set of HTTP calls should occur (discovery + jwks)
        assert http_call_count[0] == 2, f"Expected 2 HTTP calls after expiration, got {http_call_count[0]}"
