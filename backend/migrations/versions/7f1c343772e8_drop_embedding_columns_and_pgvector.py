"""drop embedding columns and pgvector

Revision ID: 7f1c343772e8
Revises: 49f4bec52ca3
Create Date: 2026-05-10 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "7f1c343772e8"
down_revision: str | Sequence[str] | None = "49f4bec52ca3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop embedding/access tracking columns and the pgvector extension."""
    op.drop_column("notes", "embedding")
    op.drop_column("notes", "access_count")
    op.drop_column("notes", "last_accessed_at")
    op.execute("DROP EXTENSION IF EXISTS vector")


def downgrade() -> None:
    """Recreate the pgvector extension and the dropped columns."""
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
    op.add_column(
        "notes",
        sa.Column("embedding", Vector(1536), nullable=True),
    )
