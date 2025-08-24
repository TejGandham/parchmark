"""
SQLAlchemy database configuration for ParchMark backend.
Configures PostgreSQL database engine and session management.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
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

# Create SQLAlchemy engine for PostgreSQL
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for declarative models
Base = declarative_base()


# Dependency to get database session
def get_db():
    """
    Dependency function to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
