"""
Artifact model.

An artifact is a user-owned, self-contained document (HTML, Markdown or SVG)
published under a stable, unguessable slug. Its content lives in immutable
versions (see ``artifact_version``); ``current_version_id`` points at the one
being served.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database.database import Base


class Artifact(Base):
    """A published artifact, owned by one user."""

    __tablename__ = "artifacts"
    __table_args__ = (CheckConstraint("visibility IN ('private', 'unlisted')", name="artifacts_visibility_valid"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # ON DELETE CASCADE: deleting the account deletes its artifacts (and, through them, their versions).
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    visibility: Mapped[str] = mapped_column(String(16), default="private", nullable=False)
    # Nullable only for the moment between inserting the artifact and its first version, inside one transaction.
    # use_alter breaks the artifacts <-> artifact_versions foreign-key cycle for create_all/drop_all.
    current_version_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("artifact_versions.id", name="fk_artifacts_current_version_id", use_alter=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
