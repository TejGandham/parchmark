"""
Pydantic schemas for ParchMark backend API.
Defines request/response models for validation matching frontend data structures.
"""

from pydantic import BaseModel, Field
from typing import Optional


# User Schemas
class UserCreate(BaseModel):
    """Schema for user registration/creation requests."""

    username: str = Field(
        ..., min_length=1, max_length=50, description="Username for the new user"
    )
    password: str = Field(..., min_length=1, description="Password for the new user")


class UserLogin(BaseModel):
    """Schema for user login requests."""

    username: str = Field(..., description="Username for authentication")
    password: str = Field(..., description="Password for authentication")


class UserResponse(BaseModel):
    """Schema for user data in responses (without password)."""

    username: str = Field(..., description="Username of the user")

    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models


# Token Schemas
class Token(BaseModel):
    """Schema for JWT token responses."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenData(BaseModel):
    """Schema for token payload data."""

    username: Optional[str] = None


# Note Schemas
class NoteCreate(BaseModel):
    """Schema for note creation requests."""

    title: str = Field(
        ..., min_length=1, max_length=255, description="Title of the note"
    )
    content: str = Field(..., description="Markdown content of the note")


class NoteUpdate(BaseModel):
    """Schema for note update requests."""

    title: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Updated title of the note"
    )
    content: Optional[str] = Field(
        None, description="Updated markdown content of the note"
    )


class NoteResponse(BaseModel):
    """
    Schema for note data in responses.
    Matches the frontend Note interface exactly.
    """

    id: str = Field(..., description="Unique identifier for the note")
    title: str = Field(..., description="Title of the note")
    content: str = Field(..., description="Markdown content of the note")
    createdAt: str = Field(..., description="ISO timestamp when the note was created")
    updatedAt: str = Field(
        ..., description="ISO timestamp when the note was last updated"
    )

    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models


# Error Response Schemas
class ErrorResponse(BaseModel):
    """Schema for error responses."""

    detail: str = Field(..., description="Error message")


class ValidationErrorResponse(BaseModel):
    """Schema for validation error responses."""

    detail: str = Field(..., description="Validation error message")
    errors: Optional[list] = Field(
        None, description="List of specific validation errors"
    )


# Success Response Schemas
class MessageResponse(BaseModel):
    """Schema for simple message responses."""

    message: str = Field(..., description="Success or status message")


class DeleteResponse(BaseModel):
    """Schema for delete operation responses."""

    message: str = Field(..., description="Confirmation message")
    deleted_id: str = Field(..., description="ID of the deleted item")

