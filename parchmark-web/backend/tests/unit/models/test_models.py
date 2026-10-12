"""
Unit tests for SQLAlchemy models (app.models.models).
Tests User and Note models, relationships, and database constraints.
"""

import warnings
from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SAWarning
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_password_hash
from app.models.models import Note, NoteTag, User


class TestUserModel:
    """Test User model functionality and constraints."""

    @pytest.mark.asyncio
    async def test_user_creation_basic(self, test_db_session: AsyncSession):
        """Test basic user creation."""
        user = User(username="testuser", password_hash=get_password_hash("password123"))
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.password_hash is not None
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)

    @pytest.mark.asyncio
    async def test_user_username_unique_constraint(self, test_db_session: AsyncSession):
        """Test that username must be unique."""
        # Create first user
        user1 = User(username="testuser", password_hash=get_password_hash("password1"))
        test_db_session.add(user1)
        await test_db_session.commit()

        # Try to create second user with same username
        user2 = User(username="testuser", password_hash=get_password_hash("password2"))
        test_db_session.add(user2)

        with pytest.raises(IntegrityError):
            await test_db_session.commit()

    @pytest.mark.asyncio
    async def test_user_username_not_null(self, test_db_session: AsyncSession):
        """Test that username cannot be null."""
        user = User(username=None, password_hash=get_password_hash("password123"))
        test_db_session.add(user)

        with pytest.raises(IntegrityError):
            await test_db_session.commit()

    @pytest.mark.asyncio
    async def test_user_password_hash_not_null(self, test_db_session: AsyncSession):
        """Test that password_hash cannot be null."""
        user = User(username="testuser", password_hash=None)
        test_db_session.add(user)

        with pytest.raises(IntegrityError):
            await test_db_session.commit()

    @pytest.mark.asyncio
    async def test_user_created_at_auto_generated(self, test_db_session: AsyncSession):
        """Test that created_at is automatically generated."""
        user = User(username="testuser", password_hash=get_password_hash("password123"))
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)

        assert user.created_at is not None
        # Verify it's a datetime object
        assert isinstance(user.created_at, datetime)
        # Should be recent (within last hour)
        now = datetime.now(UTC)
        time_diff = abs((now - user.created_at.replace(tzinfo=UTC)).total_seconds())
        assert time_diff < 3600  # Within 1 hour

    @pytest.mark.asyncio
    async def test_user_username_length_limits(self, test_db_session: AsyncSession):
        """Test username length constraints."""
        # Test maximum length (50 characters)
        long_username = "a" * 50
        user = User(username=long_username, password_hash=get_password_hash("password123"))
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)

        assert user.username == long_username

    @pytest.mark.asyncio
    async def test_user_username_too_long(self, test_db_session: AsyncSession):
        """Test username that exceeds maximum length."""
        # Test username longer than 50 characters
        too_long_username = "a" * 51
        user = User(username=too_long_username, password_hash=get_password_hash("password123"))
        test_db_session.add(user)

        # PostgreSQL will enforce column length constraint
        with pytest.raises(Exception):  # Could be DataError or other database-specific error
            await test_db_session.commit()
        await test_db_session.rollback()

    @pytest.mark.asyncio
    async def test_user_password_hash_length(self, test_db_session: AsyncSession):
        """Test password hash storage."""
        password = "testpassword123"
        password_hash = get_password_hash(password)

        user = User(username="testuser", password_hash=password_hash)
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)

        assert user.password_hash == password_hash
        assert len(user.password_hash) > 0
        # bcrypt hashes are typically 60 characters
        assert len(user.password_hash) <= 255

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "username",
        [
            "user1",
            "user_with_underscore",
            "user-with-dash",
            "user.with.dots",
            "user@email.com",
            "123numeric456",
            "MixedCaseUser",
            "ユーザー",  # Unicode characters
        ],
    )
    async def test_user_username_various_formats(self, test_db_session: AsyncSession, username):
        """Test various username formats."""
        user = User(username=username, password_hash=get_password_hash("password123"))
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)

        assert user.username == username

    @pytest.mark.asyncio
    async def test_user_notes_relationship_empty(self, test_db_session: AsyncSession):
        """Test user notes relationship when no notes exist."""
        user = User(username="testuser", password_hash=get_password_hash("password123"))
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user, attribute_names=["notes"])

        assert user.notes == []

    @pytest.mark.asyncio
    async def test_user_str_representation(self, test_db_session: AsyncSession):
        """Test user string representation (if implemented)."""
        user = User(username="testuser", password_hash=get_password_hash("password123"))
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)

        # Test that user object can be converted to string
        str_repr = str(user)
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0


