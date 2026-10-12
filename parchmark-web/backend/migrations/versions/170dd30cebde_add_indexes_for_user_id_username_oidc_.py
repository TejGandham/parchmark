"""add indexes for user_id username oidc_sub

Revision ID: 170dd30cebde
Revises: 3c1162fce719
Create Date: 2026-01-29 16:43:41.388355

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "170dd30cebde"
down_revision: str | Sequence[str] | None = "3c1162fce719"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _get_existing_indexes(inspector, table_name: str) -> list[str]:
    if not _table_exists(inspector, table_name):
        return []
    return [idx["name"] for idx in inspector.get_indexes(table_name)]


def upgrade() -> None:
    """Create ix_notes_user_id, brownfield-tolerant.

    Fresh DB after Base.metadata.create_all(): the notes table already exists
    with ix_notes_user_id (Note.user_id is declared index=True on the model),
    so this migration must be a no-op. Brownfield at parent revision
    3c1162fce719 without create_all: create the index.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not _table_exists(inspector, "notes"):
        return  # fresh DB — create_all hasn't run; app startup will produce schema
    existing_indexes = _get_existing_indexes(inspector, "notes")
    if "ix_notes_user_id" in existing_indexes:
        return  # post-create_all brownfield — index already present
    op.create_index(op.f("ix_notes_user_id"), "notes", ["user_id"], unique=False)


def downgrade() -> None:
    """Drop ix_notes_user_id, brownfield-tolerant."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not _table_exists(inspector, "notes"):
        return  # fresh DB — nothing to revert
    existing_indexes = _get_existing_indexes(inspector, "notes")
    if "ix_notes_user_id" not in existing_indexes:
        return  # already past this revision in the downgraded shape
    op.drop_index(op.f("ix_notes_user_id"), table_name="notes")
