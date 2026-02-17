"""
Integration tests for hybrid authentication (local + OIDC).
Tests authentication dependency that accepts both local JWT and OIDC tokens.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.oidc_validator import oidc_validator
from app.models.models import User


@pytest_asyncio.fixture
async def async_session(test_async_db_session):
    """Create an async session for testing."""
    session = test_async_db_session()
    try:
        yield session
    finally:
        await session.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_current_user_with_local_jwt(test_db_session, async_session: AsyncSession):
    """Test get_current_user with valid local JWT token."""
    # Create a test user using sync session (to commit to DB)
    user = User(username="testuser", password_hash="hashed_password", auth_provider="local")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    # Create valid local JWT
    from app.auth.auth import create_access_token

    token = create_access_token({"sub": "testuser"})

    # Mock HTTPAuthorizationCredentials
    credentials = MagicMock()
    credentials.credentials = token

    # Test with async session
    current_user = await get_current_user(credentials, async_session)

    assert current_user.username == "testuser"
    assert current_user.auth_provider == "local"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_current_user_with_oidc_token_existing_user(test_db_session, async_session: AsyncSession):
    """Test get_current_user with valid OIDC token for existing user."""
    # Create an OIDC user using sync session
    user = User(
        username="oidc_user",
        oidc_sub="authelia-sub-123",
        email="user@example.com",
        auth_provider="oidc",
        password_hash=None,
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    # Mock OIDC token validation
    mock_claims = {
        "sub": "authelia-sub-123",
        "preferred_username": "oidc_user",
        "email": "user@example.com",
    }

    # Mock credentials
    credentials = MagicMock()
    credentials.credentials = "oidc_token"

    # Mock local JWT verification to fail
    with patch("app.auth.dependencies.verify_token", side_effect=HTTPException(status_code=401)):
        with patch.object(oidc_validator, "validate_oidc_token", new_callable=AsyncMock) as mock_validate:
            with patch.object(oidc_validator, "extract_user_info") as mock_extract:
                mock_validate.return_value = mock_claims
                mock_extract.return_value = {
                    "oidc_sub": "authelia-sub-123",
                    "username": "oidc_user",
                    "email": "user@example.com",
                }

                current_user = await get_current_user(credentials, async_session)

                assert current_user.username == "oidc_user"
                assert current_user.auth_provider == "oidc"
                assert current_user.oidc_sub == "authelia-sub-123"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_current_user_with_oidc_token_new_user_creation(test_db_session, async_session: AsyncSession):
    """Test auto-creation of user on first OIDC login."""
    # No user exists yet
    assert test_db_session.query(User).filter(User.oidc_sub == "authelia-sub-456").first() is None

    # Mock OIDC token validation
    mock_claims = {
        "sub": "authelia-sub-456",
        "preferred_username": "new_oidc_user",
        "email": "newuser@example.com",
    }

    # Mock credentials
    credentials = MagicMock()
    credentials.credentials = "oidc_token"

    # Mock local JWT verification to fail
    with patch("app.auth.dependencies.verify_token", side_effect=HTTPException(status_code=401)):
        with patch.object(oidc_validator, "validate_oidc_token", new_callable=AsyncMock) as mock_validate:
            with patch.object(oidc_validator, "extract_user_info") as mock_extract:
                mock_validate.return_value = mock_claims
                mock_extract.return_value = {
                    "oidc_sub": "authelia-sub-456",
                    "username": "new_oidc_user",
                    "email": "newuser@example.com",
                }

                current_user = await get_current_user(credentials, async_session)

                assert current_user.username == "new_oidc_user"
                assert current_user.auth_provider == "oidc"
                assert current_user.oidc_sub == "authelia-sub-456"
                assert current_user.email == "newuser@example.com"
                assert current_user.password_hash is None

                # Verify user was created in database using async session
                result = await async_session.execute(select(User).filter(User.oidc_sub == "authelia-sub-456"))
                db_user = result.scalar_one_or_none()
                assert db_user is not None
                assert db_user.username == "new_oidc_user"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_current_user_both_auth_methods_fail(async_session: AsyncSession):
    """Test get_current_user fails when both local and OIDC validation fail."""
    # Mock credentials
    credentials = MagicMock()
    credentials.credentials = "invalid_token"

    # Mock both local and OIDC to fail
    with patch("app.auth.dependencies.verify_token", side_effect=HTTPException(status_code=401)):
        with patch.object(oidc_validator, "validate_oidc_token", new_callable=AsyncMock) as mock_validate:
            mock_validate.side_effect = Exception("OIDC validation failed")

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials, async_session)

            assert exc_info.value.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_current_user_oidc_user_email_fallback(test_db_session, async_session: AsyncSession):
    """Test OIDC user creation uses email as username if preferred_username missing."""
    # Mock OIDC token with only email (no preferred_username)
    mock_claims = {
        "sub": "authelia-sub-789",
        "email": "emailonly@example.com",
    }

    # Mock credentials
    credentials = MagicMock()
    credentials.credentials = "oidc_token"

    # Mock local JWT verification to fail
    with patch("app.auth.dependencies.verify_token", side_effect=HTTPException(status_code=401)):
        with patch.object(oidc_validator, "validate_oidc_token", new_callable=AsyncMock) as mock_validate:
            with patch.object(oidc_validator, "extract_user_info") as mock_extract:
                mock_validate.return_value = mock_claims
                mock_extract.return_value = {
                    "oidc_sub": "authelia-sub-789",
                    "username": "emailonly@example.com",
                    "email": "emailonly@example.com",
                }

                current_user = await get_current_user(credentials, async_session)

                assert current_user.username == "emailonly@example.com"
                assert current_user.auth_provider == "oidc"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_current_user_with_opaque_oidc_token(test_db_session, async_session: AsyncSession):
    """Test get_current_user with opaque OIDC access token (Authelia's default format).

    This tests the full flow: opaque token detected → userinfo endpoint called →
    user looked up/created → returned.
    """
    # No user exists yet
    assert test_db_session.query(User).filter(User.oidc_sub == "authelia-opaque-sub-001").first() is None

    # Mock OIDC userinfo response (what the userinfo endpoint returns for valid opaque tokens)
    mock_userinfo = {
        "sub": "authelia-opaque-sub-001",
        "preferred_username": "opaque_user",
        "email": "opaque@example.com",
    }

    # Mock credentials with opaque token
    credentials = MagicMock()
    credentials.credentials = "authelia_at_mFwMCsXWWuBDld5t_Tm8u48NNZXK9TW5p4Eo1QBkC40"

    # Mock local JWT verification to fail, then mock OIDC opaque token validation
    with patch("app.auth.dependencies.verify_token", side_effect=HTTPException(status_code=401)):
        with patch.object(oidc_validator, "is_opaque_token", return_value=True):
            with patch.object(oidc_validator, "validate_opaque_token", new_callable=AsyncMock) as mock_validate:
                with patch.object(oidc_validator, "extract_user_info") as mock_extract:
                    mock_validate.return_value = mock_userinfo
                    mock_extract.return_value = {
                        "oidc_sub": "authelia-opaque-sub-001",
                        "username": "opaque_user",
                        "email": "opaque@example.com",
                    }

                    current_user = await get_current_user(credentials, async_session)

                    assert current_user.username == "opaque_user"
                    assert current_user.auth_provider == "oidc"
                    assert current_user.oidc_sub == "authelia-opaque-sub-001"
                    assert current_user.email == "opaque@example.com"
                    assert current_user.password_hash is None

                    # Verify user was created in database
                    result = await async_session.execute(
                        select(User).filter(User.oidc_sub == "authelia-opaque-sub-001")
                    )
                    db_user = result.scalar_one_or_none()
                    assert db_user is not None
                    assert db_user.username == "opaque_user"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_current_user_with_opaque_token_existing_user(test_db_session, async_session: AsyncSession):
    """Test opaque token flow for an existing OIDC user (no auto-creation needed)."""
    # Create existing OIDC user
    user = User(
        username="existing_opaque_user",
        oidc_sub="authelia-opaque-sub-002",
        email="existing@example.com",
        auth_provider="oidc",
        password_hash=None,
    )
    test_db_session.add(user)
    test_db_session.commit()

    mock_userinfo = {
        "sub": "authelia-opaque-sub-002",
        "preferred_username": "existing_opaque_user",
        "email": "existing@example.com",
    }

    credentials = MagicMock()
    credentials.credentials = "authelia_at_existing_user_token"

    with patch("app.auth.dependencies.verify_token", side_effect=HTTPException(status_code=401)):
        with patch.object(oidc_validator, "is_opaque_token", return_value=True):
            with patch.object(oidc_validator, "validate_opaque_token", new_callable=AsyncMock) as mock_validate:
                with patch.object(oidc_validator, "extract_user_info") as mock_extract:
                    mock_validate.return_value = mock_userinfo
                    mock_extract.return_value = {
                        "oidc_sub": "authelia-opaque-sub-002",
                        "username": "existing_opaque_user",
                        "email": "existing@example.com",
                    }

                    current_user = await get_current_user(credentials, async_session)

                    assert current_user.username == "existing_opaque_user"
                    assert current_user.oidc_sub == "authelia-opaque-sub-002"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_user_by_oidc_sub(test_db_session, async_session: AsyncSession):
    """Test query_user_by_oidc_sub helper function."""
    from app.auth.dependencies import query_user_by_oidc_sub

    # Create OIDC user using sync session
    user = User(
        username="oidc_user",
        oidc_sub="authelia-sub-999",
        email="user@example.com",
        auth_provider="oidc",
        password_hash=None,
    )
    test_db_session.add(user)
    test_db_session.commit()

    # Test finding user with async query
    found_user = await query_user_by_oidc_sub(async_session, "authelia-sub-999")
    assert found_user is not None
    assert found_user.username == "oidc_user"

    # Test non-existent user
    not_found = await query_user_by_oidc_sub(async_session, "non-existent")
    assert not_found is None
