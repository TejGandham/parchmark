"""
Database initialization module for ParchMark backend.
Creates database tables and handles initial database setup.
"""

from app.database.database import Base, engine


def create_tables():
    """
    Create all database tables defined in the models.
    This function should be called during application startup.
    """
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def init_database():
    """
    Initialize the database with tables.
    This is the main function to call for database setup.
    """
    try:
        create_tables()
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False


if __name__ == "__main__":
    # Allow running this script directly to initialize the database
    init_database()
