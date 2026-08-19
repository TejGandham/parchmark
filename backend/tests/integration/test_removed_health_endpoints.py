"""
Integration tests for the removal of three zero-consumer routes:

  - GET /api/auth/health   (auth_health_check, backend/app/routers/auth.py)
  - GET /api/notes/health/check (notes_health_check, backend/app/routers/notes.py)
  - GET /             (root, backend/app/main.py)

Follows the F13 precedent in backend/tests/integration/notes/test_endpoint_removal.py:
for each removed route, a 404-assertion class (plus trailing-slash variant) and a
router/app-source-literal-absence class. Placed as a sibling file rather than inside
notes/test_endpoint_removal.py because two of the three routes are owned by
app/routers/auth.py and app/main.py, not app/routers/notes.py.

These three routes were unauthenticated (public) before removal, so no auth_headers
fixture is needed here.
"""

from pathlib import Path

from fastapi import status
from fastapi.testclient import TestClient


class TestAuthHealthEndpointGone:
    """GET /api/auth/health no longer resolves to a route."""

    def test_get_auth_health_returns_404(self, client: TestClient):
        response = client.get("/api/auth/health")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_auth_health_trailing_slash_returns_404(self, client: TestClient):
        """TestClient follows redirects by default; the resolved status must still be 404."""
        response = client.get("/api/auth/health/")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestNotesHealthCheckEndpointGone:
    """GET /api/notes/health/check no longer resolves to a route."""

    def test_get_notes_health_check_returns_404(self, client: TestClient):
        response = client.get("/api/notes/health/check")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_notes_health_check_trailing_slash_returns_404(self, client: TestClient):
        """TestClient follows redirects by default; the resolved status must still be 404."""
        response = client.get("/api/notes/health/check/")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRootEndpointGone:
    """GET / no longer resolves to a route."""

    def test_get_root_returns_404(self, client: TestClient):
        response = client.get("/")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRouterSourceContainsNoAuthHealthRouteString:
    """The literal route path '/health' must not appear as a decorator in routers/auth.py."""

    def test_routers_auth_has_no_health_route_string(self):
        router_file = Path(__file__).parents[2] / "app" / "routers" / "auth.py"
        assert router_file.exists(), f"Router file not found at {router_file}"

        source = router_file.read_text(encoding="utf-8")
        matches = [
            (lineno, line.rstrip()) for lineno, line in enumerate(source.splitlines(), start=1) if '"/health"' in line
        ]

        assert matches == [], (
            f"Expected zero occurrences of the '/health' route literal in {router_file}, "
            f"but found {len(matches)} match(es):\n" + "\n".join(f"  line {lineno}: {line}" for lineno, line in matches)
        )


class TestRouterSourceContainsNoNotesHealthCheckRouteString:
    """The literal route path '/health/check' must not appear as a decorator in routers/notes.py."""

    def test_routers_notes_has_no_health_check_route_string(self):
        router_file = Path(__file__).parents[2] / "app" / "routers" / "notes.py"
        assert router_file.exists(), f"Router file not found at {router_file}"

        source = router_file.read_text(encoding="utf-8")
        matches = [
            (lineno, line.rstrip())
            for lineno, line in enumerate(source.splitlines(), start=1)
            if "/health/check" in line
        ]

        assert matches == [], (
            f"Expected zero occurrences of '/health/check' in {router_file}, "
            f"but found {len(matches)} match(es):\n" + "\n".join(f"  line {lineno}: {line}" for lineno, line in matches)
        )


class TestMainSourceContainsNoRootRouteString:
    """The literal root-route decorator '@app.get("/", ...)' must not appear in app/main.py."""

    def test_main_has_no_root_route_decorator(self):
        main_file = Path(__file__).parents[2] / "app" / "main.py"
        assert main_file.exists(), f"App entrypoint not found at {main_file}"

        source = main_file.read_text(encoding="utf-8")
        matches = [
            (lineno, line.rstrip())
            for lineno, line in enumerate(source.splitlines(), start=1)
            if '@app.get("/"' in line or "@app.get('/'" in line
        ]

        assert matches == [], (
            f"Expected zero occurrences of the root route decorator in {main_file}, "
            f"but found {len(matches)} match(es):\n" + "\n".join(f"  line {lineno}: {line}" for lineno, line in matches)
        )