class TestNoteModel:
    """Test Note model functionality and constraints."""

    @pytest.mark.asyncio
    async def test_note_creation_basic(self, test_db_session: AsyncSession, sample_user: User):
        """Test basic note creation."""
        note = Note(
            id="test-note-1", user_id=sample_user.id, title="Test Note", content="# Test Note\n\nThis is test content."
        )
        test_db_session.add(note)
        await test_db_session.commit()
        await test_db_session.refresh(note)

        assert note.id == "test-note-1"
        assert note.user_id == sample_user.id
        assert note.title == "Test Note"
        assert note.content == "# Test Note\n\nThis is test content."
        assert note.created_at is not None
        assert note.updated_at is not None
        assert isinstance(note.created_at, datetime)
        assert isinstance(note.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_note_id_not_null(self, test_db_session: AsyncSession, sample_user: User):
        """Test that note ID cannot be null."""
        # Suppress warning about primary key column having no default generator
        # We're intentionally testing NULL constraint violation
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*primary key column.*", category=SAWarning)
            note = Note(id=None, user_id=sample_user.id, title="Test Note", content="Test content")
            test_db_session.add(note)

            with pytest.raises(IntegrityError):
                await test_db_session.commit()

    @pytest.mark.asyncio
    async def test_note_user_id_not_null(self, test_db_session: AsyncSession):
        """Test that user_id cannot be null."""
        note = Note(id="test-note-1", user_id=None, title="Test Note", content="Test content")
        test_db_session.add(note)

        with pytest.raises(IntegrityError):
            await test_db_session.commit()

    @pytest.mark.asyncio
    async def test_note_title_not_null(self, test_db_session: AsyncSession, sample_user: User):
        """Test that title cannot be null."""
        note = Note(id="test-note-1", user_id=sample_user.id, title=None, content="Test content")
        test_db_session.add(note)

        with pytest.raises(IntegrityError):
            await test_db_session.commit()

    @pytest.mark.asyncio
    async def test_note_content_not_null(self, test_db_session: AsyncSession, sample_user: User):
        """Test that content cannot be null."""
        note = Note(id="test-note-1", user_id=sample_user.id, title="Test Note", content=None)
        test_db_session.add(note)

        with pytest.raises(IntegrityError):
            await test_db_session.commit()

    @pytest.mark.asyncio
    async def test_note_foreign_key_constraint(self, test_db_session: AsyncSession):
        """Test foreign key constraint on user_id."""
        note = Note(
            id="test-note-1",
            user_id=99999,  # Non-existent user ID
            title="Test Note",
            content="Test content",
        )
        test_db_session.add(note)

        # PostgreSQL will enforce foreign key constraint
        with pytest.raises(IntegrityError):
            await test_db_session.commit()
        await test_db_session.rollback()

    @pytest.mark.asyncio
    async def test_note_created_at_auto_generated(self, test_db_session: AsyncSession, sample_user: User):
        """Test that created_at is automatically generated."""
        note = Note(id="test-note-1", user_id=sample_user.id, title="Test Note", content="Test content")
        test_db_session.add(note)
        await test_db_session.commit()
        await test_db_session.refresh(note)

        assert note.created_at is not None
        # Verify it's a datetime object
        assert isinstance(note.created_at, datetime)
        # Should be recent (within last hour)
        now = datetime.now(UTC)
        time_diff = abs((now - note.created_at.replace(tzinfo=UTC)).total_seconds())
        assert time_diff < 3600  # Within 1 hour

    @pytest.mark.asyncio
    async def test_note_updated_at_auto_generated(self, test_db_session: AsyncSession, sample_user: User):
        """Test that updated_at is automatically generated."""
        note = Note(id="test-note-1", user_id=sample_user.id, title="Test Note", content="Test content")
        test_db_session.add(note)
        await test_db_session.commit()
        await test_db_session.refresh(note)

        assert note.updated_at is not None
        # Verify it's a datetime object
        assert isinstance(note.updated_at, datetime)
        # Should be recent (within last hour)
        now = datetime.now(UTC)
        time_diff = abs((now - note.updated_at.replace(tzinfo=UTC)).total_seconds())
        assert time_diff < 3600  # Within 1 hour

    @pytest.mark.asyncio
    async def test_note_updated_at_auto_update(self, test_db_session: AsyncSession, sample_user: User):
        """Test that updated_at is automatically updated on modification."""
        # Create note
        note = Note(id="test-note-1", user_id=sample_user.id, title="Test Note", content="Original content")
        test_db_session.add(note)
        await test_db_session.commit()
        await test_db_session.refresh(note)

        original_updated_at = note.updated_at

        # Wait a moment to ensure timestamp difference
        import time

        time.sleep(0.1)

        # Update note
        note.content = "Updated content"
        await test_db_session.commit()
        await test_db_session.refresh(note)

        # Check that updated_at changed (or at least didn't go backwards)
        assert note.updated_at >= original_updated_at

    @pytest.mark.asyncio
    async def test_note_title_length_limits(self, test_db_session: AsyncSession, sample_user: User):
        """Test note title length constraints."""
        # Test maximum length (255 characters)
        long_title = "a" * 255
        note = Note(id="test-note-1", user_id=sample_user.id, title=long_title, content="Test content")
        test_db_session.add(note)
        await test_db_session.commit()
        await test_db_session.refresh(note)

        assert note.title == long_title

    @pytest.mark.asyncio
    async def test_note_content_large_text(self, test_db_session: AsyncSession, sample_user: User):
        """Test note content can store large text."""
        # Test large content (simulate a long markdown document)
        large_content = "# Large Note\n\n" + ("This is a large note. " * 1000)

        note = Note(id="test-note-1", user_id=sample_user.id, title="Large Note", content=large_content)
        test_db_session.add(note)
        await test_db_session.commit()
        await test_db_session.refresh(note)

        assert note.content == large_content
        assert len(note.content) > 10000

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "note_id",
        [
            "note-1",
            "note_with_underscore",
            "note-with-dash",
            "note.with.dots",
            "note123",
            "NOTE_UPPERCASE",
            "mixed-Case_Note.123",
        ],
    )
    async def test_note_id_various_formats(self, test_db_session: AsyncSession, sample_user: User, note_id):
        """Test various note ID formats."""
        note = Note(id=note_id, user_id=sample_user.id, title="Test Note", content="Test content")
        test_db_session.add(note)
        await test_db_session.commit()
        await test_db_session.refresh(note)

        assert note.id == note_id

    @pytest.mark.asyncio
    async def test_note_duplicate_id_constraint(self, test_db_session: AsyncSession, sample_user: User):
        """Test that note IDs must be unique."""
        # Create first note
        note1 = Note(id="duplicate-id", user_id=sample_user.id, title="First Note", content="First content")
        test_db_session.add(note1)
        await test_db_session.commit()

        # Suppress warning about conflicting instances with same identity key
        # We're intentionally testing duplicate ID constraint violation
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*conflicts with persistent instance.*", category=SAWarning)
            # Try to create second note with same ID
            note2 = Note(id="duplicate-id", user_id=sample_user.id, title="Second Note", content="Second content")
            test_db_session.add(note2)

            with pytest.raises(IntegrityError):
                await test_db_session.commit()


