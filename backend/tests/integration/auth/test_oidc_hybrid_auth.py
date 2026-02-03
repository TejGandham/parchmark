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
from app.database.context import reset_db, set_db
from app.models.models import User
from app.services.auth_service import auth_service


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
    user = User(username="testuser", password_hash="hashed_password", auth_provider="local")
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    from app.auth.auth import create_access_token

    token = create_access_token({"sub": "testuser"})

    credentials = MagicMock()
    credentials.credentials = token

    token_ctx = set_db(async_session)
    try:
        current_user = await get_current_user(credentials)
        assert current_user.username == "testuser"
        assert current_user.auth_provider == "local"
    finally:
        reset_db(token_ctx)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_current_user_with_oidc_token_existing_user(test_db_session, async_session: AsyncSession):
    """Test get_current_user with valid OIDC token for existing user."""
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

    mock_claims = {
        "sub": "authelia-sub-123",
        "preferred_username": "oidc_user",
        "email": "user@example.com",
    }

    credentials = MagicMock()
    credentials.credentials = "oidc_token"

    token_ctx = set_db(async_session)
    try:
        with patch("app.auth.dependencies.verify_token", side_effect=HTTPException(status_code=401)):
            with patch.object(oidc_validator, "validate_oidc_token", new_callable=AsyncMock) as mock_validate:
                with patch.object(oidc_validator, "extract_user_info") as mock_extract:
                    mock_validate.return_value = mock_claims
                    mock_extract.return_value = {
                        "oidc_sub": "authelia-sub-123",
                        "username": "oidc_user",
                        "email": "user@example.com",
                    }

                    current_user = await get_current_user(credentials)

                    assert current_user.username == "oidc_user"
                    assert current_user.auth_provider == "oidc"
                    assert current_user.oidc_sub == "authelia-sub-123"
    finally:
        reset_db(token_ctx)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_current_user_with_oidc_token_new_user_creation(test_db_session, async_session: AsyncSession):
    """Test auto-creation of user on first OIDC login."""
    assert test_db_session.query(User).filter(User.oidc_sub == "authelia-sub-456").first() is None

    mock_claims = {
        "sub": "authelia-sub-456",
        "preferred_username": "new_oidc_user",
        "email": "newuser@example.com",
    }

    credentials = MagicMock()
    credentials.credentials = "oidc_token"

    token_ctx = set_db(async_session)
    try:
        with patch("app.auth.dependencies.verify_token", side_effect=HTTPException(status_code=401)):
            with patch.object(oidc_validator, "validate_oidc_token", new_callable=AsyncMock) as mock_validate:
                with patch.object(oidc_validator, "extract_user_info") as mock_extract:
                    mock_validate.return_value = mock_claims
                    mock_extract.return_value = {
                        "oidc_sub": "authelia-sub-456",
                        "username": "new_oidc_user",
                        "email": "newuser@example.com",
                    }

                    current_user = await get_current_user(credentials)

                    assert current_user.username == "new_oidc_user"
                    assert current_user.auth_provider == "oidc"
                    assert current_user.oidc_sub == "authelia-sub-456"
                    assert current_user.email == "newuser@example.com"
                    assert current_user.password_hash is None

                    result = await async_session.execute(select(User).filter(User.oidc_sub == "authelia-sub-456"))
                    db_user = result.scalar_one_or_none()
                    assert db_user is not None
                    assert db_user.username == "new_oidc_user"
    finally:
        reset_db(token_ctx)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_current_user_both_auth_methods_fail(async_session: AsyncSession):
    """Test get_current_user fails when both local and OIDC validation fail."""
    credentials = MagicMock()
    credentials.credentials = "invalid_token"

    token_ctx = set_db(async_session)
    try:
        with patch("app.auth.dependencies.verify_token", side_effect=HTTPException(status_code=401)):
            with patch.object(oidc_validator, "validate_oidc_token", new_callable=AsyncMock) as mock_validate:
                mock_validate.side_effect = Exception("OIDC validation failed")

                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(credentials)

                assert exc_info.value.status_code == 401
    finally:
        reset_db(token_ctx)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_current_user_oidc_user_email_fallback(test_db_session, async_session: AsyncSession):
    """Test OIDC user creation uses email as username if preferred_username missing."""
    mock_claims = {
        "sub": "authelia-sub-789",
        "email": "emailonly@example.com",
    }

    credentials = MagicMock()
    credentials.credentials = "oidc_token"

    token_ctx = set_db(async_session)
    try:
        with patch("app.auth.dependencies.verify_token", side_effect=HTTPException(status_code=401)):
            with patch.object(oidc_validator, "validate_oidc_token", new_callable=AsyncMock) as mock_validate:
                with patch.object(oidc_validator, "extract_user_info") as mock_extract:
                    mock_validate.return_value = mock_claims
                    mock_extract.return_value = {
                        "oidc_sub": "authelia-sub-789",
                        "username": "emailonly@example.com",
                        "email": "emailonly@example.com",
                    }

                    current_user = await get_current_user(credentials)

                    assert current_user.username == "emailonly@example.com"
                    assert current_user.auth_provider == "oidc"
    finally:
        reset_db(token_ctx)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_user_by_oidc_sub(test_db_session, async_session: AsyncSession):
    """Test auth_service.get_user_by_oidc_sub function."""
    user = User(
        username="oidc_user",
        oidc_sub="authelia-sub-999",
        email="user@example.com",
        auth_provider="oidc",
        password_hash=None,
    )
    test_db_session.add(user)
    test_db_session.commit()

    token_ctx = set_db(async_session)
    try:
        found_user = await auth_service.get_user_by_oidc_sub("authelia-sub-999")
        assert found_user is not None
        assert found_user.username == "oidc_user"

        not_found = await auth_service.get_user_by_oidc_sub("non-existent")
        assert not_found is None
    finally:
        reset_db(token_ctx)
