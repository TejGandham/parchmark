"""add_embedding_to_notes

Revision ID: 33a4da6b0cac
Revises: fad201191d3b
Create Date: 2026-02-16 18:27:05.128994

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "33a4da6b0cac"
down_revision: str | Sequence[str] | None = "fad201191d3b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _get_existing_columns(inspector, table_name: str) -> list[str]:
    if not _table_exists(inspector, table_name):
        return []
    return [col["name"] for col in inspector.get_columns(table_name)]


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if not _table_exists(inspector, "notes"):
        return

    existing_columns = _get_existing_columns(inspector, "notes")

    if "embedding" not in existing_columns:
        op.add_column("notes", sa.Column("embedding", sa.JSON(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if not _table_exists(inspector, "notes"):
        return

    existing_columns = _get_existing_columns(inspector, "notes")

    if "embedding" in existing_columns:
        op.drop_column("notes", "embedding")
