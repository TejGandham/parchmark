"""
Notes router for CRUD operations on markdown notes.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.note import Note
from app.models.user import User
from app.routers.auth import get_current_user

# Router
router = APIRouter()


# Pydantic models
class NoteBase(BaseModel):
    title: str
    content: str


class NoteCreate(NoteBase):
    pass


class NoteUpdate(NoteBase):
    pass


class NoteResponse(NoteBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    owner_id: int

    class Config:
        from_attributes = True


# Routes
@router.get("/", response_model=List[NoteResponse])
async def get_notes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all notes for the current user."""
    notes = db.query(Note).filter(Note.owner_id == current_user.id).offset(skip).limit(limit).all()
    return notes


@router.post("/", response_model=NoteResponse)
async def create_note(
    note: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new note."""
    db_note = Note(
        title=note.title,
        content=note.content,
        owner_id=current_user.id
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific note by ID."""
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    return note


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int,
    note_update: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a specific note by ID."""
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Update note fields
    note.title = note_update.title
    note.content = note_update.content
    
    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}")
async def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a specific note by ID."""
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    db.delete(note)
    db.commit()
    
    return {"message": "Note deleted successfully"}
