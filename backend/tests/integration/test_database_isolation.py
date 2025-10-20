"""
Test database isolation between parallel test executions.

This test verifies that the database is properly cleaned between tests
when using pytest-xdist parallel execution. Each test should start with
a clean database state (no leftover data from previous tests).
"""

import pytest
from sqlalchemy.orm import Session

from app.models.models import Note, User


@pytest.mark.integration
@pytest.mark.database
def test_database_starts_clean(test_db_session: Session):
    """Verify database is completely empty at the start of each test."""
    users = test_db_session.query(User).all()
    notes = test_db_session.query(Note).all()

    assert len(users) == 0, "Database should have no users at test start"
    assert len(notes) == 0, "Database should have no notes at test start"


@pytest.mark.integration
@pytest.mark.database
def test_database_isolation_user_creation(test_db_session: Session):
    """
    Verify that data created in one test doesn't leak to other tests.
    This test creates a user but should not affect other tests due to TRUNCATE.
    """
    # Database should be clean at start
    users_before = test_db_session.query(User).count()
    assert users_before == 0, "Database should be empty at test start"

    # Create a user
    from app.auth.auth import get_password_hash

    user = User(username="isolation_test_user", password_hash=get_password_hash("testpass123"))
    test_db_session.add(user)
    test_db_session.commit()

    # Verify user was created
    users_after = test_db_session.query(User).count()
    assert users_after == 1, "User should be created"

    # Note: TRUNCATE in conftest.py will clean this up after test


@pytest.mark.integration
@pytest.mark.database
def test_database_isolation_note_creation(test_db_session: Session, sample_user: User):
    """
    Verify that notes created in one test don't leak to other tests.
    This test creates a note but should not affect other tests.
    """
    # Database should only have the sample_user fixture user
    users_count = test_db_session.query(User).count()
    notes_before = test_db_session.query(Note).count()

    assert users_count == 1, "Should only have sample_user from fixture"
    assert notes_before == 0, "Database should have no notes at test start"

    # Create a note
    note = Note(
        id="isolation-test-note-123",
        user_id=sample_user.id,
        title="Isolation Test Note",
        content="# Isolation Test Note\n\nThis note tests isolation.",
    )
    test_db_session.add(note)
    test_db_session.commit()

    # Verify note was created
    notes_after = test_db_session.query(Note).count()
    assert notes_after == 1, "Note should be created"

    # Note: TRUNCATE in conftest.py will clean this up after test


@pytest.mark.integration
@pytest.mark.database
def test_database_isolation_multiple_operations(test_db_session: Session):
    """
    Verify isolation with multiple database operations.
    Tests that complex operations don't cause race conditions.
    """
    from app.auth.auth import get_password_hash

    # Create multiple users
    for i in range(5):
        user = User(username=f"multi_test_user_{i}", password_hash=get_password_hash(f"pass{i}"))
        test_db_session.add(user)

    test_db_session.commit()

    # Verify all users were created
    users_count = test_db_session.query(User).count()
    assert users_count == 5, "All 5 users should be created"

    # Query users
    all_users = test_db_session.query(User).all()
    assert len(all_users) == 5, "Should retrieve all 5 users"

    # Verify each user has correct username pattern
    usernames = {user.username for user in all_users}
    expected_usernames = {f"multi_test_user_{i}" for i in range(5)}
    assert usernames == expected_usernames, "Usernames should match expected pattern"

    # Note: TRUNCATE in conftest.py will clean this up after test


@pytest.mark.integration
@pytest.mark.database
def test_concurrent_test_safety_check_1(test_db_session: Session):
    """
    Test 1 of concurrent safety check series.
    When run in parallel, this should not interfere with test 2.
    """
    from app.auth.auth import get_password_hash

    # Create user with specific ID pattern
    user = User(username="concurrent_test_1", password_hash=get_password_hash("concurrent1"))
    test_db_session.add(user)
    test_db_session.commit()

    # Verify only this user exists
    users = test_db_session.query(User).all()
    assert len(users) == 1, "Should only have one user"
    assert users[0].username == "concurrent_test_1", "Should be the user we created"


@pytest.mark.integration
@pytest.mark.database
def test_concurrent_test_safety_check_2(test_db_session: Session):
    """
    Test 2 of concurrent safety check series.
    When run in parallel, this should not interfere with test 1.
    """
    from app.auth.auth import get_password_hash

    # Create user with different ID pattern
    user = User(username="concurrent_test_2", password_hash=get_password_hash("concurrent2"))
    test_db_session.add(user)
    test_db_session.commit()

    # Verify only this user exists (not concurrent_test_1)
    users = test_db_session.query(User).all()
    assert len(users) == 1, "Should only have one user"
    assert users[0].username == "concurrent_test_2", "Should be the user we created"
