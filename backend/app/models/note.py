"""
Note model for storing markdown notes.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Note(Base):
    """Note model for storing markdown notes."""
    
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign key to user
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationship to user
    owner = relationship("User", back_populates="notes")
