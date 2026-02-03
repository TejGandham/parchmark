"""
Health check service for monitoring application and database status.

This service is a singleton - it uses contextvars to access the request-scoped
database session without requiring it to be passed as a parameter.
"""

import logging

from sqlalchemy import text

from app.database.context import get_db

logger = logging.getLogger(__name__)


class HealthService:
    """Service for performing health checks on application components."""

    async def check_database_connection(self) -> bool:
        """
        Check if database connection is working.

        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            db = get_db()
            await db.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            return False

    async def get_health_status(self) -> dict:
        """
        Get comprehensive health status of the application.

        Returns:
            dict: Health status including database connectivity

        Raises:
            Exception: If database connection fails
        """
        is_db_healthy = await self.check_database_connection()

        if not is_db_healthy:
            raise Exception("Database connection failed")

        return {"status": "healthy", "database": "connected", "service": "ParchMark API", "version": "1.0.0"}


# Singleton instance
health_service = HealthService()
