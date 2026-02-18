"""
Unit tests for database initialization (app.database.init_db).
Tests database table creation and initialization functions.
"""

from unittest.mock import patch

import pytest
from sqlalchemy import inspect

from app.database.database import Base
from app.database.init_db import create_tables, init_database


class TestCreateTables:
    """Test create_tables function."""

    def test_create_tables_success(self, test_db_engine):
        """Test successful table creation."""
        # Clear any existing tables
        Base.metadata.drop_all(bind=test_db_engine)

        # Verify tables don't exist
        inspector = inspect(test_db_engine)
        existing_tables = inspector.get_table_names()
        assert "users" not in existing_tables
        assert "notes" not in existing_tables

        # Create tables
        with patch("app.database.init_db.engine", test_db_engine):
            create_tables()

        # Verify tables were created
        inspector = inspect(test_db_engine)
        existing_tables = inspector.get_table_names()
        assert "users" in existing_tables
        assert "notes" in existing_tables

    def test_create_tables_idempotent(self, test_db_engine):
        """Test that create_tables is idempotent (can be run multiple times)."""
        with patch("app.database.init_db.engine", test_db_engine):
            # Create tables first time
            create_tables()

            # Verify tables exist
            inspector = inspect(test_db_engine)
            tables_first = inspector.get_table_names()
            assert "users" in tables_first
            assert "notes" in tables_first

            # Create tables second time (should not error)
            create_tables()

            # Verify tables still exist
            inspector = inspect(test_db_engine)
            tables_second = inspector.get_table_names()
            assert tables_first == tables_second

    def test_create_tables_with_existing_data(self, test_db_engine, test_db_session):
        """Test create_tables preserves existing data."""
        from app.auth.auth import get_password_hash
        from app.models.models import User

        with patch("app.database.init_db.engine", test_db_engine):
            # Create tables and add data
            create_tables()

            user = User(username="testuser", password_hash=get_password_hash("password"))
            test_db_session.add(user)
            test_db_session.commit()

            # Run create_tables again
            create_tables()

            # Verify data still exists
            existing_user = test_db_session.query(User).filter(User.username == "testuser").first()
            assert existing_user is not None
            assert existing_user.username == "testuser"

    @patch("app.database.init_db.Base.metadata.create_all")
    @patch("app.database.init_db.engine")
    def test_create_tables_calls_metadata_create_all(self, mock_engine, mock_create_all):
        """Test that create_tables calls the correct SQLAlchemy method."""
        create_tables()

        mock_create_all.assert_called_once()
        # Verify it was called with the engine
        args, kwargs = mock_create_all.call_args
        assert "bind" in kwargs

    @patch("app.database.init_db.Base.metadata.create_all")
    @patch("app.database.init_db.engine")
    def test_create_tables_exception_handling(self, mock_engine, mock_create_all):
        """Test create_tables handles exceptions properly."""
        mock_create_all.side_effect = Exception("Database error")

        # Should re-raise the exception
        with pytest.raises(Exception) as exc_info:
            create_tables()

        assert "Database error" in str(exc_info.value)

    @patch("builtins.print")
    @patch("app.database.init_db.Base.metadata.create_all")
    @patch("app.database.init_db.engine")
    def test_create_tables_output_messages(self, mock_engine, mock_create_all, mock_print):
        """Test that create_tables prints appropriate messages."""
        create_tables()

        # Verify print statements were called
        assert mock_print.call_count >= 2

        # Check for expected messages
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Creating database tables" in msg for msg in print_calls)
        assert any("created successfully" in msg for msg in print_calls)


