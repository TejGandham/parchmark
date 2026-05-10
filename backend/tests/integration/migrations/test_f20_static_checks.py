"""
Static-check tests for F20: Drop openai and pgvector dependencies.

Oracle: /features/8/oracle
Contract: /features/8/contract

Assertions covered here:
  /features/8/oracle/assertions/0  — pyproject.toml [project].dependencies has no openai/pgvector.
  /features/8/oracle/assertions/4  — no module-level openai/pgvector imports across backend/
                                     (excluding .venv and test_f19_*.py).
  /features/8/oracle/assertions/5  — no `from pgvector` or `Vector(` in migrations/versions/.
  /features/8/oracle/assertions/6  — no pgvector/pgvector:pg17 image string in docker-compose*.yml.

Assertions NOT in this file (rationale documented in the test-writer decisions):
  /features/8/oracle/assertions/1  — `uv sync` success: manual implementer step, not a unit test.
  /features/8/oracle/assertions/2  — `alembic history` without pgvector: CI gate / subprocess
                                     check. The assertion is verified by the fact that
                                     test_f20_brownfield_rewrites.py imports alembic and invokes
                                     command.upgrade() in a venv where pgvector is absent after
                                     F20 lands. Explicit subprocess isolation is not required
                                     because the integration tests already run in that venv.
  /features/8/oracle/assertions/3  — `make test-backend-all` full suite: CI meta-gate, not a
                                     unit test. Implicitly verified by the whole test run.
  /features/8/oracle/assertions/7  — CRUD against postgres:17: covered implicitly by the
                                     conftest.py image swap + the existing CRUD test suite.
                                     The conftest swap is the implementer change; no new test needed.

All checks use pure-Python ripgrep alternatives (re + Path.read_text) — consistent with
the _file_matches() helper in test_f19_drop_embedding.py.
"""

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Root paths
# ---------------------------------------------------------------------------
_BACKEND_ROOT = Path(__file__).parents[3]  # backend/
_REPO_ROOT = _BACKEND_ROOT.parent  # repo root (for compose files)
_PYPROJECT_TOML = _BACKEND_ROOT / "pyproject.toml"
_MIGRATIONS_VERSIONS_DIR = _BACKEND_ROOT / "migrations" / "versions"

# The F19 round-trip test file intentionally retains pgvector/pgvector:pg17.
# It is excluded from assertion-4 and assertion-6 scans per contract
# /features/8/contract/test_f19_image_unchanged and F21's
# acceptable_residual_locations.
_F19_TEST_FILE = _BACKEND_ROOT / "tests" / "integration" / "migrations" / "test_f19_drop_embedding.py"


def _lines_matching(path: Path, *patterns: str) -> list[tuple[int, str]]:
    """Return (line_number, line_text) for every line matching any pattern."""
    rxs = [re.compile(p) for p in patterns]
    result: list[tuple[int, str]] = []
    for i, line in enumerate(path.read_text().splitlines(), start=1):
        if any(rx.search(line) for rx in rxs):
            result.append((i, line))
    return result


# ---------------------------------------------------------------------------
# /features/8/oracle/assertions/0
# pyproject.toml [project].dependencies has no openai or pgvector entries.
# ---------------------------------------------------------------------------


class TestPyprojectDependenciesClean:
    """
    Oracle: /features/8/oracle/assertions/0
    Contract: /features/8/contract/pyproject_toml_dependencies_removed ==
              ["openai>=1.0.0", "pgvector>=0.4.2"]
    """

    def test_openai_not_in_project_dependencies(self):
        """
        [project].dependencies in pyproject.toml must not contain 'openai'.
        Only scans the [project] dependencies block — not [tool.*] sections.
        """
        assert _PYPROJECT_TOML.exists(), f"pyproject.toml not found at {_PYPROJECT_TOML}"

        in_deps_block = False
        hits: list[tuple[int, str]] = []
        for i, line in enumerate(_PYPROJECT_TOML.read_text().splitlines(), start=1):
            stripped = line.strip()
            if stripped == "[project]":
                in_deps_block = True
                continue
            # Exit the block on any new section header.
            if in_deps_block and stripped.startswith("[") and stripped != "[project]":
                in_deps_block = False
            if in_deps_block and re.search(r"\bopenai\b", line):
                hits.append((i, line))

        assert hits == [], (
            f"Found 'openai' in [project] dependencies block of {_PYPROJECT_TOML}: {hits}. "
            "Remove 'openai>=1.0.0' per F20 contract."
        )

    def test_pgvector_not_in_project_dependencies(self):
        """
        [project].dependencies in pyproject.toml must not contain 'pgvector'.
        """
        assert _PYPROJECT_TOML.exists(), f"pyproject.toml not found at {_PYPROJECT_TOML}"

        in_deps_block = False
        hits: list[tuple[int, str]] = []
        for i, line in enumerate(_PYPROJECT_TOML.read_text().splitlines(), start=1):
            stripped = line.strip()
            if stripped == "[project]":
                in_deps_block = True
                continue
            if in_deps_block and stripped.startswith("[") and stripped != "[project]":
                in_deps_block = False
            if in_deps_block and re.search(r"\bpgvector\b", line):
                hits.append((i, line))

        assert hits == [], (
            f"Found 'pgvector' in [project] dependencies block of {_PYPROJECT_TOML}: {hits}. "
            "Remove 'pgvector>=0.4.2' per F20 contract."
        )


