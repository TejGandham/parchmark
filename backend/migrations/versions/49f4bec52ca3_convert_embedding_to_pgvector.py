"""convert_embedding_to_pgvector

Revision ID: 49f4bec52ca3
Revises: 33a4da6b0cac
Create Date: 2026-02-18 15:42:16.393294

"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "49f4bec52ca3"
down_revision: str | Sequence[str] | None = "33a4da6b0cac"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Convert embedding column from JSON to pgvector Vector(1536)."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column("notes", sa.Column("embedding_vec", Vector(1536), nullable=True))
    op.execute("""
        UPDATE notes
        SET embedding_vec = embedding::text::vector(1536)
        WHERE embedding IS NOT NULL
    """)
    op.drop_column("notes", "embedding")
    op.alter_column("notes", "embedding_vec", new_column_name="embedding")


def downgrade() -> None:
    """Revert embedding column from pgvector back to JSON."""
    op.add_column("notes", sa.Column("embedding_json", sa.JSON(), nullable=True))
    op.execute("""
        UPDATE notes
        SET embedding_json = embedding::text::json
        WHERE embedding IS NOT NULL
    """)
    op.drop_column("notes", "embedding")
    op.alter_column("notes", "embedding_json", new_column_name="embedding")
    op.execute("DROP EXTENSION IF EXISTS vector")