class TestInitDatabase:
    """Test init_database function."""

    @patch("app.database.init_db.create_tables")
    @patch("app.database.init_db.check_seeding_status")
    @patch("app.database.init_db.seed_database")
    def test_init_database_success_no_seeding_needed(self, mock_seed, mock_check_status, mock_create_tables):
        """Test successful database initialization when seeding not needed."""
        # Mock that seeding is already complete
        mock_check_status.return_value = {"seeding_complete": True}

        result = init_database()

        assert result is True
        mock_create_tables.assert_called_once()
        mock_check_status.assert_called_once()
        mock_seed.assert_not_called()

    @patch("app.database.init_db.create_tables")
    @patch("app.database.init_db.check_seeding_status")
    @patch("app.database.init_db.seed_database")
    def test_init_database_success_with_seeding(self, mock_seed, mock_check_status, mock_create_tables):
        """Test successful database initialization with seeding."""
        # Mock that seeding is needed
        mock_check_status.return_value = {"seeding_complete": False}
        mock_seed.return_value = True

        result = init_database()

        assert result is True
        mock_create_tables.assert_called_once()
        mock_check_status.assert_called_once()
        mock_seed.assert_called_once()

    @patch("app.database.init_db.create_tables")
    @patch("app.database.init_db.check_seeding_status")
    @patch("app.database.init_db.seed_database")
    def test_init_database_seeding_failure(self, mock_seed, mock_check_status, mock_create_tables):
        """Test database initialization when seeding fails."""
        mock_check_status.return_value = {"seeding_complete": False}
        mock_seed.return_value = False

        result = init_database()

        # Should still return True even if seeding fails
        assert result is True
        mock_create_tables.assert_called_once()
        mock_check_status.assert_called_once()
        mock_seed.assert_called_once()

    @patch("app.database.init_db.create_tables")
    def test_init_database_create_tables_exception(self, mock_create_tables):
        """Test database initialization when table creation fails."""
        mock_create_tables.side_effect = Exception("Table creation failed")

        result = init_database()

        assert result is False
        mock_create_tables.assert_called_once()

    @patch("app.database.init_db.create_tables")
    @patch("app.database.init_db.check_seeding_status")
    def test_init_database_check_seeding_exception(self, mock_check_status, mock_create_tables):
        """Test database initialization when seeding status check fails."""
        mock_check_status.side_effect = Exception("Status check failed")

        result = init_database()

        assert result is False
        mock_create_tables.assert_called_once()
        mock_check_status.assert_called_once()

    @patch("app.database.init_db.create_tables")
    @patch("app.database.init_db.check_seeding_status")
    @patch("app.database.init_db.seed_database")
    def test_init_database_seed_exception(self, mock_seed, mock_check_status, mock_create_tables):
        """Test database initialization when seeding raises exception."""
        mock_check_status.return_value = {"seeding_complete": False}
        mock_seed.side_effect = Exception("Seeding failed")

        result = init_database()

        assert result is False
        mock_create_tables.assert_called_once()
        mock_check_status.assert_called_once()
        mock_seed.assert_called_once()

    @patch("builtins.print")
    @patch("app.database.init_db.create_tables")
    @patch("app.database.init_db.check_seeding_status")
    @patch("app.database.init_db.seed_database")
    def test_init_database_output_messages(self, mock_seed, mock_check_status, mock_create_tables, mock_print):
        """Test that init_database prints appropriate messages."""
        mock_check_status.return_value = {"seeding_complete": False}
        mock_seed.return_value = True

        init_database()

        # Verify print statements include expected messages
        print_calls = [call[0][0] for call in mock_print.call_args_list]

        # Should have messages about seeding
        assert any("not seeded" in msg for msg in print_calls)
        assert any("Seeding with default data" in msg for msg in print_calls)

    @patch("builtins.print")
    @patch("app.database.init_db.create_tables")
    @patch("app.database.init_db.check_seeding_status")
    def test_init_database_already_seeded_message(self, mock_check_status, mock_create_tables, mock_print):
        """Test message when database is already seeded."""
        mock_check_status.return_value = {"seeding_complete": True}

        init_database()

        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("already seeded" in msg for msg in print_calls)
        assert any("Skipping seeding" in msg for msg in print_calls)

    @patch("builtins.print")
    @patch("app.database.init_db.create_tables")
    def test_init_database_error_message(self, mock_create_tables, mock_print):
        """Test error message when initialization fails."""
        mock_create_tables.side_effect = Exception("Test error")

        init_database()

        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Error initializing database" in msg for msg in print_calls)

    def test_init_database_integration(self, test_db_engine):
        """Test init_database integration with real database."""
        with patch("app.database.init_db.engine", test_db_engine):
            # Clear any existing tables
            Base.metadata.drop_all(bind=test_db_engine)

            # Run initialization
            result = init_database()

            # Should succeed
            assert result is True

            # Verify tables were created
            inspector = inspect(test_db_engine)
            existing_tables = inspector.get_table_names()
            assert "users" in existing_tables
            assert "notes" in existing_tables

    def test_init_database_multiple_calls(self, test_db_engine):
        """Test that init_database can be called multiple times safely."""
        with patch("app.database.init_db.engine", test_db_engine):
            # First call
            result1 = init_database()
            assert result1 is True

            # Second call should also succeed
            result2 = init_database()
            assert result2 is True

            # Tables should still exist
            inspector = inspect(test_db_engine)
            existing_tables = inspector.get_table_names()
            assert "users" in existing_tables
            assert "notes" in existing_tables


