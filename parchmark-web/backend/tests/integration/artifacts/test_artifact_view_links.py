"""
Integration tests for the owner's signed view links and raw-content endpoint:
POST /api/artifacts/{id}/view-link mints a link to /a/<slug>?v=&e=&s= that serves
exactly version v of any artifact, private or not, for 300 seconds, and every
failure of that signed path is the constant 404 of the unlisted path.
GET /api/artifacts/{id}/content returns the current version's raw text to the owner.
"""

import hashlib
import hmac
import os
import time
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import create_access_token
from app.models.models import User

ARTIFACTS_URL = "/api/artifacts"
V1 = "<h1>Version one</h1><script>document.title = 'v1'</script>"
V2 = "<h1>Version two</h1>"
NOW = 1_900_000_000


def _sign(slug: str, version: int | str, expiry: int | str, key: str | None = None) -> str:
    key = key if key is not None else os.environ["ARTIFACT_SIGNING_KEY"]
    return hmac.new(key.encode(), f"{slug}:{version}:{expiry}".encode(), hashlib.sha256).hexdigest()


def _signed_path(slug: str, version: int | str, expiry: int | str, signature: str | None = None) -> str:
    params = {"v": version, "e": expiry, "s": signature if signature is not None else _sign(slug, version, expiry)}
    return f"/a/{slug}?{urlencode(params)}"


def _publish(client: TestClient, headers: dict[str, str], content: str = V1, content_type: str = "html") -> dict:
    body = {"title": "Report", "content_type": content_type, "content": content}
    response = client.post(ARTIFACTS_URL, headers=headers, json=body)
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


def _publish_version(client: TestClient, headers: dict[str, str], artifact_id: int, content: str = V2) -> None:
    body = {"content_type": "html", "content": content}
    response = client.post(f"{ARTIFACTS_URL}/{artifact_id}/versions", headers=headers, json=body)
    assert response.status_code == status.HTTP_201_CREATED


def _mint(client: TestClient, headers: dict[str, str], artifact_id: int) -> Response:
    return client.post(f"{ARTIFACTS_URL}/{artifact_id}/view-link", headers=headers)


def _relative(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.path}?{parts.query}"


def _assert_constant_404(client: TestClient, response: Response) -> None:
    unknown = client.get("/a/no-such-slug")
    assert response.status_code == unknown.status_code == status.HTTP_404_NOT_FOUND
    assert dict(response.headers) == dict(unknown.headers)
    assert response.content == unknown.content


@pytest.fixture
async def other_user_headers(test_db_session: AsyncSession) -> dict[str, str]:
    """Bearer headers for a second, unrelated local user."""
    test_db_session.add(User(username="otheruser", password_hash="not-a-real-hash"))
    await test_db_session.commit()
    token = create_access_token(data={"sub": "otheruser"}, expires_delta=timedelta(minutes=30))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def frozen_now() -> Iterator[int]:
    """Pin time.time() to NOW so expiry boundaries are exact."""
    with patch("app.services.artifact_service.time.time", return_value=float(NOW)):
        yield NOW


class TestMint:
    def test_the_owner_gets_a_link_on_the_content_origin_that_expires_in_300_seconds(
        self, client: TestClient, auth_headers
    ):
        artifact = _publish(client, auth_headers)
        before = int(time.time())

        response = _mint(client, auth_headers, artifact["id"])

        after = int(time.time())
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        prefix = f"{os.environ['ARTIFACT_CONTENT_ORIGIN']}/a/{artifact['slug']}?v="
        assert body["url"].startswith(prefix)
        query = parse_qs(urlsplit(body["url"]).query)
        expiry = int(query["e"][0])
        assert query["v"] == ["1"]
        assert before + 300 <= expiry <= after + 300
        assert datetime.fromisoformat(body["expires_at"]) == datetime.fromtimestamp(expiry, tz=UTC)
        assert query["s"] == [_sign(artifact["slug"], 1, expiry)]

    def test_expiry_is_exactly_now_plus_300(self, client: TestClient, auth_headers, frozen_now: int):
        artifact = _publish(client, auth_headers)

        url = _mint(client, auth_headers, artifact["id"]).json()["url"]

        assert parse_qs(urlsplit(url).query)["e"] == [str(frozen_now + 300)]

    def test_the_link_names_the_current_version(self, client: TestClient, auth_headers):
        artifact = _publish(client, auth_headers)
        _publish_version(client, auth_headers, artifact["id"])

        url = _mint(client, auth_headers, artifact["id"]).json()["url"]

        assert parse_qs(urlsplit(url).query)["v"] == ["2"]

    def test_another_users_artifact_and_an_unknown_id_are_not_found(
        self, client: TestClient, auth_headers, other_user_headers
    ):
        artifact = _publish(client, auth_headers)

        assert _mint(client, other_user_headers, artifact["id"]).status_code == status.HTTP_404_NOT_FOUND
        assert _mint(client, auth_headers, 999_999).status_code == status.HTTP_404_NOT_FOUND

    def test_requires_authentication(self, client: TestClient, auth_headers):
        artifact = _publish(client, auth_headers)

        assert client.post(f"{ARTIFACTS_URL}/{artifact['id']}/view-link").status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


