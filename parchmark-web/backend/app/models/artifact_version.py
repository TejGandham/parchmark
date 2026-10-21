"""
Artifact version model.

A version is an immutable snapshot of an artifact's raw content. Version
numbers start at 1 and increase by one per publish, unique per artifact.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database.database import Base


class ArtifactVersion(Base):
    """One published revision of an artifact's content."""

    __tablename__ = "artifact_versions"
    __table_args__ = (
        UniqueConstraint("artifact_id", "version", name="uq_artifact_versions_artifact_id_version"),
        CheckConstraint("version > 0", name="artifact_versions_version_positive"),
        CheckConstraint(
            "content_type IN ('html', 'markdown', 'svg')",
            name="artifact_versions_content_type_valid",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # The (artifact_id, version) unique index also serves lookups by artifact_id.
    artifact_id: Mapped[int] = mapped_column(Integer, ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
