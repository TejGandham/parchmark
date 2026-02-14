"""
OIDC token validation for hybrid authentication.
Validates Authelia-issued tokens (both JWT and opaque) and extracts user claims.
"""

import asyncio
import logging
import os
from datetime import UTC, datetime

import httpx
from dotenv import load_dotenv
from jose import JWTError, jwt

load_dotenv()

logger = logging.getLogger(__name__)

# OIDC Configuration from environment
OIDC_ISSUER_URL = os.getenv("OIDC_ISSUER_URL", "https://auth.engen.tech")
# Separate URL for fetching discovery/JWKS — allows using internal cluster DNS
# to bypass CDN challenges (e.g., Cloudflare JS challenges block non-browser clients).
# Defaults to OIDC_ISSUER_URL for backward compatibility.
OIDC_DISCOVERY_URL = os.getenv("OIDC_DISCOVERY_URL", OIDC_ISSUER_URL)
OIDC_AUDIENCE = os.getenv("OIDC_AUDIENCE", "parchmark")
OIDC_USERNAME_CLAIM = os.getenv("OIDC_USERNAME_CLAIM", "preferred_username")
OIDC_OPAQUE_TOKEN_PREFIX = os.getenv("OIDC_OPAQUE_TOKEN_PREFIX", "")
# Minimum length for opaque tokens — rejects obvious garbage before making IdP calls
OIDC_OPAQUE_TOKEN_MIN_LENGTH = 20


