"""
Database seeding module for ParchMark backend.
Creates default user and seeds with default notes for testing purposes.
"""

from sqlalchemy.orm import Session
from datetime import datetime
from app.database.database import SessionLocal, engine
from app.models.models import User, Note
from app.auth.auth import get_password_hash
import logging

logger = logging.getLogger(__name__)

# Default user credentials (matches frontend demo user)
DEFAULT_USER = {"username": "user", "password": "password"}

# Default notes content (matches frontend DEFAULT_NOTES from constants.ts)
DEFAULT_NOTES_DATA = [
    {
        "id": "1",
        "title": "Welcome to ParchMark",
        "content": "# Welcome to ParchMark\n\nThis is a simple yet powerful note-taking application inspired by ancient papyrus and modern markdown. Here are some features:\n\n- **Markdown support**\n- Dark mode support\n- Clean, minimal UI\n\nFeel free to edit this note or create a new one!",
    },
    {
        "id": "2",
        "title": "Getting Started",
        "content": "# Getting Started\n\n1. Create new notes using the + button\n2. Edit notes in markdown\n3. Toggle between edit and preview mode\n4. Use the sidebar to navigate between notes",
    },
]


def create_default_user(db: Session) -> User:
    """
    Create the default user for testing purposes.

    Args:
        db: Database session

    Returns:
        User: The created user object
    """
    # Check if default user already exists
    existing_user = (
        db.query(User).filter(User.username == DEFAULT_USER["username"]).first()
    )
    if existing_user:
        logger.info(f"Default user '{DEFAULT_USER['username']}' already exists")
        return existing_user

    # Create new default user
    hashed_password = get_password_hash(DEFAULT_USER["password"])
    default_user = User(
        username=DEFAULT_USER["username"], password_hash=hashed_password
    )

    db.add(default_user)
    db.commit()
    db.refresh(default_user)

    logger.info(f"Created default user: {DEFAULT_USER['username']}")
    return default_user


def create_default_notes(db: Session, user: User) -> list[Note]:
    """
    Create default notes for the user.

    Args:
        db: Database session
        user: User object to associate notes with

    Returns:
        list[Note]: List of created note objects
    """
    created_notes = []

    for note_data in DEFAULT_NOTES_DATA:
        # Check if note already exists
        existing_note = (
            db.query(Note)
            .filter(Note.id == note_data["id"], Note.user_id == user.id)
            .first()
        )

        if existing_note:
            logger.info(f"Default note '{note_data['title']}' already exists")
            created_notes.append(existing_note)
            continue

        # Create new default note
        default_note = Note(
            id=note_data["id"],
            user_id=user.id,
            title=note_data["title"],
            content=note_data["content"],
        )

        db.add(default_note)
        created_notes.append(default_note)
        logger.info(f"Created default note: {note_data['title']}")

    db.commit()

    # Refresh all created notes
    for note in created_notes:
        db.refresh(note)

    return created_notes


def seed_database() -> bool:
    """
    Main function to seed the database with default data.

    Returns:
        bool: True if seeding was successful, False otherwise
    """
    try:
        logger.info("Starting database seeding...")

        # Create database session
        db = SessionLocal()

        try:
            # Create default user
            default_user = create_default_user(db)

            # Create default notes for the user
            default_notes = create_default_notes(db, default_user)

            logger.info(f"Database seeding completed successfully!")
            logger.info(f"Created user: {default_user.username}")
            logger.info(f"Created {len(default_notes)} notes")

            return True

        except Exception as e:
            logger.error(f"Error during database seeding: {e}")
            db.rollback()
            return False

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to create database session for seeding: {e}")
        return False


def reset_and_seed_database() -> bool:
    """
    Reset the database and seed with fresh default data.
    WARNING: This will delete all existing data!

    Returns:
        bool: True if reset and seeding was successful, False otherwise
    """
    try:
        logger.warning("Resetting database - ALL DATA WILL BE LOST!")

        # Drop all tables and recreate them
        from app.database.database import Base

        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        logger.info("Database tables reset successfully")

        # Seed with default data
        return seed_database()

    except Exception as e:
        logger.error(f"Failed to reset and seed database: {e}")
        return False


def check_seeding_status() -> dict:
    """
    Check the current seeding status of the database.

    Returns:
        dict: Status information about seeded data
    """
    try:
        db = SessionLocal()

        try:
            # Check for default user
            default_user = (
                db.query(User).filter(User.username == DEFAULT_USER["username"]).first()
            )
            user_exists = default_user is not None

            # Check for default notes
            notes_count = 0
            if default_user:
                notes_count = (
                    db.query(Note).filter(Note.user_id == default_user.id).count()
                )

            return {
                "default_user_exists": user_exists,
                "default_user_id": default_user.id if default_user else None,
                "default_notes_count": notes_count,
                "expected_notes_count": len(DEFAULT_NOTES_DATA),
                "seeding_complete": user_exists
                and notes_count == len(DEFAULT_NOTES_DATA),
            }

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to check seeding status: {e}")
        return {"error": str(e), "seeding_complete": False}


if __name__ == "__main__":
    # Allow running this script directly to seed the database
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        success = reset_and_seed_database()
    else:
        success = seed_database()

    if success:
        print("Database seeding completed successfully!")
        status = check_seeding_status()
        print(f"Seeding status: {status}")
    else:
        print("Database seeding failed!")
        sys.exit(1)
