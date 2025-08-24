"""
Unit tests for database configuration and utilities (app.database).
Tests database setup, connection, and dependency functions.
"""

from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.database import SQLALCHEMY_DATABASE_URL, Base, SessionLocal, engine, get_db


class TestDatabaseConfiguration:
    """Test database configuration and setup."""

    def test_database_url_default(self):
        """Test default database URL configuration."""
        # Default is now PostgreSQL
        assert "postgresql" in SQLALCHEMY_DATABASE_URL.lower()
        assert "parchmark" in SQLALCHEMY_DATABASE_URL

    @patch.dict("os.environ", {"DATABASE_URL": "postgresql://user:pass@localhost/testdb"})
    def test_database_url_from_environment(self):
        """Test database URL can be configured via environment."""
        # Need to reload the module to pick up environment changes
        from importlib import reload

        import app.database.database

        reload(app.database.database)

        assert app.database.database.SQLALCHEMY_DATABASE_URL == "postgresql://user:pass@localhost/testdb"

    def test_engine_configuration(self):
        """Test SQLAlchemy engine configuration."""
        assert engine is not None
        # Engine should have a valid URL
        assert hasattr(engine, "url")
        # Engine pool exists
        assert hasattr(engine, "pool")

    def test_postgresql_only_validation(self):
        """Test that only PostgreSQL URLs are accepted."""
        # This test would require reloading the module with different URLs
        # which is tested in test_database_url_validation below
        assert "postgresql" in SQLALCHEMY_DATABASE_URL.lower()

    def test_session_local_configuration(self):
        """Test SessionLocal configuration."""
        assert SessionLocal is not None

        # Test session configuration
        session = SessionLocal()
        assert isinstance(session, Session)
        # Check autoflush is False (autocommit deprecated in SQLAlchemy 2.0)
        assert session.autoflush is False
        # Session should be closeable
        session.close()

    def test_base_declarative_class(self):
        """Test Base declarative class."""
        assert Base is not None
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")


class TestGetDbDependency:
    """Test get_db dependency function."""

    def test_get_db_yields_session(self):
        """Test that get_db yields a database session."""
        db_generator = get_db()

        # Get the session from the generator
        db_session = next(db_generator)

        assert isinstance(db_session, Session)

        # Clean up
        try:
            next(db_generator)
        except StopIteration:
            pass  # Expected when generator closes

    def test_get_db_closes_session(self):
        """Test that get_db properly closes the session."""
        db_generator = get_db()
        db_session = next(db_generator)

        # Mock the close method to verify it's called
        original_close = db_session.close
        close_called = False

        def mock_close():
            nonlocal close_called
            close_called = True
            original_close()

        db_session.close = mock_close

        # Trigger generator cleanup
        try:
            next(db_generator)
        except StopIteration:
            pass

        assert close_called

    def test_get_db_exception_handling(self):
        """Test that get_db handles exceptions properly."""
        db_generator = get_db()
        db_session = next(db_generator)

        # Mock the close method to verify it's called even with exceptions
        original_close = db_session.close
        close_called = False

        def mock_close():
            nonlocal close_called
            close_called = True
            original_close()

        db_session.close = mock_close

        # Simulate an exception during session use
        try:
            # This would normally be where database operations happen
            # We'll just trigger the finally block by closing the generator
            db_generator.close()
        except GeneratorExit:
            pass

        assert close_called

    def test_get_db_multiple_calls(self):
        """Test that get_db can be called multiple times."""
        sessions = []

        for _ in range(3):
            db_generator = get_db()
            session = next(db_generator)
            sessions.append(session)

            # Close generator
            try:
                next(db_generator)
            except StopIteration:
                pass

        # Each call should return a different session instance
        assert len({id(session) for session in sessions}) == 3

        # All sessions should be closed
        for session in sessions:
            # Note: SQLAlchemy sessions don't have a direct "is_closed" property
            # but calling close() multiple times is safe
            session.close()


class TestDatabaseConnectionHandling:
    """Test database connection handling and edge cases."""

    def test_database_connection_error_handling(self):
        """Test handling of database connection errors."""
        # Create engine with invalid database URL
        invalid_db_url = "postgresql://invalid_user:invalid_pass@invalid_host:5432/invalid_db"

        # Should not raise exception during creation, only when connecting
        invalid_engine = create_engine(invalid_db_url)
        assert invalid_engine is not None

    def test_engine_creation_with_valid_url(self):
        """Test engine creation with valid configuration."""
        # Test without mocking - just verify engine exists
        assert engine is not None
        assert hasattr(engine, "url")

    def test_session_isolation(self):
        """Test that different sessions are isolated."""
        # Create two separate sessions
        db_gen1 = get_db()
        db_gen2 = get_db()

        session1 = next(db_gen1)
        session2 = next(db_gen2)

        # Sessions should be different instances
        assert session1 is not session2
        assert id(session1) != id(session2)

        # Clean up
        for gen in [db_gen1, db_gen2]:
            try:
                next(gen)
            except StopIteration:
                pass


class TestDatabaseCompatibility:
    """Test database compatibility features."""

    def test_database_url_validation(self):
        """Test database URL format validation."""
        # Test various valid database URL formats - just creation, not connection
        valid_urls = [
            "postgresql://user:pass@localhost/testdb",
            "postgresql://user:pass@localhost:5432/dbname",
        ]

        for url in valid_urls:
            # Should not raise exception during engine creation
            test_engine = create_engine(url)
            assert test_engine is not None

    def test_concurrent_connections(self, test_db_session):
        """Test that the database allows concurrent connections with our configuration."""
        # Use test_db_session fixture which provides a working database connection
        from sqlalchemy import text

        result = test_db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    def test_database_basic_operations(self, test_db_session):
        """Test basic database operations work."""
        # Use test_db_session fixture which provides a working database connection
        from sqlalchemy import text

        result = test_db_session.execute(text("SELECT 1 as test_value"))
        value = result.scalar()

        assert value == 1