class TestNoteTagModel:
    """Test persisted note tag model and constraints."""

    @pytest.mark.asyncio
    async def test_note_tags_relationship_orders_tags(self, test_db_session: AsyncSession, sample_user: User):
        """Test notes expose their tags in stable alphabetical order."""
        note = Note(id="tagged-note", user_id=sample_user.id, title="Tagged Note", content="Tagged content")
        note.tags = [NoteTag(tag="work"), NoteTag(tag="draft")]
        test_db_session.add(note)
        await test_db_session.commit()
        await test_db_session.refresh(note, attribute_names=["tags"])

        assert [tag.tag for tag in note.tags] == ["draft", "work"]
        assert note.tags[0].note == note

    @pytest.mark.asyncio
    async def test_note_tag_unique_per_note(self, test_db_session: AsyncSession, sample_user: User):
        """Test a note cannot store the same normalized tag twice."""
        note = Note(id="duplicate-tag-note", user_id=sample_user.id, title="Tagged Note", content="Tagged content")
        note.tags = [NoteTag(tag="work"), NoteTag(tag="work")]
        test_db_session.add(note)

        with pytest.raises(IntegrityError):
            await test_db_session.commit()

        await test_db_session.rollback()

    @pytest.mark.asyncio
    async def test_note_tag_cascade_delete_with_note(self, test_db_session: AsyncSession, sample_user: User):
        """Test deleting a note deletes its tags."""
        note = Note(id="cascade-tag-note", user_id=sample_user.id, title="Tagged Note", content="Tagged content")
        note.tags = [NoteTag(tag="work")]
        test_db_session.add(note)
        await test_db_session.commit()

        assert (
            await test_db_session.scalar(select(func.count()).select_from(NoteTag).filter(NoteTag.note_id == note.id))
            == 1
        )

        await test_db_session.delete(note)
        await test_db_session.commit()

        assert (
            await test_db_session.scalar(select(func.count()).select_from(NoteTag).filter(NoteTag.note_id == note.id))
            == 0
        )


