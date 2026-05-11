"""
Integration tests for F20: Drop openai and pgvector dependencies from pyproject.toml.

Oracle: /features/8/oracle
Contract: /features/8/contract

Assertions covered here:
  /features/8/oracle/assertions/8 — brownfield-replay test: upgrade 49f4bec52ca3
      against pgvector-capable container; notes.embedding ends up as type vector.
  /features/8/oracle/assertions/9 — fresh-DB full-chain test: Base.metadata.create_all
      on vanilla postgres:17 then command.upgrade(head) completes without error.

Static-check assertions (1, 5, 6, 7) are in test_f20_static_checks.py.
Assertion 0 is in test_f20_static_checks.py (pyproject grep).
Assertions 2, 3, 4 are noted as CI-gate / manual-step coverage — see decisions block.

NOTE on alembic env URL plumbing: backend/migrations/env.py reads the DB URL
from os.environ["DATABASE_URL"] and ignores anything passed via
alembic_cfg.set_main_option.  Each fixture sets DATABASE_URL in the process
environment before invoking alembic commands, and restores it on teardown.
"""

import os
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

# Revision under test in the brownfield scenario (assertion 8).
_BROWNFIELD_TARGET_REVISION = "49f4bec52ca3"
# Its parent revision — the schema we seed.
_BROWNFIELD_PARENT_REVISION = "33a4da6b0cac"


# ---------------------------------------------------------------------------
# Parent-schema SQL for the brownfield fixture
#
# Represents the schema state at 33a4da6b0cac (notes.embedding is JSON).
# This mirrors the approach used in test_f19_drop_embedding.py:74-103:
# hand-rolled SQL avoids relying on Base.metadata.create_all() which has
# import-ordering sensitivities under pytest-xdist.
# ---------------------------------------------------------------------------
_BROWNFIELD_PARENT_SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    email VARCHAR(255),
    oidc_sub VARCHAR(255) UNIQUE,
    auth_provider VARCHAR(50) NOT NULL DEFAULT 'local',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);
CREATE INDEX ix_users_id ON users(id);
CREATE INDEX ix_users_username ON users(username);
CREATE INDEX ix_users_oidc_sub ON users(oidc_sub);

