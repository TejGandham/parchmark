"""
SQLAlchemy models for ParchMark backend.
Defines User and Note models matching the frontend data structures.
"""

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class User(Base):
    """
    User model for authentication and note ownership.
    Matches the frontend User interface with additional fields for backend needs.
    Supports both local password auth and OIDC federated auth.
    """

    __tablename__ = "users"
    __table_args__ = (
        # Ensure auth credentials are consistent with auth_provider:
        # - Local users must have password_hash
        # - OIDC users must have oidc_sub
        CheckConstraint(
            "(auth_provider = 'local' AND password_hash IS NOT NULL) OR "
            "(auth_provider = 'oidc' AND oidc_sub IS NOT NULL)",
            name="valid_auth_credentials",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for OIDC-only users
    email = Column(String(255), nullable=True)  # Email from OIDC provider
    oidc_sub = Column(String(255), unique=True, nullable=True, index=True)  # OIDC subject claim
    auth_provider = Column(String(50), default="local", nullable=False)  # "local" or "oidc"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to notes
    notes = relationship("Note", back_populates="owner", cascade="all, delete-orphan")


class Note(Base):
    """
    Note model for storing markdown notes.
    Matches the frontend Note interface with user relationship.
    """

    __tablename__ = "notes"

    id = Column(String(50), primary_key=True, index=True)  # Using string ID to match frontend
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    access_count = Column(Integer, server_default=text("0"), nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship to user
    owner = relationship("User", back_populates="notes")
