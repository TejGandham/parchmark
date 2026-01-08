"""
OIDC token validation for hybrid authentication.
Validates Authelia-issued JWT tokens and extracts user claims.
"""

import os
import json
import logging
import asyncio
from datetime import datetime, UTC
from typing import Optional

import httpx
from dotenv import load_dotenv
from jose import JWTError, jwt

load_dotenv()

logger = logging.getLogger(__name__)

# OIDC Configuration from environment
OIDC_ISSUER_URL = os.getenv("OIDC_ISSUER_URL", "https://auth.engen.tech")
OIDC_AUDIENCE = os.getenv("OIDC_AUDIENCE", "parchmark-web")
OIDC_USERNAME_CLAIM = os.getenv("OIDC_USERNAME_CLAIM", "preferred_username")
AUTH_MODE = os.getenv("AUTH_MODE", "local")  # "local", "oidc", or "hybrid"


class OIDCValidator:
    """Validates OIDC tokens issued by Authelia."""

    def __init__(self):
        """Initialize OIDC validator with discovery endpoint configuration."""
        self.issuer_url = OIDC_ISSUER_URL
        self.audience = OIDC_AUDIENCE
        self.username_claim = OIDC_USERNAME_CLAIM
        self.jwks_cache: Optional[dict] = None
        self.jwks_cache_time: Optional[datetime] = None
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
            try:
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
            JWTError: If token validation fails
        """
        try:
            # Get unverified header to extract kid (key ID)
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise JWTError("No 'kid' in token header")

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
                raise JWTError(f"Key '{kid}' not found in JWKS")

            # Decode and validate token
            # jwt.decode() accepts JWK dict directly for RS256 validation
            payload = jwt.decode(
                token,
                key_data,
                algorithms=["RS256"],  # Authelia typically uses RS256
                audience=self.audience,
                issuer=self.issuer_url,
            )

            # Validate expiration
            if "exp" in payload:
                exp_time = datetime.fromtimestamp(payload["exp"], tz=UTC)
                if exp_time < datetime.now(UTC):
                    raise JWTError("Token expired")

            return payload

        except JWTError as e:
            logger.error(f"OIDC token validation failed: {e}")
            raise

    def extract_username(self, token_claims: dict) -> Optional[str]:
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


# Singleton instance
oidc_validator = OIDCValidator()
