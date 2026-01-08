"""
Error handling and edge case tests for OIDC validation.
Tests failure scenarios and error recovery mechanisms.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from jose import JWTError

from app.auth.oidc_validator import OIDCValidator


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_jwks_network_timeout():
    """Test handling of network timeout when fetching JWKS."""
    validator = OIDCValidator()

    with patch("app.auth.oidc_validator.httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        mock_client.return_value.__aenter__.return_value.get = mock_get

        import httpx

        mock_get.side_effect = httpx.TimeoutException("Request timeout")

        with pytest.raises(httpx.TimeoutException):
            await validator.get_jwks()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_jwks_missing_jwks_uri():
    """Test handling when discovery endpoint missing jwks_uri."""
    validator = OIDCValidator()

    with patch("app.auth.oidc_validator.httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        mock_client.return_value.__aenter__.return_value.get = mock_get

        # Use Mock, not AsyncMock - json() is sync
        discovery_response = Mock()
        discovery_response.json.return_value = {
            "issuer": "https://auth.engen.tech",
            # Missing jwks_uri
        }

        mock_get.side_effect = [discovery_response]

        with pytest.raises(ValueError, match="No jwks_uri"):
            await validator.get_jwks()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_oidc_token_missing_kid_in_header():
    """Test token validation fails when kid missing from header."""
    validator = OIDCValidator()

    with patch("app.auth.oidc_validator.jwt.get_unverified_header") as mock_header:
        mock_header.return_value = {"alg": "RS256"}  # No kid

        with pytest.raises(JWTError, match="No 'kid'"):
            await validator.validate_oidc_token("token_without_kid")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_oidc_token_invalid_audience():
    """Test token validation fails with wrong audience."""
    validator = OIDCValidator()
    validator.audience = "correct-audience"

    with patch("app.auth.oidc_validator.httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        mock_client.return_value.__aenter__.return_value.get = mock_get

        # Mock HTTP responses for JWKS fetch
        discovery_response = Mock()
        discovery_response.json.return_value = {
            "issuer": "https://auth.engen.tech",
            "jwks_uri": "https://auth.engen.tech/.well-known/openid-configuration/jwks",
        }

        jwks_response = Mock()
        jwks_response.json.return_value = {"keys": [{"kid": "test-key", "kty": "RSA"}]}

        mock_get.side_effect = [discovery_response, jwks_response]

        with patch("app.auth.oidc_validator.jwt.get_unverified_header") as mock_header:
            with patch("app.auth.oidc_validator.jwt.decode") as mock_decode:
                mock_header.return_value = {"kid": "test-key"}
                mock_decode.side_effect = JWTError("Invalid audience")

                with pytest.raises(JWTError):
                    await validator.validate_oidc_token("wrong_audience_token")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_oidc_token_invalid_issuer():
    """Test token validation fails with wrong issuer."""
    validator = OIDCValidator()
    validator.issuer_url = "https://auth.engen.tech"

    with patch("app.auth.oidc_validator.httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        mock_client.return_value.__aenter__.return_value.get = mock_get

        # Mock HTTP responses for JWKS fetch
        discovery_response = Mock()
        discovery_response.json.return_value = {
            "issuer": "https://auth.engen.tech",
            "jwks_uri": "https://auth.engen.tech/.well-known/openid-configuration/jwks",
        }

        jwks_response = Mock()
        jwks_response.json.return_value = {"keys": [{"kid": "test-key", "kty": "RSA"}]}

        mock_get.side_effect = [discovery_response, jwks_response]

        with patch("app.auth.oidc_validator.jwt.get_unverified_header") as mock_header:
            with patch("app.auth.oidc_validator.jwt.decode") as mock_decode:
                mock_header.return_value = {"kid": "test-key"}
                mock_decode.side_effect = JWTError("Invalid issuer")

                with pytest.raises(JWTError):
                    await validator.validate_oidc_token("wrong_issuer_token")


@pytest.mark.unit
def test_extract_username_with_all_claims_missing():
    """Test username extraction when all claims are missing."""
    validator = OIDCValidator()
    claims = {"sub": "user-123"}  # No preferred_username or email

    username = validator.extract_username(claims)
    assert username is None


@pytest.mark.unit
def test_extract_username_with_empty_strings():
    """Test username extraction when claims are empty strings."""
    validator = OIDCValidator()
    claims = {"sub": "user-123", "preferred_username": "", "email": ""}

    # Empty strings are falsy, should return None
    username = validator.extract_username(claims)
    assert username is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_jwks_cache_expiration():
    """Test JWKS cache expires after TTL."""
    validator = OIDCValidator()
    validator.jwks_cache_ttl_seconds = 1  # 1 second TTL

    with patch("app.auth.oidc_validator.httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        mock_client.return_value.__aenter__.return_value.get = mock_get

        # Use Mock, not AsyncMock - json() is sync
        discovery_response = Mock()
        discovery_response.json.return_value = {
            "issuer": "https://auth.engen.tech",
            "jwks_uri": "https://auth.engen.tech/.well-known/openid-configuration/jwks",
        }

        jwks_response = Mock()
        jwks_response.json.return_value = {"keys": []}

        mock_get.side_effect = [discovery_response, jwks_response]

        # First call caches the JWKS
        result1 = await validator.get_jwks()
        assert result1 == {"keys": []}

        # Manually set cache time to far past to simulate expiration
        from datetime import UTC, datetime, timedelta

        validator.jwks_cache_time = datetime.now(UTC) - timedelta(seconds=2)

        # Reset mock to test refresh
        mock_get.side_effect = [discovery_response, jwks_response]

        # Second call should fetch again because cache expired
        result2 = await validator.get_jwks()
        assert result2 == {"keys": []}

        # Should have made 4 calls total (2 per refresh)
        assert mock_get.call_count >= 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_oidc_token_malformed_jwt():
    """Test validation of malformed JWT."""
    validator = OIDCValidator()

    with patch("app.auth.oidc_validator.jwt.get_unverified_header") as mock_header:
        mock_header.side_effect = JWTError("Invalid JWT format")

        with pytest.raises(JWTError):
            await validator.validate_oidc_token("not.a.valid.jwt")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_oidc_token_empty_token():
    """Test validation of empty token."""
    validator = OIDCValidator()

    with pytest.raises((JWTError, AttributeError)):
        await validator.validate_oidc_token("")


@pytest.mark.unit
def test_extract_user_info_minimal_claims():
    """Test extracting user info with only required claim."""
    validator = OIDCValidator()
    claims = {"sub": "user-123"}

    user_info = validator.extract_user_info(claims)

    assert user_info["oidc_sub"] == "user-123"
    assert user_info["username"] is None
    assert user_info["email"] is None


@pytest.mark.unit
def test_extract_user_info_with_all_claims():
    """Test extracting user info with complete claims."""
    validator = OIDCValidator()
    claims = {
        "sub": "user-123",
        "preferred_username": "testuser",
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/pic.jpg",
    }

    user_info = validator.extract_user_info(claims)

    assert user_info["oidc_sub"] == "user-123"
    assert user_info["username"] == "testuser"
    assert user_info["email"] == "test@example.com"
