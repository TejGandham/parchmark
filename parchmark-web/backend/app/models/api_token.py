"""
Personal access token model.

A token lets a non-browser client (the MCP server, a script) authenticate as
its owner without the owner's password. Only a SHA-256 digest of the token is
stored; the plaintext is shown once, at creation, and never persisted.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database.database import Base


class ApiToken(Base):
    """A per-user API token, identified at auth time by the digest of its plaintext."""

    __tablename__ = "api_tokens"

    id = Column(Integer, primary_key=True)
    # ON DELETE CASCADE: deleting the account revokes every token it issued.
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)  # sha256 hex digest
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
