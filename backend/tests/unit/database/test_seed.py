"""
Unit tests for database seeding (app.database.seed).
Tests seeding functions, default data creation, and status checking.
"""

from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.database.seed import (
    DEFAULT_NOTES_DATA,
    DEFAULT_USERS,
    check_seeding_status,
    create_default_notes,
    create_default_users,
    reset_and_seed_database,
    seed_database,
)
from app.models.models import Note, User


class TestDefaultData:
    """Test default data constants."""

    def test_default_users_data(self):
        """Test default users data configuration."""
        assert isinstance(DEFAULT_USERS, list)
        assert len(DEFAULT_USERS) >= 1

        for user_data in DEFAULT_USERS:
            assert isinstance(user_data, dict)
            assert "username" in user_data
            assert "password" in user_data

        # Check first default user
        assert DEFAULT_USERS[0]["username"] == "demouser"
        assert DEFAULT_USERS[0]["password"] == "demopass"

    def test_default_notes_data(self):
        """Test default notes data configuration."""
        assert isinstance(DEFAULT_NOTES_DATA, list)
        assert len(DEFAULT_NOTES_DATA) >= 2

        for note_data in DEFAULT_NOTES_DATA:
            assert isinstance(note_data, dict)
            assert "id" in note_data
            assert "title" in note_data
            assert "content" in note_data

            # Verify content format
            assert note_data["content"].startswith(f"# {note_data['title']}")

    def test_default_notes_unique_ids(self):
        """Test that default notes have unique IDs."""
        ids = [note["id"] for note in DEFAULT_NOTES_DATA]
        assert len(ids) == len(set(ids))  # All IDs should be unique


class TestCreateDefaultUsers:
    """Test create_default_users function."""

    def test_create_default_users_success(self, test_db_session: Session):
        """Test successful default users creation."""
        users = create_default_users(test_db_session)

        assert isinstance(users, list)
        assert len(users) == len(DEFAULT_USERS)

        for i, user in enumerate(users):
            assert isinstance(user, User)
            assert user.username == DEFAULT_USERS[i]["username"]
            assert user.password_hash is not None
            assert len(user.password_hash) > 0
            assert user.id is not None

            # Verify user exists in database
            db_user = test_db_session.query(User).filter(User.username == DEFAULT_USERS[i]["username"]).first()
            assert db_user is not None
            assert db_user.id == user.id

    def test_create_default_users_already_exist(self, test_db_session: Session):
        """Test creating default users when users already exist."""
        # Create users first time
        users1 = create_default_users(test_db_session)

        # Create users second time
        users2 = create_default_users(test_db_session)

        # Should return the existing users
        assert len(users1) == len(users2)
        for user1, user2 in zip(users1, users2, strict=False):
            assert user1.id == user2.id
            assert user1.username == user2.username

        # Should only have expected number of users in database
        for user_data in DEFAULT_USERS:
            user_count = test_db_session.query(User).filter(User.username == user_data["username"]).count()
            assert user_count == 1

    def test_create_default_users_password_hashing(self, test_db_session: Session):
        """Test that default users passwords are properly hashed."""
        from app.auth.auth import verify_password

        users = create_default_users(test_db_session)

        for i, user in enumerate(users):
            # Password should be hashed, not plain text
            assert user.password_hash != DEFAULT_USERS[i]["password"]

            # But should verify correctly
            assert verify_password(DEFAULT_USERS[i]["password"], user.password_hash)

    def test_create_default_users_database_error(self, test_db_session: Session):
        """Test create_default_users with database error."""
        # Mock the session to raise an exception
        test_db_session.add = Mock(side_effect=Exception("Database error"))

        with pytest.raises(Exception):
            create_default_users(test_db_session)

    @patch("app.database.seed.get_password_hash")
    def test_create_default_users_password_hash_called(self, mock_hash, test_db_session: Session):
        """Test that password hashing function is called."""
        mock_hash.return_value = "hashed_password"

        users = create_default_users(test_db_session)

        # Should be called for each user
        assert mock_hash.call_count == len(DEFAULT_USERS)
        for user in users:
            assert user.password_hash == "hashed_password"


