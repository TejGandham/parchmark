#!/usr/bin/env python
"""
Script to create the test user mentioned in the README.
"""

import sys

sys.path.append("..")

from app.auth.auth import get_password_hash
from app.database.database import SessionLocal
from app.models.models import User


def create_test_user():
    """Create testuser with testpass123 password."""
    db = SessionLocal()

    try:
        # Check if testuser already exists
        existing_user = db.query(User).filter(User.username == "testuser").first()
        if existing_user:
            print("User 'testuser' already exists!")
            return True

        # Create testuser
        hashed_password = get_password_hash("testpass123")
        test_user = User(username="testuser", password_hash=hashed_password)

        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        print(f"Created user 'testuser' with ID: {test_user.id}")
        print("You can now login with:")
        print("  Username: testuser")
        print("  Password: testpass123")
        return True

    except Exception as e:
        print(f"Error creating test user: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = create_test_user()
    sys.exit(0 if success else 1)
