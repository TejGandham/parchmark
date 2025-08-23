"""
Database seeding module for ParchMark backend.
Creates default user and seeds with default notes for testing purposes.
"""

import logging

from sqlalchemy.orm import Session

from app.auth.auth import get_password_hash
from app.database.database import SessionLocal, engine
from app.models.models import Note, User

logger = logging.getLogger(__name__)

# Default user credentials (matches frontend demo user)
DEFAULT_USERS = [
    {"username": "demouser", "password": "demopass"},
    {"username": "testuser", "password": "testpass123"}
]

# Default notes content (matches frontend DEFAULT_NOTES from constants.ts)
DEFAULT_NOTES_DATA = [
    {
        "id": "1",
        "title": "Welcome to ParchMark",
        "content": (
            "# Welcome to ParchMark\n\n"
            "This is a simple yet powerful note-taking application inspired by "
            "ancient papyrus and modern markdown. Here are some features:\n\n"
            "- **Markdown support**\n- Dark mode support\n- Clean, minimal UI\n\n"
            "Feel free to edit this note or create a new one!"
        ),
    },
    {
        "id": "2",
        "title": "Getting Started",
        "content": (
            "# Getting Started\n\n"
            "1. Create new notes using the + button\n"
            "2. Edit notes in markdown\n"
            "3. Toggle between edit and preview mode\n"
            "4. Use the sidebar to navigate between notes\n\n"
            "## Markdown Features\n\n"
            "ParchMark supports:\n"
            "- **Bold** and *italic* text\n"
            "- Lists (ordered and unordered)\n"
            "- Code blocks with syntax highlighting\n"
            "- Tables\n"
            "- Mermaid diagrams (see Architecture note)"
        ),
    },
    {
        "id": "3",
        "title": "Architecture Overview",
        "content": (
            "# Architecture Overview\n\n"
            "ParchMark uses a modern full-stack architecture with React frontend and FastAPI backend.\n\n"
            "## System Architecture Diagram\n\n"
            "```mermaid\n"
            "graph TB\n"
            "    subgraph Client[\"Client Browser\"]\n"
            "        UI[React UI<br/>TypeScript + Vite]\n"
            "        Store[Zustand Store<br/>State Management]\n"
            "    end\n"
            "    \n"
            "    subgraph Frontend[\"Frontend Layer\"]\n"
            "        Nginx[Nginx<br/>Static Server]\n"
            "        Router[React Router v7<br/>Navigation]\n"
            "    end\n"
            "    \n"
            "    subgraph Backend[\"Backend API\"]\n"
            "        FastAPI[FastAPI<br/>REST API]\n"
            "        Auth[JWT Auth<br/>Bcrypt]\n"
            "        ORM[SQLAlchemy<br/>ORM]\n"
            "    end\n"
            "    \n"
            "    subgraph Data[\"Data Layer\"]\n"
            "        DB[(SQLite<br/>Database)]\n"
            "    end\n"
            "    \n"
            "    UI --> Store\n"
            "    Store --> Router\n"
            "    Router --> Nginx\n"
            "    Nginx --> FastAPI\n"
            "    FastAPI --> Auth\n"
            "    Auth --> ORM\n"
            "    ORM --> DB\n"
            "    \n"
            "    style Client fill:#e1f5fe\n"
            "    style Frontend fill:#fff3e0\n"
            "    style Backend fill:#f3e5f5\n"
            "    style Data fill:#e8f5e9\n"
            "```\n\n"
            "## Tech Stack\n\n"
            "### Frontend\n"
            "- **React 18** - UI framework\n"
            "- **TypeScript** - Type safety\n"
            "- **Vite** - Build tool\n"
            "- **Chakra UI** - Component library\n"
            "- **Zustand** - State management\n\n"
            "### Backend\n"
            "- **FastAPI** - Web framework\n"
            "- **Python 3.13** - Runtime\n"
            "- **SQLAlchemy** - ORM\n"
            "- **JWT** - Authentication\n"
            "- **SQLite** - Database\n\n"
            "### DevOps\n"
            "- **Docker** - Containerization\n"
            "- **Nginx** - Reverse proxy\n"
            "- **uv** - Python package manager"
        ),
    },
]


def create_default_users(db: Session) -> list[User]:
    """
    Create the default users for testing purposes.

    Args:
        db: Database session

    Returns:
        list[User]: List of created user objects
    """
    created_users = []
    
    for user_data in DEFAULT_USERS:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == user_data["username"]).first()
        if existing_user:
            logger.info(f"Default user '{user_data['username']}' already exists")
            created_users.append(existing_user)
            continue

        # Create new default user
        hashed_password = get_password_hash(user_data["password"])
        default_user = User(username=user_data["username"], password_hash=hashed_password)

        db.add(default_user)
        created_users.append(default_user)
        logger.info(f"Creating default user: {user_data['username']}")
    
    db.commit()
    
    # Refresh all users
    for user in created_users:
        db.refresh(user)
        logger.info(f"Created default user: {user.username}")
    
    return created_users


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
        existing_note = db.query(Note).filter(Note.id == note_data["id"], Note.user_id == user.id).first()

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
            # Create default users
            default_users = create_default_users(db)

            # Create default notes for the first user (demouser)
            if default_users:
                default_notes = create_default_notes(db, default_users[0])
                logger.info(f"Created {len(default_notes)} notes for {default_users[0].username}")

            logger.info("Database seeding completed successfully!")
            logger.info(f"Created {len(default_users)} users")

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
            # Check for default users
            users_exist = True
            for user_data in DEFAULT_USERS:
                user = db.query(User).filter(User.username == user_data["username"]).first()
                if not user:
                    users_exist = False
                    break
            
            # Check for default notes on first user (demouser)
            first_user = db.query(User).filter(User.username == DEFAULT_USERS[0]["username"]).first()
            notes_count = 0
            if first_user:
                notes_count = db.query(Note).filter(Note.user_id == first_user.id).count()

            return {
                "default_users_exist": users_exist,
                "default_users_count": len(DEFAULT_USERS),
                "default_notes_count": notes_count,
                "expected_notes_count": len(DEFAULT_NOTES_DATA),
                "seeding_complete": users_exist and notes_count == len(DEFAULT_NOTES_DATA),
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
