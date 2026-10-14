"""
Integration tests for personal API tokens: the /api/auth/tokens endpoints and
token authentication in the auth dependency.
"""

import hashlib
from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_password_hash
from app.models.api_token import ApiToken
from app.models.models import User

TOKENS_URL = "/api/auth/tokens"


def _create_token(client: TestClient, headers: dict[str, str], name: str = "mcp laptop") -> dict:
    response = client.post(TOKENS_URL, headers=headers, json={"name": name})
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def other_user_headers(client: TestClient, test_db_session: AsyncSession) -> dict[str, str]:
    """Login headers for a second local user."""
    test_db_session.add(User(username="otheruser", password_hash=get_password_hash("otherpass123")))
    await test_db_session.commit()
    response = client.post("/api/auth/login", json={"username": "otheruser", "password": "otherpass123"})
    return _bearer(response.json()["access_token"])


class TestCreateToken:
    def test_create_returns_plaintext_and_metadata(self, client: TestClient, auth_headers):
        data = _create_token(client, auth_headers, name="  mcp laptop  ")

        assert set(data) == {"id", "name", "created_at", "token"}
        assert data["name"] == "mcp laptop"
        assert data["token"].startswith("pmat_")
        assert len(data["token"]) > 40

    async def test_only_the_digest_is_stored(self, client: TestClient, auth_headers, test_db_session: AsyncSession):
        data = _create_token(client, auth_headers)

        row = await test_db_session.scalar(select(ApiToken).filter(ApiToken.id == data["id"]))
        assert row is not None
        assert row.token_hash == hashlib.sha256(data["token"].encode()).hexdigest()
        assert data["token"] not in {row.token_hash, row.name}

    def test_each_token_is_unique(self, client: TestClient, auth_headers):
        first = _create_token(client, auth_headers)
        second = _create_token(client, auth_headers)

        assert first["token"] != second["token"]
        assert first["id"] != second["id"]

    @pytest.mark.parametrize("name", ["", "   ", "x" * 101])
    def test_invalid_name_is_rejected(self, client: TestClient, auth_headers, name: str):
        response = client.post(TOKENS_URL, headers=auth_headers, json={"name": name})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_requires_authentication(self, client: TestClient):
        response = client.post(TOKENS_URL, json={"name": "cli"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestTokenAuthentication:
    def test_created_token_authenticates_a_request(self, client: TestClient, auth_headers, sample_user):
        token = _create_token(client, auth_headers)["token"]

        me = client.get("/api/auth/me", headers=_bearer(token))
        notes = client.get("/api/notes/", headers=_bearer(token))

        assert me.status_code == status.HTTP_200_OK
        assert me.json()["username"] == sample_user.username
        assert notes.status_code == status.HTTP_200_OK

    def test_unknown_token_is_rejected_with_401(self, client: TestClient, sample_user):
        response = client.get("/api/auth/me", headers=_bearer("pmat_not-a-real-token-0123456789abcdefghijk"))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Could not validate credentials"

    def test_api_token_is_never_sent_to_the_identity_provider(self, client: TestClient, sample_user):
        with patch("app.auth.dependencies.oidc_validator") as oidc:
            response = client.get("/api/auth/me", headers=_bearer("pmat_not-a-real-token-0123456789abcdefghijk"))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        oidc.validate_opaque_token.assert_not_called()
        oidc.validate_oidc_token.assert_not_called()
        oidc.get_userinfo.assert_not_called()


class TestListTokens:
    def test_lists_metadata_newest_first_without_plaintext(self, client: TestClient, auth_headers):
        first = _create_token(client, auth_headers, name="first")
        second = _create_token(client, auth_headers, name="second")

        response = client.get(TOKENS_URL, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert [item["name"] for item in data] == ["second", "first"]
        assert all(set(item) == {"id", "name", "created_at"} for item in data)
        assert first["token"] not in response.text
        assert second["token"] not in response.text

    def test_lists_only_the_callers_tokens(self, client: TestClient, auth_headers, other_user_headers):
        _create_token(client, other_user_headers, name="theirs")
        mine = _create_token(client, auth_headers, name="mine")

        data = client.get(TOKENS_URL, headers=auth_headers).json()

        assert [item["id"] for item in data] == [mine["id"]]

    def test_requires_authentication(self, client: TestClient):
        assert client.get(TOKENS_URL).status_code == status.HTTP_401_UNAUTHORIZED


class TestRevokeToken:
    def test_revoked_token_is_rejected_with_401(self, client: TestClient, auth_headers):
        created = _create_token(client, auth_headers)
        assert client.get("/api/auth/me", headers=_bearer(created["token"])).status_code == status.HTTP_200_OK

        response = client.delete(f"{TOKENS_URL}/{created['id']}", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "Token revoked successfully", "deleted_id": str(created["id"])}
        assert client.get("/api/auth/me", headers=_bearer(created["token"])).status_code == (
            status.HTTP_401_UNAUTHORIZED
        )
        assert client.get(TOKENS_URL, headers=auth_headers).json() == []

    def test_token_can_revoke_itself(self, client: TestClient, auth_headers):
        created = _create_token(client, auth_headers)

        response = client.delete(f"{TOKENS_URL}/{created['id']}", headers=_bearer(created["token"]))

        assert response.status_code == status.HTTP_200_OK
        assert client.get("/api/auth/me", headers=_bearer(created["token"])).status_code == (
            status.HTTP_401_UNAUTHORIZED
        )

    def test_cannot_revoke_another_users_token(self, client: TestClient, auth_headers, other_user_headers):
        theirs = _create_token(client, other_user_headers)

        response = client.delete(f"{TOKENS_URL}/{theirs['id']}", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert client.get("/api/auth/me", headers=_bearer(theirs["token"])).status_code == status.HTTP_200_OK

    def test_unknown_token_id_is_404(self, client: TestClient, auth_headers):
        response = client.delete(f"{TOKENS_URL}/999999", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Token not found"

    def test_requires_authentication(self, client: TestClient):
        assert client.delete(f"{TOKENS_URL}/1").status_code == status.HTTP_401_UNAUTHORIZED

    async def test_deleting_the_account_revokes_its_tokens(
        self, client: TestClient, auth_headers, sample_user_data, test_db_session: AsyncSession
    ):
        created = _create_token(client, auth_headers)

        response = client.request(
            "DELETE",
            "/api/settings/delete-account",
            headers=auth_headers,
            json={"password": sample_user_data["password"]},
        )

        assert response.status_code == status.HTTP_200_OK
        assert await test_db_session.scalar(select(ApiToken).filter(ApiToken.id == created["id"])) is None
        assert client.get("/api/auth/me", headers=_bearer(created["token"])).status_code == (
            status.HTTP_401_UNAUTHORIZED
        )