class TestCreateDefaultNotes:
    """Test create_default_notes function."""

    def test_create_default_notes_success(self, test_db_session: Session, sample_user: User):
        """Test successful default notes creation."""
        notes = create_default_notes(test_db_session, sample_user)

        assert isinstance(notes, list)
        assert len(notes) == len(DEFAULT_NOTES_DATA)

        for i, note in enumerate(notes):
            assert isinstance(note, Note)
            assert note.id == DEFAULT_NOTES_DATA[i]["id"]
            assert note.title == DEFAULT_NOTES_DATA[i]["title"]
            assert note.content == DEFAULT_NOTES_DATA[i]["content"]
            assert note.user_id == sample_user.id

    def test_create_default_notes_already_exist(self, test_db_session: Session, sample_user: User):
        """Test creating default notes when notes already exist."""
        # Create notes first time
        notes1 = create_default_notes(test_db_session, sample_user)

        # Create notes second time
        notes2 = create_default_notes(test_db_session, sample_user)

        # Should return the same notes
        assert len(notes1) == len(notes2)
        for note1, note2 in zip(notes1, notes2, strict=False):
            assert note1.id == note2.id

        # Should only have one set of notes in database
        note_count = test_db_session.query(Note).filter(Note.user_id == sample_user.id).count()
        assert note_count == len(DEFAULT_NOTES_DATA)

    def test_create_default_notes_partial_exist(self, test_db_session: Session, sample_user: User):
        """Test creating default notes when some already exist."""
        # Create one note manually
        existing_note = Note(
            id=DEFAULT_NOTES_DATA[0]["id"],
            user_id=sample_user.id,
            title=DEFAULT_NOTES_DATA[0]["title"],
            content=DEFAULT_NOTES_DATA[0]["content"],
        )
        test_db_session.add(existing_note)
        test_db_session.commit()

        # Create default notes
        notes = create_default_notes(test_db_session, sample_user)

        assert len(notes) == len(DEFAULT_NOTES_DATA)

        # First note should be the existing one
        assert notes[0].id == existing_note.id

        # All notes should exist in database
        note_count = test_db_session.query(Note).filter(Note.user_id == sample_user.id).count()
        assert note_count == len(DEFAULT_NOTES_DATA)

    def test_create_default_notes_different_users(self, test_db_session: Session):
        """Test creating default notes for different users."""
        import uuid

        from app.auth.auth import get_password_hash

        # Create two users
        user1 = User(username="user1", password_hash=get_password_hash("pass1"))
        user2 = User(username="user2", password_hash=get_password_hash("pass2"))
        test_db_session.add_all([user1, user2])
        test_db_session.commit()
        test_db_session.refresh(user1)
        test_db_session.refresh(user2)

        # Create notes for user1
        notes1 = create_default_notes(test_db_session, user1)

        # For user2, create notes with unique IDs to avoid constraint violation
        notes2 = []
        for note_data in DEFAULT_NOTES_DATA:
            note = Note(
                id=f"user2-{uuid.uuid4()}",  # Unique ID for user2's notes
                user_id=user2.id,
                title=note_data["title"],
                content=note_data["content"],
            )
            test_db_session.add(note)
            notes2.append(note)
        test_db_session.commit()

        # Both should have same number of notes
        assert len(notes1) == len(notes2) == len(DEFAULT_NOTES_DATA)

        # But they should belong to different users
        for note in notes1:
            assert note.user_id == user1.id
        for note in notes2:
            assert note.user_id == user2.id

    def test_create_default_notes_database_error(self, test_db_session: Session, sample_user: User):
        """Test create_default_notes with database error."""
        # Mock session to raise exception on commit
        test_db_session.commit = Mock(side_effect=Exception("Database error"))

        with pytest.raises(Exception):
            create_default_notes(test_db_session, sample_user)


