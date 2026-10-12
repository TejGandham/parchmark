"""convert_embedding_to_pgvector

Revision ID: 49f4bec52ca3
Revises: 33a4da6b0cac
Create Date: 2026-02-18 15:42:16.393294

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "49f4bec52ca3"
down_revision: str | Sequence[str] | None = "33a4da6b0cac"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _get_existing_columns(inspector, table_name: str) -> list[str]:
    if not _table_exists(inspector, table_name):
        return []
    return [col["name"] for col in inspector.get_columns(table_name)]


def upgrade() -> None:
    """Convert embedding column from JSON to pgvector vector(1536).

    Brownfield-tolerant per the pattern in 3c1162fce719 / 33a4da6b0cac /
    fad201191d3b. Fresh DB: no-op (Base.metadata.create_all already produced
    the post-7f1c schema, so `notes` is absent or already past this revision).
    Brownfield at parent revision 33a4da6b0cac: convert JSON to vector(1536)
    via raw DDL — module-level pgvector import removed per F20 dep-hygiene.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not _table_exists(inspector, "notes"):
        return  # fresh DB — create_all has handled the schema
    existing = _get_existing_columns(inspector, "notes")
    if "embedding" not in existing:
        return  # already past this revision in some other shape
    # Brownfield with JSON-typed embedding — perform conversion via raw DDL.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("ALTER TABLE notes ADD COLUMN embedding_vec vector(1536)")
    op.execute("UPDATE notes SET embedding_vec = embedding::text::vector(1536) WHERE embedding IS NOT NULL")
    op.drop_column("notes", "embedding")
    op.alter_column("notes", "embedding_vec", new_column_name="embedding")


def downgrade() -> None:
    """Revert embedding column back to JSON (was pgvector)."""
    op.add_column("notes", sa.Column("embedding_json", sa.JSON(), nullable=True))
    op.execute("""
        UPDATE notes
        SET embedding_json = embedding::text::json
        WHERE embedding IS NOT NULL
    """)
    op.drop_column("notes", "embedding")
    op.alter_column("notes", "embedding_json", new_column_name="embedding")
    op.execute("DROP EXTENSION IF EXISTS vector")
