"""add artifacts and artifact versions

Revision ID: 7dc2de38f032
Revises: dba02717ee2f
Create Date: 2026-10-14 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7dc2de38f032"
down_revision: str | Sequence[str] | None = "dba02717ee2f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ARTIFACTS = "artifacts"
_VERSIONS = "artifact_versions"
_CURRENT_VERSION_FK = "fk_artifacts_current_version_id"


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    """Create artifacts and artifact_versions, brownfield-tolerant.

    Fresh DB: users does not exist yet, so app startup's create_all produces
    both tables alongside it. Post-create_all DB: artifacts already exists, so
    this is a no-op. Brownfield at dba02717ee2f: create both tables, then the
    artifacts -> artifact_versions foreign key that closes the cycle.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not _table_exists(inspector, "users") or _table_exists(inspector, _ARTIFACTS):
        return

    op.create_table(
        _ARTIFACTS,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("visibility", sa.String(length=16), nullable=False),
        sa.Column("current_version_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("visibility IN ('private', 'unlisted')", name="artifacts_visibility_valid"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_artifacts_owner_id"), _ARTIFACTS, ["owner_id"], unique=False)
    op.create_index(op.f("ix_artifacts_slug"), _ARTIFACTS, ["slug"], unique=True)

    op.create_table(
        _VERSIONS,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("artifact_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("version > 0", name="artifact_versions_version_positive"),
        sa.CheckConstraint(
            "content_type IN ('html', 'markdown', 'svg')",
            name="artifact_versions_content_type_valid",
        ),
        sa.ForeignKeyConstraint(["artifact_id"], ["artifacts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("artifact_id", "version", name="uq_artifact_versions_artifact_id_version"),
    )

    op.create_foreign_key(_CURRENT_VERSION_FK, _ARTIFACTS, _VERSIONS, ["current_version_id"], ["id"])


def downgrade() -> None:
    """Drop artifact_versions and artifacts, brownfield-tolerant. Deletes every published artifact."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if _table_exists(inspector, _ARTIFACTS):
        foreign_keys = {foreign_key["name"] for foreign_key in inspector.get_foreign_keys(_ARTIFACTS)}
        if _CURRENT_VERSION_FK in foreign_keys:
            op.drop_constraint(_CURRENT_VERSION_FK, _ARTIFACTS, type_="foreignkey")
    if _table_exists(inspector, _VERSIONS):
        op.drop_table(_VERSIONS)
    if _table_exists(inspector, _ARTIFACTS):
        op.drop_table(_ARTIFACTS)