class TestInitDatabaseScript:
    """Test init_database as a script."""

    @patch("app.database.init_db.init_database")
    def test_script_execution(self, mock_init):
        """Test running init_db.py as a script."""
        mock_init.return_value = True

        # Import and run the script's main block
        import app.database.init_db

        # The if __name__ == "__main__" block should call init_database
        # We can't directly test this without actually running the script,
        # but we can verify the function exists and is callable
        assert callable(app.database.init_db.init_database)

    def test_script_imports(self):
        """Test that the script imports are working correctly."""
        import app.database.init_db

        # Verify all necessary imports are available
        assert hasattr(app.database.init_db, "Base")
        assert hasattr(app.database.init_db, "engine")
        assert hasattr(app.database.init_db, "seed_database")
        assert hasattr(app.database.init_db, "check_seeding_status")
        assert hasattr(app.database.init_db, "create_tables")
        assert hasattr(app.database.init_db, "init_database")


class TestDatabaseInitializationEdgeCases:
    """Test edge cases in database initialization."""

    def test_init_database_partial_failure_recovery(self, test_db_engine):
        """Test recovery from partial initialization failure."""
        with patch("app.database.init_db.engine", test_db_engine):
            # First, create tables successfully
            Base.metadata.create_all(bind=test_db_engine)

            # Mock seeding to fail first time, succeed second time
            with patch("app.database.init_db.seed_database") as mock_seed:
                mock_seed.side_effect = [False, True]  # Fail then succeed

                # First call should still return True even with seeding failure
                result1 = init_database()
                assert result1 is True

                # Second call should succeed with seeding
                result2 = init_database()
                assert result2 is True

    @patch("app.database.init_db.create_tables")
    @patch("app.database.init_db.check_seeding_status")
    def test_init_database_seeding_status_invalid_format(self, mock_check_status, mock_create_tables):
        """Test handling of invalid seeding status format."""
        # Return invalid status format
        mock_check_status.return_value = {"invalid": "format"}

        result = init_database()

        # Should handle gracefully (treat as not seeded)
        assert result is True
        mock_create_tables.assert_called_once()
        mock_check_status.assert_called_once()

    def test_init_database_empty_database_file(self, test_db_engine):
        """Test initialization with empty database file."""
        with patch("app.database.init_db.engine", test_db_engine):
            # Start with completely empty database
            result = init_database()

            assert result is True

            # Verify proper initialization
            inspector = inspect(test_db_engine)
            tables = inspector.get_table_names()
            assert len(tables) >= 2  # At least users and notes tables
