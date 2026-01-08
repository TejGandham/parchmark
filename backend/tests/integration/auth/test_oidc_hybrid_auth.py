"""
Integration tests for hybrid authentication (local + OIDC).
Tests authentication dependency that accepts both local JWT and OIDC tokens.
"""

import pytest
from datetime import datetime, UTC, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import User
from app.auth.dependencies import get_current_user
from app.auth.oidc_validator import oidc_validator


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_current_user_with_local_jwt(db: Session):
    """Test get_current_user with valid local JWT token."""
    # Create a test user
    user = User(username="testuser", password_hash="hashed_password", auth_provider="local")
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create valid local JWT
    from app.auth.auth import create_access_token

    token = create_access_token({"sub": "testuser"})

    # Mock HTTPAuthorizationCredentials
    credentials = MagicMock()
    credentials.credentials = token

    # Test
    current_user = await get_current_user(credentials, db)

    assert current_user.username == "testuser"
    assert current_user.auth_provider == "local"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_current_user_with_oidc_token_existing_user(db: Session):
    """Test get_current_user with valid OIDC token for existing user."""
    # Create an OIDC user
    user = User(
        username="oidc_user",
        oidc_sub="authelia-sub-123",
        email="user@example.com",
        auth_provider="oidc",
        password_hash=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

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

                current_user = await get_current_user(credentials, db)

                assert current_user.username == "oidc_user"
                assert current_user.auth_provider == "oidc"
                assert current_user.oidc_sub == "authelia-sub-123"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_current_user_with_oidc_token_new_user_creation(db: Session):
    """Test auto-creation of user on first OIDC login."""
    # No user exists yet
    assert db.query(User).filter(User.oidc_sub == "authelia-sub-456").first() is None

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

                current_user = await get_current_user(credentials, db)

                assert current_user.username == "new_oidc_user"
                assert current_user.auth_provider == "oidc"
                assert current_user.oidc_sub == "authelia-sub-456"
                assert current_user.email == "newuser@example.com"
                assert current_user.password_hash is None

                # Verify user was created in database
                db_user = db.query(User).filter(User.oidc_sub == "authelia-sub-456").first()
                assert db_user is not None
                assert db_user.username == "new_oidc_user"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_current_user_both_auth_methods_fail(db: Session):
    """Test get_current_user fails when both local and OIDC validation fail."""
    # Mock credentials
    credentials = MagicMock()
    credentials.credentials = "invalid_token"

    # Mock both local and OIDC to fail
    with patch("app.auth.dependencies.verify_token", side_effect=HTTPException(status_code=401)):
        with patch.object(oidc_validator, "validate_oidc_token", new_callable=AsyncMock) as mock_validate:
            mock_validate.side_effect = Exception("OIDC validation failed")

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials, db)

            assert exc_info.value.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_current_user_oidc_user_email_fallback(db: Session):
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

                current_user = await get_current_user(credentials, db)

                assert current_user.username == "emailonly@example.com"
                assert current_user.auth_provider == "oidc"


@pytest.mark.integration
def test_get_user_by_oidc_sub(db: Session):
    """Test get_user_by_oidc_sub helper function."""
    from app.auth.dependencies import get_user_by_oidc_sub

    # Create OIDC user
    user = User(
        username="oidc_user",
        oidc_sub="authelia-sub-999",
        email="user@example.com",
        auth_provider="oidc",
        password_hash=None,
    )
    db.add(user)
    db.commit()

    # Test finding user
    found_user = get_user_by_oidc_sub(db, "authelia-sub-999")
    assert found_user is not None
    assert found_user.username == "oidc_user"

    # Test user not found
    not_found = get_user_by_oidc_sub(db, "non-existent-sub")
    assert not_found is None
