"""
Integration tests for F13: Delete GET /api/notes/{id}/similar endpoint.

Contract: /features/1/contract
  - route: /api/notes/{note_id}/similar
  - method: GET
  - endpoint_status: removed
  - response_for_removed_route: 404
  - deleted_test_file: backend/tests/integration/notes/test_similarity.py

These tests are RED today (endpoint still exists) and go GREEN after the
implementer deletes the route and test_similarity.py.
"""

from pathlib import Path

from fastapi import status
from fastapi.testclient import TestClient


class TestSimilarEndpointGone:
    """
    Oracle: /features/1/oracle/assertions/0
    "GET on `/api/notes/{note_id}/similar` for any authenticated user returns HTTP 404."
    """

    def test_get_similar_returns_404_for_authenticated_request(self, client: TestClient, auth_headers, sample_note):
        """GET /api/notes/{note_id}/similar with valid auth returns 404 (no matching route)."""
        response = client.get(f"/api/notes/{sample_note.id}/similar", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_similar_trailing_slash_returns_404(self, client: TestClient, auth_headers, sample_note):
        """
        GET /api/notes/{note_id}/similar/ (trailing slash) returns 404.

        Oracle: /features/1/oracle/assertions/0 (amended constraint: explicit
        trailing-slash assertion per roundtable Attempt 2).

        Starlette's redirect_slashes=True default would 307-redirect to
        the canonical URL, but that canonical URL must also 404 once the
        route is deleted.  TestClient follows redirects by default; assert
        the final resolved status is 404.
        """
        response = client.get(f"/api/notes/{sample_note.id}/similar/", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRouterSourceContainsNoSimilarPath:
    """
    Oracle: /features/1/oracle/assertions/1
    "grep of `backend/app/routers/notes.py` for `/similar` returns zero matches."
    """

    def test_routers_notes_has_no_similar_route_string(self):
        """The literal string '/similar' must not appear anywhere in routers/notes.py."""
        router_file = Path(__file__).parents[3] / "app" / "routers" / "notes.py"
        assert router_file.exists(), f"Router file not found at {router_file}"

        source = router_file.read_text(encoding="utf-8")
        matches = [
            (lineno, line.rstrip()) for lineno, line in enumerate(source.splitlines(), start=1) if "/similar" in line
        ]

        assert matches == [], (
            f"Expected zero occurrences of '/similar' in {router_file}, "
            f"but found {len(matches)} match(es):\n" + "\n".join(f"  line {lineno}: {line}" for lineno, line in matches)
        )


class TestSimilarityTestFileDeleted:
    """
    Oracle: /features/1/oracle/assertions/2
    "File `backend/tests/integration/notes/test_similarity.py` does not exist."
    """

    def test_test_similarity_file_does_not_exist(self):
        """backend/tests/integration/notes/test_similarity.py must have been deleted."""
        similarity_test = Path(__file__).parent / "test_similarity.py"

        assert not similarity_test.exists(), (
            f"Expected {similarity_test} to be deleted as part of F13, " "but it still exists."
        )


# ---------------------------------------------------------------------------
# F14: Delete POST /api/notes/{id}/access endpoint
# ---------------------------------------------------------------------------


class TestAccessEndpointGone:
    """
    Oracle: /features/2/oracle/assertions/0
    "POST on `/api/notes/{note_id}/access` for any authenticated user returns HTTP 404."
    """

    def test_post_access_returns_404_for_authenticated_request(self, client: TestClient, auth_headers, sample_note):
        """POST /api/notes/{note_id}/access with valid auth returns 404 (no matching route)."""
        response = client.post(f"/api/notes/{sample_note.id}/access", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_post_access_trailing_slash_returns_404(self, client: TestClient, auth_headers, sample_note):
        """
        POST /api/notes/{note_id}/access/ (trailing slash) returns 404.

        Oracle: /features/2/oracle/assertions/0 (sibling assertion: explicit
        trailing-slash parity per execution brief, mirroring F13's amended constraint).

        Starlette's redirect_slashes=True default would 307-redirect to the
        canonical URL, but that canonical URL must also 404 once the route is
        deleted.  TestClient follows redirects by default; assert the final
        resolved status is 404.
        """
        response = client.post(f"/api/notes/{sample_note.id}/access/", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRouterSourceContainsNoAccessRouteString:
    """
    Oracle: /features/2/oracle/assertions/1
    "grep of `backend/app/routers/notes.py` for `/access` returns zero matches."

    NOTE: match on the quoted-slash pattern '"/access"' (or the full decorator
    literal) — NOT on the bare word 'access'. F19 removed access_count and
    last_accessed_at from _note_to_response; no false-positive risk from those
    fields remains after F19.
    """

    def test_routers_notes_has_no_access_route_string(self):
        """The route-segment literal '/access' (with leading slash inside quotes) must not appear in routers/notes.py."""
        router_file = Path(__file__).parents[3] / "app" / "routers" / "notes.py"
        assert router_file.exists(), f"Router file not found at {router_file}"

        source = router_file.read_text(encoding="utf-8")
        # Match the route-path literal as it would appear in a decorator:
        # '"/access"' or '"/{note_id}/access"'.
        matches = [
            (lineno, line.rstrip())
            for lineno, line in enumerate(source.splitlines(), start=1)
            if '"/access"' in line or '"/{note_id}/access"' in line
        ]

        assert matches == [], (
            f"Expected zero occurrences of the '/access' route literal in {router_file}, "
            f"but found {len(matches)} match(es):\n" + "\n".join(f"  line {lineno}: {line}" for lineno, line in matches)
        )


class TestAccessTrackingTestFileDeleted:
    """
    Oracle: /features/2/oracle/assertions/2
    "File `backend/tests/integration/notes/test_access_tracking.py` does not exist."
    """

    def test_test_access_tracking_file_does_not_exist(self):
        """backend/tests/integration/notes/test_access_tracking.py must have been deleted."""
        access_tracking_test = Path(__file__).parent / "test_access_tracking.py"

        assert not access_tracking_test.exists(), (
            f"Expected {access_tracking_test} to be deleted as part of F14, " "but it still exists."
        )
