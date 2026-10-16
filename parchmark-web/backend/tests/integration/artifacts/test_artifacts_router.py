"""
Integration tests for the artifact endpoints: the authenticated /api/artifacts
routes and the unauthenticated public content path /a/<slug>.
"""

from datetime import timedelta

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import create_access_token
from app.models.models import User

ARTIFACTS_URL = "/api/artifacts"

PAGE = {"title": "Quarterly report", "content_type": "html", "content": "<h1>Q3</h1>\n<script>x()</script>"}
REVISION = {"content_type": "markdown", "content": "# Q3, revised"}


def _publish(client: TestClient, headers: dict[str, str], body: dict[str, str] = PAGE) -> dict:
    response = client.post(ARTIFACTS_URL, headers=headers, json=body)
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


def _set_visibility(client: TestClient, headers: dict[str, str], artifact_id: int, visibility: str) -> dict:
    response = client.post(
        f"{ARTIFACTS_URL}/{artifact_id}/visibility", headers=headers, json={"visibility": visibility}
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()


@pytest.fixture
async def other_user_headers(test_db_session: AsyncSession) -> dict[str, str]:
    """Bearer headers for a second, unrelated local user."""
    test_db_session.add(User(username="otheruser", password_hash="not-a-real-hash"))
    await test_db_session.commit()
    token = create_access_token(data={"sub": "otheruser"}, expires_delta=timedelta(minutes=30))
    return {"Authorization": f"Bearer {token}"}


class TestPublish:
    def test_publish_creates_a_private_artifact_at_version_one(self, client: TestClient, auth_headers):
        data = _publish(client, auth_headers)

        assert set(data) == {"id", "slug", "title", "visibility", "created_at", "current_version"}
        assert data["title"] == PAGE["title"]
        assert data["visibility"] == "private"
        assert len(data["slug"]) >= 22
        assert data["current_version"]["version"] == 1
        assert data["current_version"]["content_type"] == "html"
        assert "content" not in data["current_version"]

    def test_publishing_a_version_adds_the_next_number(self, client: TestClient, auth_headers):
        first = _publish(client, auth_headers)

        response = client.post(f"{ARTIFACTS_URL}/{first['id']}/versions", headers=auth_headers, json=REVISION)

        assert response.status_code == status.HTTP_201_CREATED
        second = response.json()
        assert second["id"] == first["id"]
        assert second["slug"] == first["slug"]
        assert second["current_version"]["version"] == 2
        assert second["current_version"]["content_type"] == "markdown"
        assert second["current_version"]["id"] != first["current_version"]["id"]

    @pytest.mark.parametrize(
        "body",
        [
            {"title": "T", "content_type": "pdf", "content": "x"},
            {"title": "T", "content_type": "html", "content": ""},
            {"title": "", "content_type": "html", "content": "x"},
        ],
        ids=["content-type", "empty-content", "empty-title"],
    )
    def test_invalid_artifact_is_rejected(self, client: TestClient, auth_headers, body: dict[str, str]):
        response = client.post(ARTIFACTS_URL, headers=auth_headers, json=body)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestManage:
    def test_list_returns_the_callers_artifacts_newest_first(self, client: TestClient, auth_headers):
        first = _publish(client, auth_headers)
        second = _publish(client, auth_headers, {**PAGE, "title": "Second"})

        response = client.get(ARTIFACTS_URL, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        assert [a["id"] for a in response.json()] == [second["id"], first["id"]]

    def test_get_returns_metadata_and_the_current_version(self, client: TestClient, auth_headers):
        artifact = _publish(client, auth_headers)
        updated = client.post(f"{ARTIFACTS_URL}/{artifact['id']}/versions", headers=auth_headers, json=REVISION).json()

        response = client.get(f"{ARTIFACTS_URL}/{artifact['id']}", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == updated

    def test_set_visibility_switches_between_private_and_unlisted(self, client: TestClient, auth_headers):
        artifact = _publish(client, auth_headers)

        assert _set_visibility(client, auth_headers, artifact["id"], "unlisted")["visibility"] == "unlisted"
        assert _set_visibility(client, auth_headers, artifact["id"], "private")["visibility"] == "private"

    def test_set_visibility_rejects_other_values(self, client: TestClient, auth_headers):
        artifact = _publish(client, auth_headers)

        response = client.post(
            f"{ARTIFACTS_URL}/{artifact['id']}/visibility", headers=auth_headers, json={"visibility": "public"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_delete_removes_the_artifact(self, client: TestClient, auth_headers):
        artifact = _publish(client, auth_headers)
        _set_visibility(client, auth_headers, artifact["id"], "unlisted")

        response = client.delete(f"{ARTIFACTS_URL}/{artifact['id']}", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["deleted_id"] == str(artifact["id"])
        assert client.get(f"{ARTIFACTS_URL}/{artifact['id']}", headers=auth_headers).status_code == 404
        assert client.get(f"/a/{artifact['slug']}").status_code == 404
        assert client.get(ARTIFACTS_URL, headers=auth_headers).json() == []

    def test_missing_artifact_is_not_found(self, client: TestClient, auth_headers):
        response = client.get(f"{ARTIFACTS_URL}/999999", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAccess:
    @pytest.mark.parametrize(
        ("method", "path", "body"),
        [
            ("POST", "", PAGE),
            ("GET", "", None),
            ("GET", "/1", None),
            ("POST", "/1/versions", REVISION),
            ("POST", "/1/visibility", {"visibility": "unlisted"}),
            ("DELETE", "/1", None),
        ],
        ids=["publish", "list", "get", "publish-version", "set-visibility", "delete"],
    )
    def test_requires_authentication(self, client: TestClient, method: str, path: str, body: dict | None):
        response = client.request(method, f"{ARTIFACTS_URL}{path}", json=body)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        ("method", "path", "body"),
        [
            ("GET", "", None),
            ("POST", "/versions", REVISION),
            ("POST", "/visibility", {"visibility": "unlisted"}),
            ("DELETE", "", None),
        ],
        ids=["get", "publish-version", "set-visibility", "delete"],
    )
    def test_another_users_artifact_is_not_found(
        self, client: TestClient, auth_headers, other_user_headers, method: str, path: str, body: dict | None
    ):
        artifact = _publish(client, auth_headers)

        response = client.request(
            method, f"{ARTIFACTS_URL}/{artifact['id']}{path}", headers=other_user_headers, json=body
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert client.get(ARTIFACTS_URL, headers=other_user_headers).json() == []
        owned = client.get(f"{ARTIFACTS_URL}/{artifact['id']}", headers=auth_headers).json()
        assert owned == artifact  # unchanged: still private, still version 1


class TestPublicContent:
    def test_unlisted_artifact_is_readable_without_authentication(self, client: TestClient, auth_headers):
        artifact = _publish(client, auth_headers)
        _set_visibility(client, auth_headers, artifact["id"], "unlisted")

        response = client.get(f"/a/{artifact['slug']}")

        assert response.status_code == status.HTTP_200_OK
        assert response.text == PAGE["content"]
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert response.headers["x-content-type-options"] == "nosniff"

    def test_private_artifact_is_not_readable(self, client: TestClient, auth_headers):
        artifact = _publish(client, auth_headers)

        assert client.get(f"/a/{artifact['slug']}").status_code == status.HTTP_404_NOT_FOUND
        # Not even with the owner's credentials: the public path never reads private artifacts.
        assert client.get(f"/a/{artifact['slug']}", headers=auth_headers).status_code == status.HTTP_404_NOT_FOUND

    def test_making_an_artifact_private_again_hides_it(self, client: TestClient, auth_headers):
        artifact = _publish(client, auth_headers)
        _set_visibility(client, auth_headers, artifact["id"], "unlisted")
        _set_visibility(client, auth_headers, artifact["id"], "private")

        assert client.get(f"/a/{artifact['slug']}").status_code == status.HTTP_404_NOT_FOUND

    def test_serves_the_current_version(self, client: TestClient, auth_headers):
        artifact = _publish(client, auth_headers)
        _set_visibility(client, auth_headers, artifact["id"], "unlisted")
        client.post(f"{ARTIFACTS_URL}/{artifact['id']}/versions", headers=auth_headers, json=REVISION)

        assert client.get(f"/a/{artifact['slug']}").text == REVISION["content"]

    def test_unknown_slug_is_not_found(self, client: TestClient):
        assert client.get("/a/no-such-slug").status_code == status.HTTP_404_NOT_FOUND
