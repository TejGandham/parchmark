"""
OIDC token validation for hybrid authentication.
Validates Authelia-issued JWT tokens and extracts user claims.
"""

import asyncio
import json
import logging
import os
from datetime import UTC, datetime
from typing import cast

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from dotenv import load_dotenv
from jwt.algorithms import RSAAlgorithm
from jwt.exceptions import PyJWTError

load_dotenv()

logger = logging.getLogger(__name__)

# OIDC Configuration from environment
OIDC_ISSUER_URL = os.getenv("OIDC_ISSUER_URL", "https://auth.engen.tech")
OIDC_AUDIENCE = os.getenv("OIDC_AUDIENCE", "parchmark")
OIDC_USERNAME_CLAIM = os.getenv("OIDC_USERNAME_CLAIM", "preferred_username")


class OIDCValidator:
    """Validates OIDC tokens issued by Authelia."""

    # Overall timeout for JWKS fetch operation (discovery + JWKS fetch)
    # Individual HTTP requests have 10s timeout, but overall operation is capped at 15s
    JWKS_FETCH_TIMEOUT_SECONDS = 15.0

    def __init__(self):
        """Initialize OIDC validator with discovery endpoint configuration."""
        self.issuer_url = OIDC_ISSUER_URL
        self.audience = OIDC_AUDIENCE
        self.username_claim = OIDC_USERNAME_CLAIM
        self.jwks_cache: dict | None = None
        self.jwks_cache_time: datetime | None = None
        self.jwks_cache_ttl_seconds = 3600  # 1 hour
        self._jwks_lock = asyncio.Lock()  # Lock to prevent concurrent JWKS fetches

    async def get_jwks(self) -> dict:
        """
        Fetch JWKS from Authelia discovery endpoint with caching.

        Uses double-checked locking to prevent concurrent JWKS fetches during cache expiration.
        Only one request will fetch fresh JWKS; others will wait and use the result.

        Returns:
            dict: JWKS public keys

        Raises:
            Exception: If unable to fetch JWKS
        """
        # Fast path: check cache without lock
        if self.jwks_cache and self.jwks_cache_time:
            age_seconds = (datetime.now(UTC) - self.jwks_cache_time).total_seconds()
            if age_seconds < self.jwks_cache_ttl_seconds:
                return self.jwks_cache

        # Slow path: acquire lock for cache update
        async with self._jwks_lock:
            # Double-check cache after acquiring lock (another task may have fetched it)
            if self.jwks_cache and self.jwks_cache_time:
                age_seconds = (datetime.now(UTC) - self.jwks_cache_time).total_seconds()
                if age_seconds < self.jwks_cache_ttl_seconds:
                    return self.jwks_cache

            # Fetch fresh JWKS (only one task does this at a time)
            # Overall timeout prevents slow responses from blocking requests
            try:
                async with asyncio.timeout(self.JWKS_FETCH_TIMEOUT_SECONDS):
                    async with httpx.AsyncClient() as client:
                        # Get OIDC discovery endpoint
                        discovery_url = f"{self.issuer_url}/.well-known/openid-configuration"
                        discovery_response = await client.get(discovery_url, timeout=10.0)
                        discovery_response.raise_for_status()

                        discovery_data = discovery_response.json()
                        jwks_uri = discovery_data.get("jwks_uri")

                        if not jwks_uri:
                            raise ValueError("No jwks_uri in discovery endpoint")

                        # Fetch JWKS
                        jwks_response = await client.get(jwks_uri, timeout=10.0)
                        jwks_response.raise_for_status()

                        # Update cache atomically
                        jwks_result = jwks_response.json()
                        self.jwks_cache = jwks_result
                        self.jwks_cache_time = datetime.now(UTC)
                        logger.debug("JWKS cache updated successfully")

                        return jwks_result
            except TimeoutError:
                logger.error(f"JWKS fetch timed out after {self.JWKS_FETCH_TIMEOUT_SECONDS}s")
                raise
            except Exception as e:
                logger.error(f"Failed to fetch JWKS: {e}")
                raise

    async def validate_oidc_token(self, token: str) -> dict:
        """
        Validate OIDC JWT token issued by Authelia.

        Args:
            token: JWT token from Authelia

        Returns:
            dict: Token claims including user identifier

        Raises:
            PyJWTError: If token validation fails
        """
        try:
            # Get unverified header to extract kid (key ID)
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise PyJWTError("No 'kid' in token header")

            # Fetch JWKS
            jwks = await self.get_jwks()
            keys = jwks.get("keys", [])

            # Find the matching key
            key_data = None
            for key in keys:
                if key.get("kid") == kid:
                    key_data = key
                    break

            if not key_data:
                raise PyJWTError(f"Key '{kid}' not found in JWKS")

            # Convert JWK to public key for PyJWT
            public_key = cast(RSAPublicKey, RSAAlgorithm.from_jwk(json.dumps(key_data)))

            # Decode and validate token
            # jwt.decode() requires a proper key object for RS256 validation
            # Note: jwt.decode() automatically validates expiration (exp claim)
            #
            # First try with audience validation, fall back to no audience check
            # if the token has an empty audience (Authelia may not set it)
            try:
                payload = jwt.decode(
                    token,
                    public_key,
                    algorithms=["RS256"],
                    audience=self.audience,
                    issuer=self.issuer_url,
                )
            except PyJWTError as e:
                if "audience" in str(e).lower():
                    # Retry without audience validation, check client_id instead
                    logger.info("Audience validation failed, checking client_id")
                    payload = jwt.decode(
                        token,
                        public_key,
                        algorithms=["RS256"],
                        issuer=self.issuer_url,
                        options={"verify_aud": False},
                    )
                    # Verify client_id matches as fallback
                    if payload.get("client_id") != self.audience:
                        raise PyJWTError(
                            f"client_id '{payload.get('client_id')}' does not match expected '{self.audience}'"
                        ) from None
                else:
                    raise

            return payload

        except PyJWTError as e:
            logger.warning(f"OIDC token validation failed: {e}")
            raise

    def extract_username(self, token_claims: dict) -> str | None:
        """
        Extract username from OIDC token claims.

        Tries preferred_username first, falls back to email.

        Args:
            token_claims: Decoded JWT claims

        Returns:
            str: Username or email, None if neither found
        """
        username = token_claims.get(self.username_claim)
        if username:
            return username

        # Fallback to email
        email = token_claims.get("email")
        if email:
            return email

        return None

    def extract_user_info(self, token_claims: dict) -> dict:
        """
        Extract user information from OIDC token claims.

        Args:
            token_claims: Decoded JWT claims

        Returns:
            dict: User info with keys: oidc_sub, username, email
        """
        return {
            "oidc_sub": token_claims.get("sub"),
            "username": self.extract_username(token_claims),
            "email": token_claims.get("email"),
        }

    async def get_userinfo(self, access_token: str) -> dict:
        """
        Fetch user info from the OIDC userinfo endpoint.

        Used when access token doesn't contain user claims (preferred_username, email).

        Args:
            access_token: Valid OIDC access token

        Returns:
            dict: User info from userinfo endpoint

        Raises:
            Exception: If unable to fetch userinfo
        """
        try:
            async with httpx.AsyncClient() as client:
                # Get userinfo endpoint from discovery
                discovery_url = f"{self.issuer_url}/.well-known/openid-configuration"
                discovery_response = await client.get(discovery_url, timeout=10.0)
                discovery_response.raise_for_status()

                discovery_data = discovery_response.json()
                userinfo_url = discovery_data.get("userinfo_endpoint")

                if not userinfo_url:
                    raise ValueError("No userinfo_endpoint in discovery document")

                # Call userinfo endpoint with access token
                userinfo_response = await client.get(
                    userinfo_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0,
                )
                userinfo_response.raise_for_status()

                return userinfo_response.json()
        except Exception as e:
            logger.error(f"Failed to fetch userinfo: {e}")
            raise


# Singleton instance
oidc_validator = OIDCValidator()