# ---------------------------------------------------------------------------
# /features/8/oracle/assertions/4
# No module-level openai/pgvector imports across backend/ (excl. .venv and test_f19_*.py).
# Pattern: ^(from|import) (openai|pgvector)
# ---------------------------------------------------------------------------


class TestNoModuleLevelOpenaiPgvectorImports:
    """
    Oracle: /features/8/oracle/assertions/4
    Contract: /features/8/contract/migrations_rewritten (imports removed from both files)
    """

    def test_no_module_level_openai_or_pgvector_imports_in_backend(self):
        """
        ripgrep ^(from|import) (openai|pgvector) across backend/ excluding .venv
        and tests/integration/migrations/test_f19_*.py must return zero matches.
        """
        pattern = re.compile(r"^(from|import) (openai|pgvector)")
        hits: list[tuple[Path, int, str]] = []

        for py_file in _BACKEND_ROOT.rglob("*.py"):
            # Exclude virtualenv.
            if ".venv" in py_file.parts:
                continue
            # Exclude F19 round-trip test (intentional residual per contract).
            if py_file == _F19_TEST_FILE:
                continue
            for i, line in enumerate(py_file.read_text().splitlines(), start=1):
                if pattern.match(line):
                    hits.append((py_file, i, line))

        assert hits == [], (
            "Found module-level 'openai' or 'pgvector' imports in backend/ "
            "(excluding .venv and test_f19_drop_embedding.py):\n"
            + "\n".join(f"  {p}:{i}: {line}" for p, i, line in hits)
        )


# ---------------------------------------------------------------------------
# /features/8/oracle/assertions/5
# No `from pgvector` or `Vector(` in backend/migrations/versions/.
# ---------------------------------------------------------------------------


class TestNoVectorImportInMigrationVersions:
    """
    Oracle: /features/8/oracle/assertions/5
    Contract: /features/8/contract/migrations_rewritten
              Both 49f4bec52ca3 and 7f1c343772e8 must have module-level
              `from pgvector.sqlalchemy import Vector` removed and no Vector(
              call sites remaining.
    """

    def test_no_from_pgvector_or_vector_call_in_migration_versions(self):
        """
        rg -n "from pgvector|Vector\\(" backend/migrations/versions/ must return
        zero matches. Descriptive title strings like 'drop embedding columns and
        pgvector' in docstrings are permitted by the narrow pattern.
        """
        assert _MIGRATIONS_VERSIONS_DIR.exists(), f"migrations/versions/ not found at {_MIGRATIONS_VERSIONS_DIR}"
        pattern = re.compile(r"from pgvector|Vector\(")
        hits: list[tuple[Path, int, str]] = []

        for py_file in _MIGRATIONS_VERSIONS_DIR.glob("*.py"):
            for i, line in enumerate(py_file.read_text().splitlines(), start=1):
                if pattern.search(line):
                    hits.append((py_file, i, line))

        assert hits == [], (
            "Found 'from pgvector' or 'Vector(' in backend/migrations/versions/:\n"
            + "\n".join(f"  {p.name}:{i}: {line}" for p, i, line in hits)
            + "\nRemove `from pgvector.sqlalchemy import Vector` and replace Vector(1536) "
            "call sites with raw DDL per F20 contract."
        )


# ---------------------------------------------------------------------------
# /features/8/oracle/assertions/6
# No pgvector/pgvector:pg17 image string in docker-compose*.yml (repo root only).
# The F19 round-trip test file is NOT a compose file — it is excluded by scope.
# ---------------------------------------------------------------------------


class TestNoDockerComposePgvectorImage:
    """
    Oracle: /features/8/oracle/assertions/6
    Contract: /features/8/contract/docker_compose_image_swaps ==
              [docker-compose.dev.yml, docker-compose.yml,
               docker-compose.prod.yml, docker-compose.oidc-test.yml]
    """

    def test_no_pgvector_image_in_docker_compose_files(self):
        """
        rg -n "pgvector/pgvector:pg17" docker-compose*.yml (repo root) must return
        zero matches.

        Note: backend/tests/integration/migrations/test_f19_drop_embedding.py
        legitimately retains the string PostgresContainer("pgvector/pgvector:pg17")
        but is NOT a docker-compose*.yml file and is therefore outside this check's
        scope. That residual is whitelisted in F21's acceptable_residual_locations.
        """
        compose_files = list(_REPO_ROOT.glob("docker-compose*.yml"))
        assert compose_files, (
            f"No docker-compose*.yml files found at repo root {_REPO_ROOT}. "
            "Check that _REPO_ROOT resolves to the project root."
        )

        pattern = re.compile(r"pgvector/pgvector:pg17")
        hits: list[tuple[Path, int, str]] = []

        for compose_file in compose_files:
            for i, line in enumerate(compose_file.read_text().splitlines(), start=1):
                if pattern.search(line):
                    hits.append((compose_file, i, line))

        assert hits == [], (
            "Found 'pgvector/pgvector:pg17' image reference in docker-compose*.yml files:\n"
            + "\n".join(f"  {p.name}:{i}: {line}" for p, i, line in hits)
            + "\nSwap to 'postgres:17' per F20 contract."
        )
