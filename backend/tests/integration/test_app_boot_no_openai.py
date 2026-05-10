"""
Integration tests for F15: Delete embeddings + backfill services and OpenAI lifespan wiring.

Oracle: /features/3/oracle (type: integration)
Contract: /features/3/contract

These tests verify the post-deletion state. They FAIL until the implementer
removes the files named in contract.deleted_files and strips OpenAI wiring
from backend/app/main.py.
"""

import re
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Repo root is 3 levels up from this file (backend/tests/integration/)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_BACKEND_APP = _REPO_ROOT / "backend" / "app"


# ---------------------------------------------------------------------------
# /features/3/oracle/assertions/0 — embeddings.py and backfill.py absent
# /features/3/oracle/assertions/1 — test_embeddings.py absent
# /features/3/oracle/assertions/2 (amended) — test_backfill.py absent
# ---------------------------------------------------------------------------

_DELETED_FILES = [
    "backend/app/services/embeddings.py",
    "backend/app/services/backfill.py",
    "backend/tests/unit/services/test_embeddings.py",
    "backend/tests/unit/services/test_backfill.py",
]


@pytest.mark.parametrize("rel_path", _DELETED_FILES)
def test_contract_file_is_absent(rel_path: str) -> None:
    """
    Asserts each path listed in contract.deleted_files does not exist on disk.

    Covers oracle assertions 0, 1, 2 (amended):
      /features/3/oracle/assertions/0 — embeddings.py and backfill.py
      /features/3/oracle/assertions/1 — test_embeddings.py
      /features/3/oracle/assertions/2 — test_backfill.py
    """
    target = _REPO_ROOT / rel_path
    assert not target.exists(), (
        f"Contract violation: {rel_path} must be deleted (contract.deleted_files) " f"but still exists at {target}"
    )


# ---------------------------------------------------------------------------
# /features/3/oracle/assertions/3
# ripgrep `^(from|import) openai` across backend/app/ returns zero matches
# ---------------------------------------------------------------------------


def _grep_openai_imports(app_dir: Path) -> list[str]:
    """Return lines matching ^(from|import) openai under app_dir using rg or re fallback."""
    try:
        result = subprocess.run(
            ["rg", "--no-heading", "-n", r"^(from|import) openai", str(app_dir)],
            capture_output=True,
            text=True,
        )
        # rg exits 0 on match, 1 on no match, 2 on error
        if result.returncode == 2:
            raise FileNotFoundError("rg error")
        return result.stdout.splitlines()
    except FileNotFoundError:
        # Fallback: pure-Python regex walk
        pattern = re.compile(r"^(from|import) openai", re.MULTILINE)
        hits: list[str] = []
        for py_file in app_dir.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            for m in pattern.finditer(text):
                line_no = text[: m.start()].count("\n") + 1
                hits.append(f"{py_file}:{line_no}:{m.group()}")
        return hits


def test_no_openai_imports_in_app_tree() -> None:
    """
    oracle assertion 3 (/features/3/oracle/assertions/3):
    ripgrep `^(from|import) openai` across backend/app/ returns zero matches.
    """
    hits = _grep_openai_imports(_BACKEND_APP)
    assert hits == [], (
        "Found openai import(s) in backend/app/ — contract.openai_imports_in_app_tree must be 'absent':\n"
        + "\n".join(hits)
    )


# ---------------------------------------------------------------------------
# /features/3/oracle/assertions/4
# ripgrep `app.state.openai_client` across backend/app/ returns zero matches
# ---------------------------------------------------------------------------


def _grep_openai_client_refs(app_dir: Path) -> list[str]:
    """Return lines matching app.state.openai_client under app_dir using rg or re fallback."""
    pattern_str = r"app\.state\.openai_client"
    try:
        result = subprocess.run(
            ["rg", "--no-heading", "-n", pattern_str, str(app_dir)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 2:
            raise FileNotFoundError("rg error")
        return result.stdout.splitlines()
    except FileNotFoundError:
        pattern = re.compile(pattern_str)
        hits: list[str] = []
        for py_file in app_dir.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            for m in pattern.finditer(text):
                line_no = text[: m.start()].count("\n") + 1
                hits.append(f"{py_file}:{line_no}:{m.group()}")
        return hits


def test_no_app_state_openai_client_refs() -> None:
    """
    oracle assertion 4 (/features/3/oracle/assertions/4):
    ripgrep `app.state.openai_client` across backend/app/ returns zero matches.
    """
    hits = _grep_openai_client_refs(_BACKEND_APP)
    assert hits == [], (
        "Found app.state.openai_client reference(s) in backend/app/ — "
        "contract.app_state_openai_client must be 'absent':\n" + "\n".join(hits)
    )


# ---------------------------------------------------------------------------
# /features/3/oracle/assertions/5
# FastAPI app boots successfully via the existing lifespan with OPENAI_API_KEY unset
# ---------------------------------------------------------------------------


def test_app_boots_without_openai_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    oracle assertion 5 (/features/3/oracle/assertions/5):
    FastAPI app boots successfully via the existing lifespan with OPENAI_API_KEY unset.

    Uses monkeypatch to ensure OPENAI_API_KEY is absent from os.environ, then
    instantiates the TestClient (which exercises the lifespan context manager)
    with init_database mocked out (same pattern as conftest.py `client` fixture).
    """
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from app.main import app

    with patch("app.main.init_database", return_value=True):
        with TestClient(app) as test_client:
            response = test_client.get("/api/health")
            # A 200 or any non-500 startup-failure code confirms boot succeeded.
            # /api/health may return 503 if DB is not available in this context;
            # what we care about is that the lifespan did NOT raise on startup.
            assert response.status_code != 500, (
                f"App failed to boot: /api/health returned {response.status_code}. "
                "OpenAI lifespan wiring may still be present."
            )