class OIDCValidator:
    """Validates OIDC tokens issued by Authelia (both JWT and opaque access tokens)."""

    # Overall timeout for JWKS fetch operation (discovery + JWKS fetch)
    # Individual HTTP requests have 10s timeout, but overall operation is capped at 15s
    JWKS_FETCH_TIMEOUT_SECONDS = 15.0

    def __init__(self):
        """Initialize OIDC validator with discovery endpoint configuration."""
        self.issuer_url = OIDC_ISSUER_URL
        self.discovery_url = OIDC_DISCOVERY_URL
        self.audience = OIDC_AUDIENCE
        self.username_claim = OIDC_USERNAME_CLAIM
        self.jwks_cache: dict | None = None
        self.jwks_cache_time: datetime | None = None
        self.jwks_cache_ttl_seconds = 3600  # 1 hour
        self._jwks_lock = asyncio.Lock()  # Lock to prevent concurrent JWKS fetches
        self._discovery_cache: dict | None = None
        self._discovery_cache_time: datetime | None = None
        self._discovery_lock = asyncio.Lock()  # Lock to prevent concurrent discovery fetches
        self._http_client: httpx.AsyncClient | None = None

    @staticmethod
    def is_opaque_token(token: str) -> bool:
        """Check if a token is opaque (not a JWT).

        JWTs have exactly 3 dot-separated base64url segments (header.payload.signature).
        Opaque tokens (e.g., Authelia's ``authelia_at_`` format) lack this structure.

        Rejects tokens that are too short to be valid (prevents garbage tokens from
        triggering outbound IdP calls) and optionally requires a configurable prefix.

        Args:
            token: The access token to inspect

        Returns:
            bool: True if the token is opaque, False if it has JWT structure
                  or is too short/malformed to be a valid opaque token
        """
        if len(token.split(".")) == 3:
            return False  # JWT structure
        # Reject obviously invalid tokens (too short to be real opaque tokens)
        if len(token) < OIDC_OPAQUE_TOKEN_MIN_LENGTH:
            return False
        # If a prefix is configured, require it
        if OIDC_OPAQUE_TOKEN_PREFIX and not token.startswith(OIDC_OPAQUE_TOKEN_PREFIX):
            return False
        return True

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the shared HTTP client for OIDC endpoint calls."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=10.0)
        return self._http_client

    async def close(self) -> None:
        """Close the shared HTTP client. Call during application shutdown."""
        if self._http_client is not None and not self._http_client.is_closed:
            await self._http_client.aclose()

    async def get_discovery_document(self) -> dict:
        """Fetch and cache the OIDC discovery document.

        Uses double-checked locking to prevent concurrent fetches during cache expiration.

        Returns:
            dict: OIDC discovery document

        Raises:
            Exception: If unable to fetch discovery document
        """
        # Fast path: check cache without lock
        if self._discovery_cache and self._discovery_cache_time:
            age_seconds = (datetime.now(UTC) - self._discovery_cache_time).total_seconds()
            if age_seconds < self.jwks_cache_ttl_seconds:
                return self._discovery_cache

        # Slow path: acquire lock for cache update
        async with self._discovery_lock:
            # Double-check after acquiring lock
            if self._discovery_cache and self._discovery_cache_time:
                age_seconds = (datetime.now(UTC) - self._discovery_cache_time).total_seconds()
                if age_seconds < self.jwks_cache_ttl_seconds:
                    return self._discovery_cache

            try:
                client = await self._get_client()
                discovery_url = f"{self.discovery_url}/.well-known/openid-configuration"
                response = await client.get(discovery_url)
                response.raise_for_status()

                discovery_result = response.json()
                self._discovery_cache = discovery_result
                self._discovery_cache_time = datetime.now(UTC)
                logger.debug("Discovery document cache updated successfully")

                return discovery_result
            except Exception as e:
                logger.error(f"Failed to fetch discovery document: {e}")
                raise

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
                    discovery_data = await self.get_discovery_document()
                    jwks_uri = discovery_data.get("jwks_uri")

                    if not jwks_uri:
                        raise ValueError("No jwks_uri in discovery endpoint")

                    client = await self._get_client()
                    jwks_response = await client.get(jwks_uri)
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
            # Note: jwt.decode() automatically validates expiration (exp claim)
            #
            # First try with audience validation, fall back to no audience check
            # if the token has an empty audience (Authelia may not set it)
            try:
                payload = jwt.decode(
                    token,
                    key_data,
                    algorithms=["RS256"],
                    audience=self.audience,
                    issuer=self.issuer_url,
                )
            except JWTError as e:
                if "audience" in str(e).lower():
                    # Retry without audience validation, check client_id instead
                    logger.info("Audience validation failed, checking client_id")
                    payload = jwt.decode(
                        token,
                        key_data,
                        algorithms=["RS256"],
                        issuer=self.issuer_url,
                        options={"verify_aud": False},
                    )
                    # Verify client_id matches as fallback
                    if payload.get("client_id") != self.audience:
                        raise JWTError(
                            f"client_id '{payload.get('client_id')}' does not match expected '{self.audience}'"
                        ) from None
                else:
                    raise

            return payload

        except JWTError as e:
            logger.warning(f"OIDC token validation failed: {e}")
            raise

    async def validate_opaque_token(self, token: str) -> dict:
        """Validate an opaque access token via the userinfo endpoint.

        Per OAuth 2.0 / OIDC spec, opaque access tokens are validated by presenting
        them to the authorization server's userinfo endpoint. If the server accepts
        the token, it returns user claims; if rejected, it returns an HTTP error.

        Args:
            token: Opaque access token (e.g., Authelia's ``authelia_at_`` format)

        Returns:
            dict: User claims from the userinfo endpoint (sub, preferred_username, email, etc.)

        Raises:
            ValueError: If userinfo response is missing the required ``sub`` claim
            httpx.HTTPStatusError: If the userinfo endpoint rejects the token
        """
        userinfo = await self.get_userinfo(token)

        if not userinfo.get("sub"):
            raise ValueError("Userinfo response missing required 'sub' claim")

        # Defense-in-depth: reject tokens minted for other clients (when claim is present)
        token_client = userinfo.get("azp") or userinfo.get("client_id")
        if token_client and token_client != self.audience:
            raise ValueError(f"Token client '{token_client}' does not match expected '{self.audience}'")

        return userinfo

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

        Used for validating opaque access tokens and fetching user claims
        when the access token doesn't contain them directly.

        Args:
            access_token: Valid OIDC access token (JWT or opaque)

        Returns:
            dict: User info from userinfo endpoint

        Raises:
            httpx.HTTPStatusError: If the userinfo endpoint rejects the token
            ValueError: If discovery document lacks userinfo_endpoint
        """
        try:
            discovery_data = await self.get_discovery_document()
            userinfo_url = discovery_data.get("userinfo_endpoint")

            if not userinfo_url:
                raise ValueError("No userinfo_endpoint in discovery document")

            client = await self._get_client()
            userinfo_response = await client.get(
                userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            userinfo_response.raise_for_status()

            return userinfo_response.json()
        except Exception as e:
            logger.error(f"Failed to fetch userinfo: {e}")
            raise


# Singleton instance
oidc_validator = OIDCValidator()