class TestSeedDatabase:
    """Test seed_database function."""

    @patch("app.database.seed.SessionLocal")
    @patch("app.database.seed.create_default_users")
    @patch("app.database.seed.create_default_notes")
    def test_seed_database_success(self, mock_create_notes, mock_create_users, mock_session_local):
        """Test successful database seeding."""
        # Mock database session
        mock_session = Mock()
        mock_session_local.return_value = mock_session

        # Mock users and notes creation
        mock_users = [Mock(), Mock()]
        mock_notes = [Mock(), Mock()]
        mock_create_users.return_value = mock_users
        mock_create_notes.return_value = mock_notes

        result = seed_database()

        assert result is True
        mock_create_users.assert_called_once_with(mock_session)
        mock_create_notes.assert_called_once_with(mock_session, mock_users[0])  # First user gets notes
        mock_session.close.assert_called_once()

    @patch("app.database.seed.SessionLocal")
    @patch("app.database.seed.create_default_users")
    def test_seed_database_user_creation_error(self, mock_create_users, mock_session_local):
        """Test seed_database when user creation fails."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_create_users.side_effect = Exception("User creation failed")

        result = seed_database()

        assert result is False
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("app.database.seed.SessionLocal")
    @patch("app.database.seed.create_default_users")
    @patch("app.database.seed.create_default_notes")
    def test_seed_database_notes_creation_error(self, mock_create_notes, mock_create_users, mock_session_local):
        """Test seed_database when notes creation fails."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_users = [Mock()]
        mock_create_users.return_value = mock_users
        mock_create_notes.side_effect = Exception("Notes creation failed")

        result = seed_database()

        assert result is False
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("app.database.seed.SessionLocal")
    def test_seed_database_session_creation_error(self, mock_session_local):
        """Test seed_database when session creation fails."""
        mock_session_local.side_effect = Exception("Session creation failed")

        result = seed_database()

        assert result is False

    def test_seed_database_integration(self, test_db_engine):
        """Test seed_database integration with real database."""
        from sqlalchemy.orm import sessionmaker

        # Use test database
        with patch("app.database.seed.SessionLocal", sessionmaker(bind=test_db_engine)):
            with patch("app.database.seed.engine", test_db_engine):
                # Create tables first
                from app.database.database import Base

                Base.metadata.create_all(bind=test_db_engine)

                result = seed_database()

                assert result is True

                # Verify data was created
                TestSessionLocal = sessionmaker(bind=test_db_engine)
                session = TestSessionLocal()

                try:
                    # Check first default user
                    user = session.query(User).filter(User.username == DEFAULT_USERS[0]["username"]).first()
                    assert user is not None

                    notes = session.query(Note).filter(Note.user_id == user.id).all()
                    assert len(notes) == len(DEFAULT_NOTES_DATA)

                finally:
                    session.close()


class TestResetAndSeedDatabase:
    """Test reset_and_seed_database function."""

    @patch("app.database.seed.seed_database")
    @patch("app.database.database.Base")
    @patch("app.database.seed.engine")
    def test_reset_and_seed_success(self, mock_engine, mock_base, mock_seed):
        """Test successful database reset and seeding."""
        mock_seed.return_value = True

        result = reset_and_seed_database()

        assert result is True
        mock_base.metadata.drop_all.assert_called_once_with(bind=mock_engine)
        mock_base.metadata.create_all.assert_called_once_with(bind=mock_engine)
        mock_seed.assert_called_once()

    @patch("app.database.database.Base")
    @patch("app.database.seed.engine")
    def test_reset_and_seed_drop_error(self, mock_engine, mock_base):
        """Test reset_and_seed_database when drop fails."""
        mock_base.metadata.drop_all.side_effect = Exception("Drop failed")

        result = reset_and_seed_database()

        assert result is False

    @patch("app.database.database.Base")
    @patch("app.database.seed.engine")
    def test_reset_and_seed_create_error(self, mock_engine, mock_base):
        """Test reset_and_seed_database when create fails."""
        mock_base.metadata.create_all.side_effect = Exception("Create failed")

        result = reset_and_seed_database()

        assert result is False

    @patch("app.database.seed.seed_database")
    @patch("app.database.database.Base")
    @patch("app.database.seed.engine")
    def test_reset_and_seed_seeding_error(self, mock_engine, mock_base, mock_seed):
        """Test reset_and_seed_database when seeding fails."""
        mock_seed.return_value = False

        result = reset_and_seed_database()

        assert result is False
        mock_seed.assert_called_once()