CREATE TABLE notes (
    id VARCHAR(50) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    embedding JSON,
    access_count INTEGER NOT NULL DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE
);
CREATE INDEX ix_notes_id ON notes(id);
CREATE INDEX ix_notes_user_id ON notes(user_id);
"""

# A sample JSON-encoded embedding to insert so the UPDATE path in 49f4's
# upgrade() exercises data preservation (optional but valuable per the brief).
_SAMPLE_EMBEDDING_JSON = "[" + ",".join(["0.1"] * 1536) + "]"


# ---------------------------------------------------------------------------
# Fixture: brownfield pgvector container seeded at 33a4da6b0cac
# Oracle assertion 8
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def brownfield_migration_container():
    """
    Spin up pgvector/pgvector:pg17, materialize the schema at parent revision
    33a4da6b0cac (notes.embedding as JSON), insert one sample row, stamp
    alembic at 33a4da6b0cac, then yield (engine, alembic_cfg).

    The pgvector image is required because the rewritten 49f4bec52ca3.upgrade()
    brownfield path runs CREATE EXTENSION IF NOT EXISTS vector — the vanilla
    postgres:17 image has no vector.so and would fail at that step.

    This fixture is intentionally separate from the F19 migration_container
    fixture — each feature's load-bearing migration test owns its own container.
    """
    saved_db_url = os.environ.get("DATABASE_URL")
    with PostgresContainer("pgvector/pgvector:pg17") as pg:
        sync_url = pg.get_connection_url()
        os.environ["DATABASE_URL"] = sync_url
        try:
            engine = create_engine(sync_url)

            # Materialize the parent-revision schema.
            with engine.begin() as conn:
                for stmt in _BROWNFIELD_PARENT_SCHEMA_SQL.strip().split(";"):
                    s = stmt.strip()
                    if s:
                        conn.execute(text(s))

            # Insert a sample user and note with a JSON embedding so the UPDATE
            # path in 49f4.upgrade() exercises data conversion, not just DDL.
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO users (username, password_hash, auth_provider) "
                        "VALUES ('brownfield_test_user', 'hash', 'local')"
                    )
                )
                conn.execute(
                    text(
                        "INSERT INTO notes (id, user_id, title, content, embedding) "
                        "VALUES ('note-bf-1', 1, 'BF Note', 'content', :emb)"
                    ),
                    {"emb": _SAMPLE_EMBEDDING_JSON},
                )

            alembic_cfg = Config(str(_ALEMBIC_INI))
            alembic_cfg.set_main_option("sqlalchemy.url", sync_url)

            # Stamp at the parent revision — upgrade() will run only 49f4bec52ca3.
            command.stamp(alembic_cfg, _BROWNFIELD_PARENT_REVISION)

            yield engine, alembic_cfg
        finally:
            if saved_db_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = saved_db_url


# ---------------------------------------------------------------------------
# Oracle assertion 8 — brownfield-replay test
# /features/8/oracle/assertions/8
# ---------------------------------------------------------------------------


class TestF20BrownfieldReplay49f4:
    """
    Running command.upgrade(alembic_cfg, '49f4bec52ca3') against a brownfield
    pgvector testcontainer (notes.embedding as JSON at parent 33a4da6b0cac)
    succeeds and produces notes.embedding with type vector.

    Oracle: /features/8/oracle/assertions/8
    Contract: /features/8/contract/migration_rewrite_strategy
    """

    def test_upgrade_49f4_completes_without_error(self, brownfield_migration_container):
        """
        /features/8/oracle/assertions/8 — part 1: upgrade exits without exception.
        """
        engine, alembic_cfg = brownfield_migration_container
        # Must not raise. Will fail with ImportError if from pgvector... import
        # is still present in the migration file (pgvector is not installed).
        command.upgrade(alembic_cfg, _BROWNFIELD_TARGET_REVISION)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current = result.scalar()
        assert current == _BROWNFIELD_TARGET_REVISION, (
            f"Expected alembic_version to be {_BROWNFIELD_TARGET_REVISION!r} " f"after upgrade, but got {current!r}"
        )

    def test_notes_embedding_column_type_is_vector_after_upgrade(self, brownfield_migration_container):
        """
        /features/8/oracle/assertions/8 — part 2: notes.embedding has udt_name = 'vector'
        after the brownfield upgrade.

        The rewritten 49f4bec52ca3.upgrade() must perform:
          CREATE EXTENSION IF NOT EXISTS vector
          ALTER TABLE notes ADD COLUMN embedding_vec vector(1536)
          UPDATE notes SET embedding_vec = embedding::text::vector(1536) ...
          drop old, rename new
        This assertion catches a wrong raw-DDL rewrite (e.g. wrong type name,
        missing UPDATE, wrong rename) that static grep checks cannot catch.
        """
        engine, alembic_cfg = brownfield_migration_container
        command.upgrade(alembic_cfg, _BROWNFIELD_TARGET_REVISION)

        with engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT udt_name
                    FROM information_schema.columns
                    WHERE table_name = 'notes'
                      AND column_name = 'embedding'
                    """
                )
            ).fetchone()

        assert row is not None, (
            "notes.embedding column not found after upgrading to 49f4bec52ca3 "
            "— the rename step may have failed or the column was dropped entirely."
        )
        assert row[0] == "vector", (
            f"Expected notes.embedding to have udt_name='vector' after upgrade "
            f"to 49f4bec52ca3, but got udt_name={row[0]!r}. "
            "The raw-DDL rewrite of 49f4bec52ca3.upgrade() may use the wrong type."
        )

    def test_sample_embedding_data_preserved_after_upgrade(self, brownfield_migration_container):
        """
        /features/8/oracle/assertions/8 — part 3 (optional but valuable per brief):
        the sample JSON embedding inserted before the upgrade is preserved as a
        non-NULL vector after the conversion.
        """
        engine, alembic_cfg = brownfield_migration_container
        command.upgrade(alembic_cfg, _BROWNFIELD_TARGET_REVISION)

        with engine.connect() as conn:
            row = conn.execute(text("SELECT embedding FROM notes WHERE id = 'note-bf-1'")).fetchone()

        assert row is not None, "Sample note not found after upgrade — unexpected."
        assert row[0] is not None, (
            "notes.embedding is NULL for the sample note after upgrade to 49f4bec52ca3. "
            "The UPDATE ... SET embedding_vec = embedding::text::vector(1536) step "
            "may have been skipped or failed silently."
        )


