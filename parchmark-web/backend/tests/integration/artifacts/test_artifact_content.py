"""
Integration tests for the public artifact content route /a/<slug>, the only route
the content origin serves: raw bytes under a sandboxing Content-Security-Policy,
with a media type per content type, no cookies, and one constant 404.
"""

from collections.abc import Iterator, Sequence

import pytest
from fastapi import status
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from httpx import Response

from app.main import app
from app.routers import artifacts

ARTIFACTS_URL = "/api/artifacts"

# Every document tries to run a script; only HTML is allowed to.
DOCUMENTS = {
    "html": "<h1>Q3</h1>\n<script>document.title = 'ran'</script>",
    "svg": '<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script><circle r="4"/></svg>',
    "markdown": "# Q3 — ünïcode\n\n<script>alert(1)</script>",
}
MEDIA_TYPES = {
    "html": "text/html; charset=utf-8",
    "svg": "image/svg+xml; charset=utf-8",
    "markdown": "text/plain; charset=utf-8",
}
BASE_POLICY = (
    "default-src 'none'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; "
    "base-uri 'none'; form-action 'none'"
)
POLICY_ADDITIONS = {
    "html": "script-src 'unsafe-inline'; sandbox allow-scripts",
    "svg": "sandbox",
    "markdown": "sandbox",
}
COMMON_HEADERS = {
    "x-content-type-options": "nosniff",
    "referrer-policy": "no-referrer",
    "cache-control": "no-store",
}


def _publish(client: TestClient, headers: dict[str, str], content_type: str) -> dict:
    body = {"title": "Report", "content_type": content_type, "content": DOCUMENTS[content_type]}
    response = client.post(ARTIFACTS_URL, headers=headers, json=body)
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


def _read_unlisted(
    client: TestClient, headers: dict[str, str], content_type: str, read_headers: dict[str, str] | None = None
) -> Response:
    """Publish a document of this type, make it unlisted, and read it back over /a/<slug> with read_headers."""
    artifact = _publish(client, headers, content_type)
    visibility = {"visibility": "unlisted"}
    client.post(f"{ARTIFACTS_URL}/{artifact['id']}/visibility", headers=headers, json=visibility)
    response = client.get(f"/a/{artifact['slug']}", headers=read_headers)
    assert response.status_code == status.HTTP_200_OK
    return response


def _policy(response: Response) -> dict[str, list[str]]:
    """Parse the Content-Security-Policy header into {directive: [values]}."""
    directives = (d.split() for d in response.headers["content-security-policy"].split(";") if d.strip())
    return {name: values for name, *values in directives}


def _api_routes(routes: Sequence[object], prefix: str = "") -> Iterator[tuple[str, APIRoute]]:
    """Yield (full path, route) for every API route, descending into routers FastAPI includes lazily."""
    for route in routes:
        included = getattr(route, "original_router", None)
        if included is not None:
            yield from _api_routes(included.routes, prefix + route.include_context.prefix)  # type: ignore[attr-defined]
        elif isinstance(route, APIRoute):
            yield prefix + route.path, route


def test_the_content_route_is_served_only_by_the_artifact_content_module():
    assert not hasattr(artifacts, "content_router")
    routes = [route for path, route in _api_routes(app.routes) if path == "/a/{slug}"]
    assert len(routes) == 1
    assert routes[0].endpoint.__module__ == "app.routers.artifact_content"


@pytest.mark.parametrize("content_type", list(DOCUMENTS))
def test_serves_the_raw_bytes_with_the_media_type_of_its_content_type(
    client: TestClient, auth_headers, content_type: str
):
    response = _read_unlisted(client, auth_headers, content_type)

    assert response.content == DOCUMENTS[content_type].encode()
    assert response.headers["content-type"] == MEDIA_TYPES[content_type]
    for name, value in COMMON_HEADERS.items():
        assert response.headers[name] == value
    assert "set-cookie" not in response.headers


