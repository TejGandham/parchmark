"""
Integration tests for F19: Alembic migration drops embedding columns + pgvector extension.

Oracle: /features/7/oracle
Contract: /features/7/contract

Assertions covered:
  /features/7/oracle/assertions/0 — alembic upgrade head from 49f4bec52ca3 succeeds
  /features/7/oracle/assertions/1 — pg_extension has no 'vector' row after upgrade
  /features/7/oracle/assertions/2 — information_schema.columns has no dropped columns after upgrade
  /features/7/oracle/assertions/3 — downgrade→upgrade round-trip succeeds; columns + extension absent after re-upgrade
  /features/7/oracle/assertions/4 — models.py has no pgvector / Vector( references
  /features/7/oracle/assertions/5 — init_db.py has no CREATE EXTENSION ... vector

Each test class is self-contained. The migration tests spin up a dedicated
testcontainers Postgres (pgvector/pgvector:pg17 image — required for downgrade
recreation of Vector(1536)) seeded at revision 49f4bec52ca3 before applying
the new F19 head migration.

NOTE on alembic env URL plumbing: backend/migrations/env.py reads the DB URL
from `os.environ["DATABASE_URL"]` and ignores anything passed via
`alembic_cfg.set_main_option`. The fixture below sets `DATABASE_URL` in the
process environment to the testcontainer's URL before invoking alembic.
"""

import os
import re
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from testcontainers.postgres import PostgresContainer

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_BACKEND_ROOT = Path(__file__).parents[3]  # backend/
_ALEMBIC_INI = _BACKEND_ROOT / "alembic.ini"
_MODELS_PY = _BACKEND_ROOT / "app" / "models" / "models.py"
_INIT_DB_PY = _BACKEND_ROOT / "app" / "database" / "init_db.py"

# The parent revision that F19's migration must be parented against.
_PARENT_REVISION = "49f4bec52ca3"


def _file_matches(path: Path, *patterns: str) -> list[tuple[int, str]]:
    """Native-Python alternative to ripgrep — returns (lineno, line) for matches."""
    rxs = [re.compile(p) for p in patterns]
    matches: list[tuple[int, str]] = []
    for i, line in enumerate(path.read_text().splitlines(), start=1):
        if any(rx.search(line) for rx in rxs):
            matches.append((i, line))
    return matches


# ---------------------------------------------------------------------------
# Fixture: isolated Postgres container seeded at the parent revision
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def migration_container():
    """
    Spin up a fresh pgvector/pgvector:pg17 container, materialize the schema
    state corresponding to F19's parent revision (49f4bec52ca3), and yield
    (engine, alembic_cfg) so each test class can run command.upgrade(head).

    The migration chain is brownfield-tolerant: revision 3c1162fce719 (root)
    explicitly skips when `users` doesn't exist, expecting app startup to
    create tables via Base.metadata.create_all() FIRST. The next revision
    170dd30cebde isn't brownfield-tolerant (creates an index assuming `notes`
    exists), so a naive command.upgrade(parent) on a fresh DB fails. The
    conftest sidesteps this by running create_all() and skipping alembic.

    For F19's migration test we follow the same protocol:
      1. create_all() materializes the current Note model (without dropped cols)
      2. ALTER TABLE adds the embedding/access_count/last_accessed_at columns
         that revisions fad201191d3b, 33a4da6b0cac, 49f4bec52ca3 cumulatively
         introduce — recreating the schema state F19 expects to operate on.
      3. command.stamp(parent_revision) marks alembic at parent without
         re-running the (partially broken on fresh DB) upstream chain.
      4. Tests then call command.upgrade("head") which runs only F19.

    Sets DATABASE_URL in the process environment so backend/migrations/env.py
    picks up the testcontainer URL (env.py ignores set_main_option).
    """
    # Import here to avoid pulling app code at module load time
    from app.database.database import Base
    from app.models import models  # noqa: F401 — registers Note/User on Base

    saved_database_url = os.environ.get("DATABASE_URL")
    with PostgresContainer("pgvector/pgvector:pg17") as pg:
        sync_url = pg.get_connection_url()
        os.environ["DATABASE_URL"] = sync_url

        try:
            engine = create_engine(sync_url)

            # Step 1+2: bootstrap schema like app startup does, then add the
            # columns that revisions fad201191d3b/33a4da6b0cac/49f4bec52ca3
            # contributed (which F19 will drop).
            with engine.begin() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            Base.metadata.create_all(bind=engine)
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE notes ADD COLUMN IF NOT EXISTS access_count INTEGER NOT NULL DEFAULT 0"))
                conn.execute(
                    text("ALTER TABLE notes ADD COLUMN IF NOT EXISTS last_accessed_at TIMESTAMP WITH TIME ZONE")
                )
                conn.execute(text("ALTER TABLE notes ADD COLUMN IF NOT EXISTS embedding vector(1536)"))

            alembic_cfg = Config(str(_ALEMBIC_INI))
            alembic_cfg.set_main_option("sqlalchemy.url", sync_url)

            # Step 3: stamp alembic at the parent revision so upgrade head
            # runs ONLY the F19 migration.
            command.stamp(alembic_cfg, _PARENT_REVISION)

            yield engine, alembic_cfg, sync_url
        finally:
            if saved_database_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = saved_database_url


