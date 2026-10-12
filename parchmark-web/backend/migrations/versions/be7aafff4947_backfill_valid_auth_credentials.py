"""backfill valid_auth_credentials

Revision ID: be7aafff4947
Revises: 1b2c3d4e5f6a
Create Date: 2026-07-06 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "be7aafff4947"
down_revision: str | Sequence[str] | None = "1b2c3d4e5f6a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CONSTRAINT_NAME = "valid_auth_credentials"
_CONSTRAINT_PREDICATE = (
    "(auth_provider = 'local' AND password_hash IS NOT NULL) OR "
    "(auth_provider = 'oidc' AND oidc_sub IS NOT NULL)"
)


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _get_existing_check_constraints(inspector, table_name: str) -> list[str]:
    if not _table_exists(inspector, table_name):
        return []
    return [constraint["name"] for constraint in inspector.get_check_constraints(table_name)]


def upgrade() -> None:
    """Backfill the valid_auth_credentials CHECK onto brownfield DBs.

    Fresh DB after Base.metadata.create_all(): the users table already carries
    valid_auth_credentials (declared in User.__table_args__ on the model), so
    this migration must be a no-op. Brownfield at parent revision 1b2c3d4e5f6a
    without create_all having run yet, or on a truly empty DB where users
    doesn't exist at all: add the constraint (or defer to create_all).

    If existing brownfield rows violate the predicate, ADD CONSTRAINT fails
    loudly and the migration aborts — no silent data mutation, no NOT VALID.
    A human repairs the offending rows before retrying.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not _table_exists(inspector, "users"):
        return  # fresh DB — create_all hasn't run; app startup will produce schema
    existing_check_constraints = _get_existing_check_constraints(inspector, "users")
    if _CONSTRAINT_NAME in existing_check_constraints:
        return  # post-create_all brownfield — constraint already present
    op.create_check_constraint(_CONSTRAINT_NAME, "users", _CONSTRAINT_PREDICATE)


def downgrade() -> None:
    """Drop valid_auth_credentials, brownfield-tolerant."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not _table_exists(inspector, "users"):
        return  # fresh DB — nothing to revert
    existing_check_constraints = _get_existing_check_constraints(inspector, "users")
    if _CONSTRAINT_NAME not in existing_check_constraints:
        return  # already past this revision in the downgraded shape
    op.drop_constraint(_CONSTRAINT_NAME, "users", type_="check")
