"""add note tags

Revision ID: 1b2c3d4e5f6a
Revises: 8f4d2b1c9a7e
Create Date: 2026-06-21 14:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1b2c3d4e5f6a"
down_revision: str | Sequence[str] | None = "8f4d2b1c9a7e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _get_existing_indexes(inspector, table_name: str) -> list[str]:
    if not _table_exists(inspector, table_name):
        return []
    return [idx["name"] for idx in inspector.get_indexes(table_name)]


def _get_existing_constraints(inspector, table_name: str) -> list[str]:
    if not _table_exists(inspector, table_name):
        return []
    constraints = inspector.get_unique_constraints(table_name) + inspector.get_check_constraints(table_name)
    return [constraint["name"] for constraint in constraints]


def upgrade() -> None:
    """Create note_tags, brownfield-tolerant."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not _table_exists(inspector, "notes") or _table_exists(inspector, "note_tags"):
        return

    op.create_table(
        "note_tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("note_id", sa.String(length=50), nullable=False),
        sa.Column("tag", sa.String(length=64), nullable=False),
        sa.CheckConstraint("length(tag) > 0", name="note_tags_tag_not_empty"),
        sa.ForeignKeyConstraint(["note_id"], ["notes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("note_id", "tag", name="uq_note_tags_note_id_tag"),
    )

    inspector = sa.inspect(conn)
    existing_indexes = _get_existing_indexes(inspector, "note_tags")
    if "ix_note_tags_id" not in existing_indexes:
        op.create_index(op.f("ix_note_tags_id"), "note_tags", ["id"], unique=False)
    if "ix_note_tags_note_id" not in existing_indexes:
        op.create_index(op.f("ix_note_tags_note_id"), "note_tags", ["note_id"], unique=False)
    if "ix_note_tags_tag" not in existing_indexes:
        op.create_index(op.f("ix_note_tags_tag"), "note_tags", ["tag"], unique=False)


def downgrade() -> None:
    """Drop note_tags, brownfield-tolerant."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not _table_exists(inspector, "note_tags"):
        return

    existing_indexes = _get_existing_indexes(inspector, "note_tags")
    for index_name in ("ix_note_tags_tag", "ix_note_tags_note_id", "ix_note_tags_id"):
        if index_name in existing_indexes:
            op.drop_index(op.f(index_name), table_name="note_tags")

    # Constraints are dropped with the table. Keep the introspection call here
    # to mirror the guarded migration style used across this repo.
    _get_existing_constraints(inspector, "note_tags")
    op.drop_table("note_tags")
