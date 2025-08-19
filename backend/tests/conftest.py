"""
Test configuration and fixtures for ParchMark backend tests.
Provides common test fixtures, database setup, and authentication utilities.
"""

import pytest
import os
import tempfile
from typing import Generator, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

# Import application components
from app.database.database import Base, get_db
from app.models.models import User, Note
from app.auth.auth import get_password_hash, create_access_token
from main import app
from tests.factories import (
    UserFactory, 
    UserDataFactory, 
    NoteFactory, 
    NoteDataFactory,
    AuthTokenFactory,
    MarkdownContentFactory
)


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a temporary SQLite database for testing."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    database_url = f"sqlite:///{db_path}"
    
    # Create engine for test database
    engine = create_engine(
        database_url, 
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a database session for testing with automatic rollback."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=test_db_engine
    )
    
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(test_db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up dependency override
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return UserDataFactory()


@pytest.fixture
def sample_user(test_db_session: Session, sample_user_data: Dict[str, str]) -> User:
    """Create a sample user in the test database."""
    hashed_password = get_password_hash(sample_user_data["password"])
    user = User(
        username=sample_user_data["username"],
        password_hash=hashed_password
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def sample_admin_user(test_db_session: Session) -> User:
    """Create a sample admin user in the test database."""
    hashed_password = get_password_hash("adminpass123")
    user = User(
        username="adminuser",
        password_hash=hashed_password
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(sample_user: User) -> str:
    """Generate a valid JWT token for testing authenticated endpoints."""
    token_data = {"sub": sample_user.username}
    token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=30)
    )
    return token


@pytest.fixture
def auth_headers(auth_token: str) -> Dict[str, str]:
    """Generate authentication headers for API requests."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def sample_note_data():
    """Sample note data for testing."""
    return NoteDataFactory()


@pytest.fixture
def sample_note(test_db_session: Session, sample_user: User, sample_note_data: Dict[str, str]) -> Note:
    """Create a sample note in the test database."""
    note = Note(
        id="test-note-1",
        user_id=sample_user.id,
        title=sample_note_data["title"],
        content=sample_note_data["content"]
    )
    test_db_session.add(note)
    test_db_session.commit()
    test_db_session.refresh(note)
    return note


@pytest.fixture
def multiple_notes(test_db_session: Session, sample_user: User) -> list[Note]:
    """Create multiple sample notes for testing."""
    notes_data = [
        {
            "id": "note-1",
            "title": "First Note",
            "content": "# First Note\n\nThis is the first test note."
        },
        {
            "id": "note-2", 
            "title": "Second Note",
            "content": "# Second Note\n\nThis is the second test note."
        },
        {
            "id": "note-3",
            "title": "Third Note", 
            "content": "# Third Note\n\nThis is the third test note."
        }
    ]
    
    notes = []
    for note_data in notes_data:
        note = Note(
            id=note_data["id"],
            user_id=sample_user.id,
            title=note_data["title"],
            content=note_data["content"]
        )
        test_db_session.add(note)
        notes.append(note)
    
    test_db_session.commit()
    
    for note in notes:
        test_db_session.refresh(note)
    
    return notes


@pytest.fixture
def invalid_token():
    """Generate an invalid JWT token for testing error cases."""
    return "invalid.jwt.token"


@pytest.fixture
def expired_token(sample_user: User):
    """Generate an expired JWT token for testing."""
    token_data = {"sub": sample_user.username}
    # Create token that expired 1 hour ago
    expired_delta = timedelta(hours=-1)
    token = create_access_token(
        data=token_data,
        expires_delta=expired_delta
    )
    return token


@pytest.fixture
def markdown_content_samples():
    """Various markdown content samples for testing."""
    return MarkdownContentFactory()


@pytest.fixture
def user_factory():
    """Provide access to UserFactory for dynamic test data generation."""
    return UserFactory


@pytest.fixture
def note_factory():
    """Provide access to NoteFactory for dynamic test data generation."""
    return NoteFactory


@pytest.fixture
def edge_case_data():
    """Provide edge case test data scenarios."""
    from tests.factories import EdgeCaseDataFactory
    return EdgeCaseDataFactory


@pytest.fixture
def security_test_data():
    """Provide security-related test data."""
    from tests.factories import SecurityTestDataFactory
    return SecurityTestDataFactory


@pytest.fixture
def api_response_factory():
    """Provide API response factory for testing responses."""
    from tests.factories import APIResponseFactory
    return APIResponseFactory


# Test utilities
class TestDataFactory:
    """Factory class for creating test data."""
    
    @staticmethod
    def create_user_data(username: str = None, password: str = None) -> Dict[str, str]:
        """Create user data with optional custom values."""
        return {
            "username": username or f"user_{datetime.now().timestamp()}",
            "password": password or "testpass123"
        }
    
    @staticmethod
    def create_note_data(title: str = None, content: str = None) -> Dict[str, str]:
        """Create note data with optional custom values."""
        title = title or f"Test Note {datetime.now().timestamp()}"
        content = content or f"# {title}\n\nTest content for the note."
        return {
            "title": title,
            "content": content
        }
    
    @staticmethod
    def create_note_update_data(title: str = None, content: str = None) -> Dict[str, str]:
        """Create note update data with optional values."""
        data = {}
        if title is not None:
            data["title"] = title
        if content is not None:
            data["content"] = content
        return data


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Set environment variables for testing
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["ALGORITHM"] = "HS256"
    os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
    

def pytest_unconfigure(config):
    """Clean up after pytest runs."""
    # Clean up environment variables
    test_env_vars = [
        "SECRET_KEY",
        "ALGORITHM", 
        "ACCESS_TOKEN_EXPIRE_MINUTES"
    ]
    for var in test_env_vars:
        if var in os.environ:
            del os.environ[var]