"""
Health check service for monitoring application and database status.
"""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class HealthService:
    """Service for performing health checks on application components."""

    @staticmethod
    async def check_database_connection(db: AsyncSession) -> bool:
        """
        Check if database connection is working.

        Args:
            db: Async database session

        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            await db.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            return False

    @staticmethod
    async def get_health_status(db: AsyncSession) -> dict:
        """
        Get comprehensive health status of the application.

        Args:
            db: Async database session

        Returns:
            dict: Health status including database connectivity

        Raises:
            Exception: If database connection fails
        """
        is_db_healthy = await HealthService.check_database_connection(db)

        if not is_db_healthy:
            raise Exception("Database connection failed")

        from app.version import get_version_info

        return {"status": "healthy", "database": "connected", "service": "ParchMark API", **get_version_info()}


# Singleton instance
health_service = HealthService()
