"""add_oidc_support_to_user_model

Revision ID: 3c1162fce719
Revises:
Create Date: 2026-01-08 22:50:22.795808

This migration adds OIDC (OpenID Connect) support to the User model:
- Makes password_hash nullable (OIDC users don't have passwords)
- Adds oidc_sub for OIDC subject identifier
- Adds email field
- Adds auth_provider to distinguish local vs OIDC users
- Sets auth_provider='local' for all existing users
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3c1162fce719"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _get_existing_columns(inspector, table_name: str) -> list[str]:
    """Get list of existing column names for a table."""
    return [col["name"] for col in inspector.get_columns(table_name)]


def _get_existing_indexes(inspector, table_name: str) -> list[str]:
    """Get list of existing index names for a table."""
    return [idx["name"] for idx in inspector.get_indexes(table_name)]


def upgrade() -> None:
    """Add OIDC support columns to users table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = _get_existing_columns(inspector, "users")
    existing_indexes = _get_existing_indexes(inspector, "users")

    # Make password_hash nullable for OIDC users (who don't have passwords)
    if "password_hash" in existing_columns:
        op.alter_column(
            "users",
            "password_hash",
            existing_type=sa.String(255),
            nullable=True,
        )

    # Add oidc_sub column (unique identifier from OIDC provider)
    if "oidc_sub" not in existing_columns:
        op.add_column(
            "users",
            sa.Column("oidc_sub", sa.String(255), nullable=True),
        )
    if "ix_users_oidc_sub" not in existing_indexes:
        op.create_index("ix_users_oidc_sub", "users", ["oidc_sub"], unique=True)

    # Add email column
    if "email" not in existing_columns:
        op.add_column(
            "users",
            sa.Column("email", sa.String(255), nullable=True),
        )
    if "ix_users_email" not in existing_indexes:
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Add auth_provider column with default 'local'
    if "auth_provider" not in existing_columns:
        op.add_column(
            "users",
            sa.Column("auth_provider", sa.String(20), nullable=False, server_default="local"),
        )
    # Update existing users to have auth_provider='local'
    op.execute("UPDATE users SET auth_provider = 'local' WHERE auth_provider IS NULL OR auth_provider = ''")


def downgrade() -> None:
    """Remove OIDC support columns from users table.

    WARNING: This will fail if OIDC users exist (they have NULL password_hash).
    Before downgrading, either:
    1. Delete all OIDC users, or
    2. Set a placeholder password_hash for OIDC users
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = _get_existing_columns(inspector, "users")
    existing_indexes = _get_existing_indexes(inspector, "users")

    # Remove auth_provider column
    if "auth_provider" in existing_columns:
        op.drop_column("users", "auth_provider")

    # Remove email column and index
    if "ix_users_email" in existing_indexes:
        op.drop_index("ix_users_email", table_name="users")
    if "email" in existing_columns:
        op.drop_column("users", "email")

    # Remove oidc_sub column and index
    if "ix_users_oidc_sub" in existing_indexes:
        op.drop_index("ix_users_oidc_sub", table_name="users")
    if "oidc_sub" in existing_columns:
        op.drop_column("users", "oidc_sub")

    # Make password_hash non-nullable again
    # WARNING: This will fail if any users have NULL password_hash (OIDC users)
    if "password_hash" in existing_columns:
        op.alter_column(
            "users",
            "password_hash",
            existing_type=sa.String(255),
            nullable=False,
        )