# ---------------------------------------------------------------------------
# /features/7/oracle/assertions/0
# ---------------------------------------------------------------------------


class TestF19UpgradeSucceeds:
    """alembic upgrade head from 49f4bec52ca3 completes without error."""

    def test_upgrade_head_from_parent_revision_raises_no_exception(self, migration_container):
        """
        Oracle: /features/7/oracle/assertions/0
        Contract: /features/7/contract/new_migration/down_revision == '49f4bec52ca3'
        """
        engine, alembic_cfg, _ = migration_container
        command.upgrade(alembic_cfg, "head")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current = result.scalar()
        assert current != _PARENT_REVISION, (
            f"alembic_version still at parent {_PARENT_REVISION!r} — "
            "upgrade head produced no new revision. F19 migration may be missing."
        )


# ---------------------------------------------------------------------------
# /features/7/oracle/assertions/1
# ---------------------------------------------------------------------------


class TestPgExtensionVectorAbsent:
    """After upgrade, pg_extension has zero rows for 'vector'."""

    def test_vector_extension_not_present_after_upgrade(self, migration_container):
        """
        Oracle: /features/7/oracle/assertions/1
        Contract: /features/7/contract/new_migration/upgrade_runs == 'DROP EXTENSION IF EXISTS vector'
        """
        engine, alembic_cfg, _ = migration_container
        command.upgrade(alembic_cfg, "head")

        with engine.connect() as conn:
            rows = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'")).fetchall()

        assert rows == [], (
            "Expected pg_extension to have zero rows for extname='vector' after upgrade, " f"but got: {rows}"
        )


# ---------------------------------------------------------------------------
# /features/7/oracle/assertions/2
# ---------------------------------------------------------------------------


