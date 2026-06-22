"""
Pydantic schemas for ParchMark backend API.
Defines request/response models for validation matching frontend data structures.
"""

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

TAG_PATTERN = re.compile(r"^[a-z0-9_-]+$")


def normalize_tag(value: str) -> str:
    """Normalize and validate one user-facing note tag."""
    tag = value.strip()
    if tag.startswith("#"):
        tag = tag[1:].strip()
    tag = re.sub(r"\s+", "-", tag.lower())

    if not tag:
        raise ValueError("Tag cannot be empty")
    if len(tag) > 64:
        raise ValueError("Tag must be at most 64 characters")
    if not TAG_PATTERN.fullmatch(tag):
        raise ValueError("Tag may contain only lowercase letters, numbers, hyphen, and underscore")
    return tag


def normalize_tags(values: list[str] | None) -> list[str] | None:
    """Normalize, deduplicate, and sort tags while preserving a stable API shape."""
    if values is None:
        return None

    normalized = {normalize_tag(value) for value in values}
    return sorted(normalized)


# User Schemas
class UserCreate(BaseModel):
    """Schema for user registration/creation requests."""

    username: str = Field(..., min_length=4, max_length=50, description="Username for the new user")
    password: str = Field(..., min_length=4, description="Password for the new user")


class UserLogin(BaseModel):
    """Schema for user login requests."""

    username: str = Field(..., min_length=4, description="Username for authentication")
    password: str = Field(..., min_length=4, description="Password for authentication")


class UserResponse(BaseModel):
    """Schema for user data in responses (without password)."""

    username: str = Field(..., description="Username of the user")

    model_config = ConfigDict(from_attributes=True)


# Token Schemas
class Token(BaseModel):
    """Schema for JWT token responses."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenData(BaseModel):
    """Schema for token payload data."""

    username: str | None = None


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str = Field(..., description="JWT refresh token")


# Note Schemas
class NoteCreate(BaseModel):
    """Schema for note creation requests."""

    content: str = Field(..., min_length=4, description="Markdown content of the note")
    title: str | None = Field(
        None,
        min_length=4,
        max_length=255,
        description="Optional title. If not provided, extracted from content H1.",
    )
    tags: list[str] | None = Field(
        None,
        description="Optional note tags. Values are normalized, deduplicated, and returned in sorted order.",
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, values: list[str] | None) -> list[str] | None:
        return normalize_tags(values)


class NoteUpdate(BaseModel):
    """Schema for note update requests."""

    title: str | None = Field(None, min_length=4, max_length=255, description="Updated title of the note")
    content: str | None = Field(None, min_length=4, description="Updated markdown content of the note")
    tags: list[str] | None = Field(
        None,
        description="Optional full replacement tag set. Omit or pass null to leave tags unchanged.",
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, values: list[str] | None) -> list[str] | None:
        return normalize_tags(values)


class NoteResponse(BaseModel):
    """
    Schema for note data in responses.
    Matches the frontend Note interface exactly.
    """

    id: str = Field(..., description="Unique identifier for the note")
    title: str = Field(..., description="Title of the note")
    content: str = Field(..., description="Markdown content of the note")
    tags: list[str] = Field(default_factory=list, description="Normalized note tags in stable sorted order")
    createdAt: str = Field(..., description="ISO timestamp when the note was created")
    updatedAt: str = Field(..., description="ISO timestamp when the note was last updated")

    model_config = ConfigDict(from_attributes=True)


# Success Response Schemas
class MessageResponse(BaseModel):
    """Schema for simple message responses."""

    message: str = Field(..., description="Success or status message")


class DeleteResponse(BaseModel):
    """Schema for delete operation responses."""

    message: str = Field(..., description="Confirmation message")
    deleted_id: str = Field(..., description="ID of the deleted item")


# Settings/Account Management Schemas
class PasswordChangeRequest(BaseModel):
    """Schema for password change requests."""

    current_password: str = Field(..., min_length=4, description="Current password for verification")
    new_password: str = Field(..., min_length=4, description="New password to set")


class AccountDeleteRequest(BaseModel):
    """Schema for account deletion requests."""

    password: str = Field(..., min_length=4, description="Password for confirmation")


class UserInfoResponse(BaseModel):
    """Schema for detailed user information responses."""

    username: str = Field(..., description="Username of the user")
    email: str | None = Field(None, description="Email address (from OIDC provider if applicable)")
    created_at: str = Field(..., description="ISO timestamp when the user was created")
    notes_count: int = Field(..., description="Number of notes the user has")
    auth_provider: str = Field(..., description="Authentication provider: 'local' or 'oidc'")

    model_config = ConfigDict(from_attributes=True)