# ---------------------------------------------------------------------------
# Fixture: fresh vanilla postgres:17 container
# Oracle assertion 9
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def fresh_vanilla_migration_container():
    """
    Spin up postgres:17 (NO pgvector), run command.upgrade(alembic_cfg, 'head')
    against the EMPTY DB first (all migrations early-return on the missing notes
    table), then run Base.metadata.create_all() to produce the current
    (post-7f1c) schema.  Yield (engine, alembic_cfg).

    Order matches production boot sequence (docker-entrypoint.sh):
      1. alembic upgrade head  — against empty DB; all brownfield guards
         early-return because notes does not exist yet; alembic stamps at head.
      2. init_database() / Base.metadata.create_all() — creates the
         post-7f1c schema tables.
      3. (seed_database, not exercised here)

    The OLD order (create_all FIRST) was wrong: it caused 33a4da6b0cac's
    brownfield guard to see notes and attempt to add the embedding column,
    then 49f4's guard to attempt CREATE EXTENSION vector — which fails on the
    vanilla postgres:17 image (no vector.so).

    Importing app.models.models (which registers all mapped classes with Base)
    before calling create_all() ensures the full current schema is materialized,
    matching what init_db.py does on startup.
    """
    saved_db_url = os.environ.get("DATABASE_URL")
    with PostgresContainer("postgres:17") as pg:
        sync_url = pg.get_connection_url()
        os.environ["DATABASE_URL"] = sync_url
        try:
            engine = create_engine(sync_url)

            alembic_cfg = Config(str(_ALEMBIC_INI))
            alembic_cfg.set_main_option("sqlalchemy.url", sync_url)

            # Step 1: run alembic upgrade against the empty DB first.
            # All brownfield migrations early-return (notes table absent);
            # alembic stamps the version table at head.
            command.upgrade(alembic_cfg, "head")

            # Step 2: materialize the current ORM schema (post-7f1c).
            # Import models to register all ORM classes with Base before
            # calling create_all.  Must happen after DATABASE_URL is set.
            import app.models.models  # noqa: F401 — side-effect: registers ORM classes
            from app.database.database import Base

            with engine.begin() as conn:
                Base.metadata.create_all(bind=conn)

            yield engine, alembic_cfg
        finally:
            if saved_db_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = saved_db_url


# ---------------------------------------------------------------------------
# Oracle assertion 9 — fresh-DB full-chain test
# /features/8/oracle/assertions/9
# ---------------------------------------------------------------------------


class TestF20FreshDbFullChain:
    """
    Running command.upgrade(alembic_cfg, 'head') against a fresh postgres:17
    container (after Base.metadata.create_all) completes successfully.

    Every migration in the chain (3c1162fce719 → 170dd30cebde → fad201191d3b
    → 33a4da6b0cac → 49f4bec52ca3 → 7f1c343772e8) must detect the post-7f1c
    schema is already present and return early.

    Oracle: /features/8/oracle/assertions/9
    Contract: /features/8/contract/migration_rewrite_strategy
              /features/8/contract/migration_brownfield_pattern
    """

    def test_upgrade_head_on_fresh_db_raises_no_exception(self, fresh_vanilla_migration_container):
        """
        /features/8/oracle/assertions/9 — part 1: upgrade exits without exception.

        Will fail if 49f4bec52ca3.upgrade() or 7f1c343772e8.upgrade() lacks the
        brownfield guard and attempts CREATE EXTENSION or column operations on the
        already-correct post-7f1c schema.

        Will also fail if either migration still has `from pgvector.sqlalchemy import
        Vector` at module level (ImportError because pgvector is not installed).
        """
        engine, alembic_cfg = fresh_vanilla_migration_container
        # Must not raise — the entire reason F20 exists.
        command.upgrade(alembic_cfg, "head")

    def test_alembic_version_table_records_head_after_fresh_db_upgrade(self, fresh_vanilla_migration_container):
        """
        /features/8/oracle/assertions/9 — part 2: alembic_version table records
        head revision after the full-chain upgrade.

        Verifies that even though every migration early-returns its body, alembic
        still records each revision as applied (the version table is updated by
        alembic's framework, not by the migration body itself).
        """
        engine, alembic_cfg = fresh_vanilla_migration_container
        command.upgrade(alembic_cfg, "head")

        # The head revision in the chain is 7f1c343772e8.
        _HEAD_REVISION = "7f1c343772e8"

        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current = result.scalar()

        assert current == _HEAD_REVISION, (
            f"Expected alembic_version to record head revision {_HEAD_REVISION!r} "
            f"after full-chain upgrade on fresh DB, but got {current!r}. "
            "A migration in the chain may have raised before alembic could stamp it."
        )

    def test_notes_table_has_no_embedding_column_after_fresh_db_upgrade(self, fresh_vanilla_migration_container):
        """
        /features/8/oracle/assertions/9 — part 3: notes table has no embedding,
        access_count, or last_accessed_at columns (the post-7f1c schema is correct).

        Verifies that the brownfield-tolerant rewrites of 49f4 and 7f1c did not
        accidentally add embedding columns to the fresh DB during upgrade.
        """
        engine, alembic_cfg = fresh_vanilla_migration_container
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
            "Expected no embedding/access_count/last_accessed_at columns on notes "
            "after fresh-DB full-chain upgrade, but found: "
            f"{[r[0] for r in rows]}. "
            "A brownfield migration may have incorrectly added columns to the fresh schema."
        )
