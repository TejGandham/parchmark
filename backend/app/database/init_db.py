"""
Database initialization module for ParchMark backend.
Creates database tables and handles initial database setup.
"""

from app.database.database import Base, async_engine
from app.database.seed import check_seeding_status, seed_database


async def create_tables():
    """
    Create all database tables defined in the models.
    This function is idempotent and will not recreate existing tables.
    """
    print("Creating database tables...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")


async def init_database():
    """
    Initialize the database with tables and default data if needed.
    This is the main function to call for database setup.
    """
    try:
        await create_tables()

        # Check if the database is already seeded
        seeding_status = await check_seeding_status()
        if not seeding_status.get("seeding_complete"):
            print("Database is not seeded. Seeding with default data...")
            await seed_database()
        else:
            print("Database is already seeded. Skipping seeding.")

        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False


if __name__ == "__main__":
    # Allow running this script directly to initialize the database
    import asyncio

    asyncio.run(init_database())
