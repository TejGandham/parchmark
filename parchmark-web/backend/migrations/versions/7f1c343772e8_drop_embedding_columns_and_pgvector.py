"""drop embedding columns and pgvector

Revision ID: 7f1c343772e8
Revises: 49f4bec52ca3
Create Date: 2026-05-10 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7f1c343772e8"
down_revision: str | Sequence[str] | None = "49f4bec52ca3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _get_existing_columns(inspector, table_name: str) -> list[str]:
    if not _table_exists(inspector, table_name):
        return []
    return [col["name"] for col in inspector.get_columns(table_name)]


def upgrade() -> None:
    """Drop embedding/access tracking columns and the pgvector extension.

    Brownfield-tolerant. Fresh DB: no-op (Base.metadata.create_all already
    produced the post-7f1c schema, so the columns are absent). Brownfield at
    parent revision 49f4bec52ca3: drop the three columns and the extension.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not _table_exists(inspector, "notes"):
        return  # fresh DB — create_all has handled the schema
    existing = _get_existing_columns(inspector, "notes")
    if "embedding" not in existing:
        return  # already past this revision
    op.drop_column("notes", "embedding")
    op.drop_column("notes", "access_count")
    op.drop_column("notes", "last_accessed_at")
    op.execute("DROP EXTENSION IF EXISTS vector")


def downgrade() -> None:
    """Recreate the pgvector extension and the dropped columns.

    Brownfield-tolerant. Fresh DB: no-op. Brownfield (post-7f1c schema):
    recreate the extension and three columns via raw DDL — module-level
    pgvector import removed per F20 dep-hygiene.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not _table_exists(inspector, "notes"):
        return  # fresh DB — nothing to revert
    existing = _get_existing_columns(inspector, "notes")
    if "embedding" in existing:
        return  # already at this revision in the downgraded shape
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column(
        "notes",
        sa.Column(
            "access_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )
    op.add_column(
        "notes",
        sa.Column(
            "last_accessed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.execute("ALTER TABLE notes ADD COLUMN embedding vector(1536)")