@pytest.mark.parametrize("content_type", list(DOCUMENTS))
def test_the_policy_is_the_base_policy_plus_the_types_addition(client: TestClient, auth_headers, content_type: str):
    response = _read_unlisted(client, auth_headers, content_type)

    assert response.headers["content-security-policy"] == f"{BASE_POLICY}; {POLICY_ADDITIONS[content_type]}"
    assert "frame-ancestors" not in response.headers["content-security-policy"]
    policy = _policy(response)
    # The sandbox directive gives the document an opaque origin even when opened directly.
    assert "allow-same-origin" not in policy["sandbox"]


def test_only_html_may_run_scripts(client: TestClient, auth_headers):
    html = _policy(_read_unlisted(client, auth_headers, "html"))

    assert html["script-src"] == ["'unsafe-inline'"]
    assert html["sandbox"] == ["allow-scripts"]


@pytest.mark.parametrize("content_type", ["svg", "markdown"])
def test_svg_and_markdown_run_no_scripts(client: TestClient, auth_headers, content_type: str):
    policy = _policy(_read_unlisted(client, auth_headers, content_type))

    assert "script-src" not in policy  # falls back to default-src 'none'
    assert policy["sandbox"] == []  # no tokens: scripts, forms, popups and navigation are all blocked


def test_sends_no_cookies_and_ignores_the_ones_it_receives(client: TestClient, auth_headers):
    response = _read_unlisted(client, auth_headers, "html", {**auth_headers, "Cookie": "session=app-session"})

    assert "set-cookie" not in response.headers
    assert not response.cookies
    assert response.headers["referrer-policy"] == "no-referrer"


@pytest.mark.parametrize("content_type", list(DOCUMENTS))
def test_head_answers_like_get_without_a_body(client: TestClient, auth_headers, content_type: str):
    get = _read_unlisted(client, auth_headers, content_type)
    slug = get.url.path.removeprefix("/a/")

    head = client.head(f"/a/{slug}")

    assert head.status_code == status.HTTP_200_OK
    assert dict(head.headers) == dict(get.headers)
    assert head.content == b""


class TestNotFound:
    def test_private_and_unknown_slugs_get_the_same_constant_404(self, client: TestClient, auth_headers):
        private = _publish(client, auth_headers, "html")

        for_private = client.get(f"/a/{private['slug']}")
        for_unknown = client.get("/a/no-such-slug?reason=1")

        assert for_private.status_code == for_unknown.status_code == status.HTTP_404_NOT_FOUND
        assert dict(for_private.headers) == dict(for_unknown.headers)
        assert for_private.content == for_unknown.content == b"Not found"
        assert for_private.headers["content-type"] == "text/plain; charset=utf-8"
        for name, value in COMMON_HEADERS.items():
            assert for_private.headers[name] == value
        assert "set-cookie" not in for_private.headers
        assert private["slug"].encode() not in for_private.content

    def test_the_owners_bearer_token_does_not_reveal_a_private_artifact(self, client: TestClient, auth_headers):
        private = _publish(client, auth_headers, "html")

        anonymous = client.get(f"/a/{private['slug']}")
        as_owner = client.get(f"/a/{private['slug']}", headers=auth_headers)

        assert as_owner.status_code == status.HTTP_404_NOT_FOUND
        assert dict(as_owner.headers) == dict(anonymous.headers)
        assert as_owner.content == anonymous.content

    def test_head_on_private_and_unknown_slugs_is_the_get_404_without_a_body(self, client: TestClient, auth_headers):
        private = _publish(client, auth_headers, "html")
        get_unknown = client.get("/a/no-such-slug")

        head_private = client.head(f"/a/{private['slug']}")
        head_unknown = client.head("/a/no-such-slug")
        head_as_owner = client.head(f"/a/{private['slug']}", headers=auth_headers)

        for head in (head_private, head_unknown, head_as_owner):
            assert head.status_code == status.HTTP_404_NOT_FOUND
            assert dict(head.headers) == dict(get_unknown.headers)
            assert head.content == b""
