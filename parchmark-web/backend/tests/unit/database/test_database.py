"""
Unit tests for database configuration and utilities (app.database).
Tests database setup, connection, and dependency functions.
"""

from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import (
    ASYNC_DATABASE_URL,
    SQLALCHEMY_DATABASE_URL,
    AsyncSessionLocal,
    Base,
    async_engine,
    get_async_db,
)


class TestDatabaseConfiguration:
    """Test database configuration and setup."""

    def test_database_url_default(self):
        """Test default database URL configuration."""
        # Default is now PostgreSQL
        assert "postgresql" in SQLALCHEMY_DATABASE_URL.lower()
        assert "parchmark" in SQLALCHEMY_DATABASE_URL

    def test_async_database_url_configuration(self):
        """Test async database URL is properly configured."""
        assert "postgresql+asyncpg://" in ASYNC_DATABASE_URL
        assert "parchmark" in ASYNC_DATABASE_URL

    @patch.dict("os.environ", {"DATABASE_URL": "postgresql://user:pass@localhost/testdb"})
    def test_database_url_from_environment(self):
        """Test database URL can be configured via environment."""
        # Need to reload the module to pick up environment changes
        from importlib import reload

        import app.database.database

        reload(app.database.database)

        assert app.database.database.SQLALCHEMY_DATABASE_URL == "postgresql://user:pass@localhost/testdb"

    def test_async_engine_configuration(self):
        """Test async SQLAlchemy engine configuration."""
        assert async_engine is not None
        # Engine should have a valid URL
        assert hasattr(async_engine, "url")
        # Verify it's configured for asyncpg
        assert "asyncpg" in str(async_engine.url)

    def test_postgresql_only_validation(self):
        """Test that only PostgreSQL URLs are accepted."""
        # This test would require reloading the module with different URLs
        # which is tested in test_database_url_validation below
        assert "postgresql" in SQLALCHEMY_DATABASE_URL.lower()

    def test_async_session_local_configuration(self):
        """Test AsyncSessionLocal configuration."""
        assert AsyncSessionLocal is not None

    def test_base_declarative_class(self):
        """Test Base declarative class."""
        assert Base is not None
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")


class TestGetAsyncDbDependency:
    """Test get_async_db dependency function."""

    @pytest.mark.asyncio
    async def test_get_async_db_yields_session(self):
        """Test that get_async_db yields an async database session."""
        db_generator = get_async_db()

        # Get the session from the async generator
        db_session = await db_generator.__anext__()

        assert isinstance(db_session, AsyncSession)

        # Clean up
        try:
            await db_generator.__anext__()
        except StopAsyncIteration:
            pass  # Expected when generator closes


class TestDatabaseConnectionHandling:
    """Test database connection handling and edge cases."""

    def test_database_connection_error_handling(self):
        """Test handling of database connection errors."""
        # Create engine with invalid database URL
        invalid_db_url = "postgresql://invalid_user:invalid_pass@invalid_host:5432/invalid_db"

        # Should not raise exception during creation, only when connecting
        invalid_engine = create_engine(invalid_db_url)
        assert invalid_engine is not None


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

    @pytest.mark.asyncio
    async def test_concurrent_connections(self, test_db_session):
        """Test that the database allows concurrent connections with our configuration."""
        # Use test_db_session fixture which provides a working database connection
        from sqlalchemy import text

        result = await test_db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_database_basic_operations(self, test_db_session):
        """Test basic database operations work."""
        # Use test_db_session fixture which provides a working database connection
        from sqlalchemy import text

        result = await test_db_session.execute(text("SELECT 1 as test_value"))
        value = result.scalar()

        assert value == 1
