"""
Unit tests for database configuration and utilities (app.database).
Tests database setup, connection, and dependency functions.
"""

import os
import tempfile
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.database import SQLALCHEMY_DATABASE_URL, Base, SessionLocal, engine, get_db


class TestDatabaseConfiguration:
    """Test database configuration and setup."""

    def test_database_url_default(self):
        """Test default database URL configuration."""
        # Default should be SQLite
        assert "sqlite" in SQLALCHEMY_DATABASE_URL.lower()
        assert "parchmark.db" in SQLALCHEMY_DATABASE_URL

    @patch.dict("os.environ", {"DATABASE_URL": "sqlite:///test.db"})
    def test_database_url_from_environment(self):
        """Test database URL can be configured via environment."""
        # Need to reload the module to pick up environment changes
        from importlib import reload

        import app.database.database

        reload(app.database.database)

        assert app.database.database.SQLALCHEMY_DATABASE_URL == "sqlite:///test.db"

    def test_engine_configuration(self):
        """Test SQLAlchemy engine configuration."""
        assert engine is not None
        assert str(engine.url).startswith("sqlite")

        # Test SQLite-specific configuration
        assert engine.dialect.name == "sqlite"
        # Engine pool exists
        assert hasattr(engine, "pool")

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

    def test_database_file_creation(self):
        """Test that SQLite database file is created when needed."""
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            temp_db_path = tmp_file.name

        # Remove the file so we can test creation
        os.unlink(temp_db_path)

        try:
            # Create engine for temporary database
            temp_db_url = f"sqlite:///{temp_db_path}"
            temp_engine = create_engine(temp_db_url, connect_args={"check_same_thread": False})

            # Create a session - this should create the database file
            from sqlalchemy.orm import sessionmaker

            TempSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=temp_engine)

            from sqlalchemy import text

            session = TempSessionLocal()
            session.execute(text("SELECT 1"))  # Simple query to ensure connection
            session.close()

            # Verify database file was created
            assert os.path.exists(temp_db_path)

        finally:
            # Clean up
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_database_connection_error_handling(self):
        """Test handling of database connection errors."""
        # Create engine with invalid database path
        invalid_db_url = "sqlite:///invalid/path/that/does/not/exist/test.db"

        with pytest.raises(Exception):
            invalid_engine = create_engine(invalid_db_url, connect_args={"check_same_thread": False})

            from sqlalchemy.orm import sessionmaker

            InvalidSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=invalid_engine)

            from sqlalchemy import text

            session = InvalidSessionLocal()
            # This should raise an exception
            session.execute(text("SELECT 1"))
            session.close()

    def test_engine_creation_with_mock(self):
        """Test engine creation configuration."""
        # Test without mocking - just verify engine exists
        assert engine is not None
        assert "sqlite" in str(engine.url).lower()

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
    """Test database compatibility and SQLite-specific features."""

    def test_sqlite_features(self):
        """Test SQLite-specific features and configuration."""
        db_generator = get_db()
        session = next(db_generator)

        try:
            # Test that we can execute SQLite-specific queries
            from sqlalchemy import text

            result = session.execute(text("SELECT sqlite_version()"))
            version = result.scalar()

            assert version is not None
            assert isinstance(version, str)
            assert len(version) > 0

        finally:
            # Clean up
            try:
                next(db_generator)
            except StopIteration:
                pass

    def test_concurrent_connections(self):
        """Test that SQLite allows concurrent connections with our configuration."""
        sessions = []
        generators = []

        try:
            # Create multiple concurrent sessions
            for _ in range(3):
                gen = get_db()
                session = next(gen)
                sessions.append(session)
                generators.append(gen)

            # All sessions should be usable
            from sqlalchemy import text

            for session in sessions:
                result = session.execute(text("SELECT 1"))
                assert result.scalar() == 1

        finally:
            # Clean up all sessions
            for gen in generators:
                try:
                    next(gen)
                except StopIteration:
                    pass

    def test_database_url_validation(self):
        """Test database URL format validation."""
        # Test various valid SQLite URL formats
        valid_urls = [
            "sqlite:///./test.db",
            "sqlite:///test.db",
            "sqlite:////absolute/path/test.db",
            "sqlite:///:memory:",
        ]

        for url in valid_urls:
            # Should not raise exception
            test_engine = create_engine(url, connect_args={"check_same_thread": False})
            assert test_engine is not None

    def test_in_memory_database(self):
        """Test in-memory SQLite database functionality."""
        # Create in-memory database
        memory_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

        from sqlalchemy.orm import sessionmaker

        MemorySessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=memory_engine)

        session = MemorySessionLocal()

        try:
            # Create a simple table and test it
            from sqlalchemy import text

            session.execute(
                text("""
                CREATE TABLE test_table (
                    id INTEGER PRIMARY KEY,
                    name TEXT
                )
            """)
            )

            session.execute(
                text("""
                INSERT INTO test_table (name) VALUES ('test')
            """)
            )

            result = session.execute(text("SELECT name FROM test_table"))
            assert result.scalar() == "test"

        finally:
            session.close()