class TestSignedPath:
    def test_a_minted_link_serves_a_private_artifact_with_the_unlisted_header_set(
        self, client: TestClient, auth_headers
    ):
        artifact = _publish(client, auth_headers)
        url = _mint(client, auth_headers, artifact["id"]).json()["url"]

        signed = client.get(_relative(url))
        visibility = {"visibility": "unlisted"}
        client.post(f"{ARTIFACTS_URL}/{artifact['id']}/visibility", headers=auth_headers, json=visibility)
        unsigned = client.get(f"/a/{artifact['slug']}")

        assert signed.status_code == unsigned.status_code == status.HTTP_200_OK
        assert signed.content == unsigned.content == V1.encode()
        assert dict(signed.headers) == dict(unsigned.headers)
        assert "set-cookie" not in signed.headers
        assert "frame-ancestors" not in signed.headers["content-security-policy"]

    def test_a_link_for_version_1_still_serves_version_1_after_version_2_is_published(
        self, client: TestClient, auth_headers
    ):
        artifact = _publish(client, auth_headers)
        url = _mint(client, auth_headers, artifact["id"]).json()["url"]
        _publish_version(client, auth_headers, artifact["id"])

        response = client.get(_relative(url))

        assert response.status_code == status.HTTP_200_OK
        assert response.content == V1.encode()

    def test_a_link_for_an_older_version_of_an_unlisted_artifact_serves_that_version(
        self, client: TestClient, auth_headers, frozen_now: int
    ):
        artifact = _publish(client, auth_headers)
        _publish_version(client, auth_headers, artifact["id"])
        client.post(
            f"{ARTIFACTS_URL}/{artifact['id']}/visibility", headers=auth_headers, json={"visibility": "unlisted"}
        )

        response = client.get(_signed_path(artifact["slug"], 1, frozen_now + 60))

        assert response.content == V1.encode()

    def test_an_expiry_of_exactly_now_and_now_plus_300_is_served(
        self, client: TestClient, auth_headers, frozen_now: int
    ):
        artifact = _publish(client, auth_headers)

        for expiry in (frozen_now, frozen_now + 300):
            assert client.get(_signed_path(artifact["slug"], 1, expiry)).status_code == status.HTTP_200_OK

    @pytest.mark.parametrize(
        ("version", "expiry_offset", "slug"),
        [(1, -1, None), (1, 301, None), (2, 60, None), (1, 60, "no-such-slug-signed")],
        ids=["expired", "beyond-the-clamp", "wrong-version", "unknown-slug"],
    )
    def test_a_correctly_signed_link_that_fails_one_condition_is_the_constant_404(
        self,
        client: TestClient,
        auth_headers,
        frozen_now: int,
        version: int,
        expiry_offset: int,
        slug: str | None,
    ):
        artifact = _publish(client, auth_headers)
        target = slug or artifact["slug"]

        response = client.get(_signed_path(target, version, frozen_now + expiry_offset))

        _assert_constant_404(client, response)

    def test_a_tampered_signature_is_the_constant_404(self, client: TestClient, auth_headers, frozen_now: int):
        artifact = _publish(client, auth_headers)
        _publish_version(client, auth_headers, artifact["id"])
        expiry = frozen_now + 60
        signature = _sign(artifact["slug"], 1, expiry)
        flipped = ("0" if signature[0] != "0" else "1") + signature[1:]

        one_digit = client.get(_signed_path(artifact["slug"], 1, expiry, flipped))
        other_version = client.get(_signed_path(artifact["slug"], 2, expiry, signature))

        _assert_constant_404(client, one_digit)
        _assert_constant_404(client, other_version)

    def test_a_private_artifact_without_a_signature_is_the_constant_404(self, client: TestClient, auth_headers):
        artifact = _publish(client, auth_headers)

        _assert_constant_404(client, client.get(f"/a/{artifact['slug']}"))

    @pytest.mark.parametrize(
        "query",
        [
            {"v": "one", "e": "{expiry}", "s": "{signature}"},
            {"v": "1", "e": "soon", "s": "{signature}"},
            {"v": "1", "e": "{expiry}"},
            {"v": "1"},
            {"s": "{signature}"},
            {"v": "", "e": "", "s": ""},
        ],
        ids=["non-integer-v", "non-integer-e", "missing-s", "only-v", "only-s", "empty"],
    )
    def test_malformed_parameters_are_the_constant_404_never_422(
        self, client: TestClient, auth_headers, frozen_now: int, query: dict[str, str]
    ):
        artifact = _publish(client, auth_headers)
        expiry = frozen_now + 60
        values = {"expiry": str(expiry), "signature": _sign(artifact["slug"], 1, expiry)}
        params = {name: value.format(**values) for name, value in query.items()}

        response = client.get(f"/a/{artifact['slug']}?{urlencode(params)}")

        _assert_constant_404(client, response)

    def test_any_signed_parameter_takes_the_signed_path_even_for_an_unlisted_artifact(
        self, client: TestClient, auth_headers
    ):
        artifact = _publish(client, auth_headers)
        client.post(
            f"{ARTIFACTS_URL}/{artifact['id']}/visibility", headers=auth_headers, json={"visibility": "unlisted"}
        )

        _assert_constant_404(client, client.get(f"/a/{artifact['slug']}?s=bad"))

    def test_the_owners_bearer_token_does_not_rescue_a_bad_signature(
        self, client: TestClient, auth_headers, frozen_now: int
    ):
        artifact = _publish(client, auth_headers)

        response = client.get(_signed_path(artifact["slug"], 1, frozen_now + 60, "0" * 64), headers=auth_headers)

        _assert_constant_404(client, response)

    def test_a_link_signed_with_secret_key_is_rejected_by_a_constant_time_comparison(
        self, client: TestClient, auth_headers, frozen_now: int
    ):
        artifact = _publish(client, auth_headers)
        expiry = frozen_now + 60
        forged = _sign(artifact["slug"], 1, expiry, key=os.environ["SECRET_KEY"])

        with patch("app.services.artifact_service.hmac.compare_digest", wraps=hmac.compare_digest) as spy:
            response = client.get(_signed_path(artifact["slug"], 1, expiry, forged))

        _assert_constant_404(client, response)
        assert spy.called


class TestContent:
    def test_the_owner_gets_the_current_versions_raw_content(self, client: TestClient, auth_headers):
        artifact = _publish(client, auth_headers, "# One", "markdown")
        response = client.post(
            f"{ARTIFACTS_URL}/{artifact['id']}/versions",
            headers=auth_headers,
            json={"content_type": "markdown", "content": "# Two — ünïcode"},
        )
        assert response.status_code == status.HTTP_201_CREATED

        content = client.get(f"{ARTIFACTS_URL}/{artifact['id']}/content", headers=auth_headers)

        assert content.status_code == status.HTTP_200_OK
        assert content.json() == {"version": 2, "content_type": "markdown", "content": "# Two — ünïcode"}

    def test_another_users_artifact_and_an_unknown_id_are_not_found(
        self, client: TestClient, auth_headers, other_user_headers
    ):
        artifact = _publish(client, auth_headers)

        other = client.get(f"{ARTIFACTS_URL}/{artifact['id']}/content", headers=other_user_headers)
        unknown = client.get(f"{ARTIFACTS_URL}/999999/content", headers=auth_headers)

        assert other.status_code == unknown.status_code == status.HTTP_404_NOT_FOUND