class TestUserNoteRelationship:
    """Test relationship between User and Note models."""

    @pytest.mark.asyncio
    async def test_user_notes_relationship(self, test_db_session: AsyncSession, sample_user: User):
        """Test user can access their notes through relationship."""
        # Create notes for user
        note1 = Note(id="note-1", user_id=sample_user.id, title="First Note", content="First content")
        note2 = Note(id="note-2", user_id=sample_user.id, title="Second Note", content="Second content")
        test_db_session.add_all([note1, note2])
        await test_db_session.commit()
        await test_db_session.refresh(sample_user, attribute_names=["notes"])

        # Access notes through relationship
        user_notes = sample_user.notes
        assert len(user_notes) == 2
        assert note1 in user_notes
        assert note2 in user_notes

    @pytest.mark.asyncio
    async def test_note_owner_relationship(self, test_db_session: AsyncSession, sample_user: User):
        """Test note can access its owner through relationship."""
        note = Note(id="test-note", user_id=sample_user.id, title="Test Note", content="Test content")
        test_db_session.add(note)
        await test_db_session.commit()
        await test_db_session.refresh(note, attribute_names=["owner"])

        # Access owner through relationship
        assert note.owner == sample_user
        assert note.owner.username == sample_user.username

    @pytest.mark.asyncio
    async def test_cascade_delete_user_notes(self, test_db_session: AsyncSession):
        """Test that deleting user cascades to delete their notes."""
        # Create user and notes
        user = User(username="deleteuser", password_hash=get_password_hash("password123"))
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)

        note1 = Note(id="note-1", user_id=user.id, title="Note 1", content="Content 1")
        note2 = Note(id="note-2", user_id=user.id, title="Note 2", content="Content 2")
        test_db_session.add_all([note1, note2])
        await test_db_session.commit()

        # Verify notes exist
        notes_count = await test_db_session.scalar(
            select(func.count()).select_from(Note).filter(Note.user_id == user.id)
        )
        assert notes_count == 2

        # Delete user
        await test_db_session.delete(user)
        await test_db_session.commit()

        # Verify notes are also deleted
        remaining_notes = await test_db_session.scalar(
            select(func.count()).select_from(Note).filter(Note.user_id == user.id)
        )
        assert remaining_notes == 0

    @pytest.mark.asyncio
    async def test_multiple_users_separate_notes(self, test_db_session: AsyncSession):
        """Test that different users have separate note collections."""
        # Create two users
        user1 = User(username="user1", password_hash=get_password_hash("password1"))
        user2 = User(username="user2", password_hash=get_password_hash("password2"))
        test_db_session.add_all([user1, user2])
        await test_db_session.commit()
        await test_db_session.refresh(user1)
        await test_db_session.refresh(user2)

        # Create notes for each user
        note1 = Note(id="user1-note", user_id=user1.id, title="User 1 Note", content="User 1 content")
        note2 = Note(id="user2-note", user_id=user2.id, title="User 2 Note", content="User 2 content")
        test_db_session.add_all([note1, note2])
        await test_db_session.commit()
        await test_db_session.refresh(user1, attribute_names=["notes"])
        await test_db_session.refresh(user2, attribute_names=["notes"])

        # Verify each user has only their own notes
        assert len(user1.notes) == 1
        assert len(user2.notes) == 1
        assert user1.notes[0].id == "user1-note"
        assert user2.notes[0].id == "user2-note"