class TestDroppedColumnsAbsentAfterUpgrade:
    """After upgrade, information_schema.columns has no rows for dropped columns."""

    def test_embedding_access_count_last_accessed_at_absent_from_notes(self, migration_container):
        """
        Oracle: /features/7/oracle/assertions/2
        Contract: /features/7/contract/new_migration/upgrade_drops_columns
        """
        engine, alembic_cfg, _ = migration_container
        command.upgrade(alembic_cfg, "head")

        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'notes'
                      AND column_name IN ('embedding', 'access_count', 'last_accessed_at')
                    """
                )
            ).fetchall()

        assert rows == [], (
            "Expected zero rows in information_schema.columns for "
            "notes.(embedding, access_count, last_accessed_at) after upgrade, "
            f"but found: {[r[0] for r in rows]}"
        )


# ---------------------------------------------------------------------------
# /features/7/oracle/assertions/3
# ---------------------------------------------------------------------------


class TestRoundTripDowngradeUpgrade:
    """Downgrade to parent then upgrade to head succeeds; post-round-trip state is clean."""

    def test_downgrade_to_parent_then_upgrade_head_succeeds(self, migration_container):
        """
        Oracle: /features/7/oracle/assertions/3
        Verifies that the downgrade recreates extension + columns, and the
        subsequent re-upgrade removes them again.
        """
        engine, alembic_cfg, _ = migration_container
        # Start from head
        command.upgrade(alembic_cfg, "head")

        # Downgrade to parent — must not raise
        command.downgrade(alembic_cfg, _PARENT_REVISION)

        # After downgrade: vector extension must be present (recreated)
        with engine.connect() as conn:
            ext_rows = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'")).fetchall()
        assert len(ext_rows) == 1, (
            "After downgrade to parent, expected vector extension to be recreated, " f"but pg_extension has: {ext_rows}"
        )

        # After downgrade: columns must be present
        with engine.connect() as conn:
            col_rows = conn.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'notes'
                      AND column_name IN ('embedding', 'access_count', 'last_accessed_at')
                    ORDER BY column_name
                    """
                )
            ).fetchall()
        recreated = {r[0] for r in col_rows}
        assert recreated == {
            "embedding",
            "access_count",
            "last_accessed_at",
        }, f"After downgrade, expected all three columns recreated but got: {recreated}"

        # Re-upgrade to head
        command.upgrade(alembic_cfg, "head")

        # Post-round-trip: extension absent
        with engine.connect() as conn:
            ext_after = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'")).fetchall()
        assert ext_after == [], f"After round-trip upgrade, vector extension still present: {ext_after}"

        # Post-round-trip: columns absent
        with engine.connect() as conn:
            col_after = conn.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'notes'
                      AND column_name IN ('embedding', 'access_count', 'last_accessed_at')
                    """
                )
            ).fetchall()
        assert col_after == [], f"After round-trip upgrade, dropped columns still present: {[r[0] for r in col_after]}"


# ---------------------------------------------------------------------------
# /features/7/oracle/assertions/4
# ---------------------------------------------------------------------------


class TestModelsPyNoPgvectorReferences:
    """
    Static check: backend/app/models/models.py contains no 'pgvector' or 'Vector(' strings.
    Contract: /features/7/contract/models_py/pgvector_sqlalchemy_import == 'removed'
    """

    def test_models_py_has_no_pgvector_or_vector_import(self):
        """Oracle: /features/7/oracle/assertions/4."""
        assert _MODELS_PY.exists(), f"models.py not found at {_MODELS_PY}"
        hits = _file_matches(_MODELS_PY, r"pgvector", r"Vector\(")
        assert hits == [], f"Expected zero matches for 'pgvector' / 'Vector(' in {_MODELS_PY}, got: {hits}"


# ---------------------------------------------------------------------------
# /features/7/oracle/assertions/5
# ---------------------------------------------------------------------------


class TestInitDbPyNoCreateExtension:
    """
    Static check: backend/app/database/init_db.py contains no 'CREATE EXTENSION' + 'vector'.
    Contract: /features/7/contract/init_db_py/create_extension_vector_line == 'removed'
    """

    def test_init_db_py_has_no_create_extension_vector(self):
        """Oracle: /features/7/oracle/assertions/5."""
        assert _INIT_DB_PY.exists(), f"init_db.py not found at {_INIT_DB_PY}"
        hits = _file_matches(_INIT_DB_PY, r"(?i)CREATE\s+EXTENSION.*vector")
        assert hits == [], f"Expected zero matches for 'CREATE EXTENSION ... vector' in {_INIT_DB_PY}, got: {hits}"
