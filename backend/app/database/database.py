"""
SQLAlchemy database configuration for ParchMark backend.
Configures PostgreSQL database engine and session management with async support.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from .env file
load_dotenv()

# Database URL - PostgreSQL required
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/parchmark")

# Validate that we're using PostgreSQL
if not SQLALCHEMY_DATABASE_URL.startswith(("postgresql://", "postgresql+psycopg2://")):
    raise ValueError(
        f"PostgreSQL database URL required. Got: {SQLALCHEMY_DATABASE_URL.split('://')[0]}://"
        "\nPlease set DATABASE_URL to a valid PostgreSQL connection string."
    )

# Convert sync URL to async URL for asyncpg
ASYNC_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://").replace(
    "postgresql+psycopg2://", "postgresql+asyncpg://"
)

# Create async SQLAlchemy engine for PostgreSQL with connection pool settings
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,  # Verify connections before use to avoid stale connection errors
    pool_recycle=3600,  # Recycle connections after 1 hour to prevent stale connections
)

# Create AsyncSessionLocal class for async database sessions
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Create sync SQLAlchemy engine (kept for backwards compatibility during migration)
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create SessionLocal class for sync database sessions (kept for backwards compatibility)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for declarative models
Base = declarative_base()


# Async dependency to get database session
async def get_async_db():
    """
    Async dependency function to get database session.
    Yields an async database session and ensures it's closed after use.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Sync dependency (kept for backwards compatibility during migration)
def get_db():
    """
    Dependency function to get database session.
    Yields a database session and ensures it's closed after use.

    DEPRECATED: Use get_async_db for new code.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
