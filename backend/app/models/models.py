"""
SQLAlchemy models for ParchMark backend.
Defines User and Note models matching the frontend data structures.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


class User(Base):
    """
    User model for authentication and note ownership.
    Matches the frontend User interface with additional fields for backend needs.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(
        String(255), nullable=False
    )  # Store hashed password, not plain text
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship to notes
    notes = relationship("Note", back_populates="owner", cascade="all, delete-orphan")


class Note(Base):
    """
    Note model for storing markdown notes.
    Matches the frontend Note interface with user relationship.
    """

    __tablename__ = "notes"

    id = Column(
        String(50), primary_key=True, index=True
    )  # Using string ID to match frontend
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship to user
    owner = relationship("User", back_populates="notes")
