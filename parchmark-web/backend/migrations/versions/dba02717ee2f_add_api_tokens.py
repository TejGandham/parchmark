"""add api tokens

Revision ID: dba02717ee2f
Revises: be7aafff4947
Create Date: 2026-10-14 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dba02717ee2f"
down_revision: str | Sequence[str] | None = "be7aafff4947"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "api_tokens"
_INDEXES = (
    ("ix_api_tokens_user_id", ["user_id"], False),
    ("ix_api_tokens_token_hash", ["token_hash"], True),
)


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    """Create api_tokens, brownfield-tolerant.

    Fresh DB: users does not exist yet, so app startup's create_all produces
    api_tokens alongside it. Post-create_all DB: api_tokens already exists, so
    this is a no-op. Brownfield at be7aafff4947: create the table and indexes.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not _table_exists(inspector, "users") or _table_exists(inspector, _TABLE):
        return

    op.create_table(
        _TABLE,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for index_name, columns, unique in _INDEXES:
        op.create_index(op.f(index_name), _TABLE, columns, unique=unique)


def downgrade() -> None:
    """Drop api_tokens, brownfield-tolerant. Revokes every issued token."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not _table_exists(inspector, _TABLE):
        return

    existing_indexes = {index["name"] for index in inspector.get_indexes(_TABLE)}
    for index_name, _columns, _unique in _INDEXES:
        if index_name in existing_indexes:
            op.drop_index(op.f(index_name), table_name=_TABLE)
    op.drop_table(_TABLE)
