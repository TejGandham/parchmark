"""
Database initialization module for ParchMark backend.
Creates database tables and handles initial database setup.
"""

from app.database.database import Base, engine
from app.database.seed import check_seeding_status, seed_database


def create_tables():
    """
    Create all database tables defined in the models.
    This function is idempotent and will not recreate existing tables.
    """
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def init_database():
    """
    Initialize the database with tables and default data if needed.
    This is the main function to call for database setup.
    """
    try:
        create_tables()

        # Check if the database is already seeded
        seeding_status = check_seeding_status()
        if not seeding_status.get("seeding_complete"):
            print("Database is not seeded. Seeding with default data...")
            seed_database()
        else:
            print("Database is already seeded. Skipping seeding.")

        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False


if __name__ == "__main__":
    # Allow running this script directly to initialize the database
    init_database()