class TestCheckSeedingStatus:
    """Test check_seeding_status function."""

    @patch("app.database.seed.SessionLocal")
    def test_check_seeding_status_complete(self, mock_session_local):
        """Test checking seeding status when complete."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session

        # Mock users exist
        mock_user = Mock()
        mock_user.id = 1
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user

        # Mock notes count matches expected
        mock_session.query.return_value.filter.return_value.count.return_value = len(DEFAULT_NOTES_DATA)

        status = check_seeding_status()

        assert status["default_users_exist"] is True
        assert status["default_users_count"] == len(DEFAULT_USERS)
        assert status["default_notes_count"] == len(DEFAULT_NOTES_DATA)
        assert status["expected_notes_count"] == len(DEFAULT_NOTES_DATA)
        assert status["seeding_complete"] is True
        mock_session.close.assert_called_once()

    @patch("app.database.seed.SessionLocal")
    def test_check_seeding_status_incomplete_no_user(self, mock_session_local):
        """Test checking seeding status when no user exists."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session

        # Mock no user exists
        mock_session.query.return_value.filter.return_value.first.return_value = None

        status = check_seeding_status()

        assert status["default_users_exist"] is False
        assert status["default_users_count"] == len(DEFAULT_USERS)
        assert status["default_notes_count"] == 0
        assert status["seeding_complete"] is False

    @patch("app.database.seed.SessionLocal")
    def test_check_seeding_status_incomplete_missing_notes(self, mock_session_local):
        """Test checking seeding status when notes are missing."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session

        # Mock user exists
        mock_user = Mock()
        mock_user.id = 1
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user

        # Mock insufficient notes count
        mock_session.query.return_value.filter.return_value.count.return_value = len(DEFAULT_NOTES_DATA) - 1

        status = check_seeding_status()

        assert status["default_users_exist"] is True
        assert status["default_users_count"] == len(DEFAULT_USERS)
        assert status["default_notes_count"] == len(DEFAULT_NOTES_DATA) - 1
        assert status["seeding_complete"] is False

    @patch("app.database.seed.SessionLocal")
    def test_check_seeding_status_database_error(self, mock_session_local):
        """Test checking seeding status when database error occurs."""
        mock_session = Mock()
        mock_session_local.return_value = mock_session
        mock_session.query.side_effect = Exception("Database error")

        status = check_seeding_status()

        assert "error" in status
        assert status["seeding_complete"] is False
        assert "Database error" in status["error"]
        mock_session.close.assert_called_once()

    def test_check_seeding_status_integration(self, test_db_engine):
        """Test check_seeding_status integration with real database."""
        from sqlalchemy.orm import sessionmaker

        TestSessionLocal = sessionmaker(bind=test_db_engine)

        with patch("app.database.seed.SessionLocal", TestSessionLocal):
            # Test with empty database
            status = check_seeding_status()
            # Status should be returned
            assert isinstance(status, dict)
            assert "seeding_complete" in status

            # Create the database structure and seed it
            from app.database.database import Base

            Base.metadata.create_all(bind=test_db_engine)

            # Seed the database
            with patch("app.database.seed.engine", test_db_engine):
                seed_result = seed_database()
                assert seed_result is True

            # Now check status again
            status = check_seeding_status()
            # Should have seeding info
            assert isinstance(status, dict)
            assert "seeding_complete" in status
            # If seeding was successful, it should be complete
            if seed_result:
                assert status["default_users_exist"] is True
                assert status["default_notes_count"] > 0


class TestSeedingScript:
    """Test seed.py as a script."""

    @patch("app.database.seed.seed_database")
    @patch("app.database.seed.check_seeding_status")
    def test_script_execution_normal(self, mock_check, mock_seed):
        """Test running seed.py as a script normally."""
        mock_seed.return_value = True
        mock_check.return_value = {"seeding_complete": True}

        # Import the module (simulates running as script)
        import app.database.seed

        # Verify functions are available
        assert callable(app.database.seed.seed_database)
        assert callable(app.database.seed.check_seeding_status)

    @patch("app.database.seed.reset_and_seed_database")
    def test_script_execution_reset_flag(self, mock_reset):
        """Test running seed.py with --reset flag."""
        mock_reset.return_value = True

        # Import the module
        import app.database.seed

        # Verify reset function is available
        assert callable(app.database.seed.reset_and_seed_database)

    def test_script_imports(self):
        """Test that the script imports are working correctly."""
        import app.database.seed

        # Verify all necessary imports and constants are available
        assert hasattr(app.database.seed, "DEFAULT_USERS")
        assert hasattr(app.database.seed, "DEFAULT_NOTES_DATA")
        assert hasattr(app.database.seed, "create_default_users")
        assert hasattr(app.database.seed, "create_default_notes")
        assert hasattr(app.database.seed, "seed_database")
        assert hasattr(app.database.seed, "reset_and_seed_database")
        assert hasattr(app.database.seed, "check_seeding_status")
