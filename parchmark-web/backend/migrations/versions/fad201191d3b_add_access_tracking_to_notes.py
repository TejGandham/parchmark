"""add_access_tracking_to_notes

Revision ID: fad201191d3b
Revises: 170dd30cebde
Create Date: 2026-02-16 15:47:36.515807

This migration adds access tracking columns to the notes table:
- access_count: Integer counter for how many times a note has been accessed
- last_accessed_at: Timestamp of the most recent access
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fad201191d3b"
down_revision: str | Sequence[str] | None = "170dd30cebde"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(inspector, table_name: str) -> bool:
    """Check if a table exists in the database."""
    return table_name in inspector.get_table_names()


def _get_existing_columns(inspector, table_name: str) -> list[str]:
    """Get list of existing column names for a table."""
    if not _table_exists(inspector, table_name):
        return []
    return [col["name"] for col in inspector.get_columns(table_name)]


def upgrade() -> None:
    """Add access tracking columns to notes table.

    This migration is idempotent and handles the following scenarios:
    - Fresh database: Table doesn't exist yet (created by SQLAlchemy create_all)
    - Existing database without access tracking: Adds new columns
    - Already migrated: No changes (columns already exist)
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if not _table_exists(inspector, "notes"):
        print("Notes table does not exist yet. Skipping migration - table will be created by app startup.")
        return

    existing_columns = _get_existing_columns(inspector, "notes")

    if "access_count" not in existing_columns:
        op.add_column(
            "notes",
            sa.Column("access_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        )

    if "last_accessed_at" not in existing_columns:
        op.add_column(
            "notes",
            sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    """Remove access tracking columns from notes table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if not _table_exists(inspector, "notes"):
        return

    existing_columns = _get_existing_columns(inspector, "notes")

    if "last_accessed_at" in existing_columns:
        op.drop_column("notes", "last_accessed_at")

    if "access_count" in existing_columns:
        op.drop_column("notes", "access_count")
