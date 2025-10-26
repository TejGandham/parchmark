"""
Health check service for monitoring application and database status.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session


class HealthService:
    """Service for performing health checks on application components."""

    @staticmethod
    def check_database_connection(db: Session) -> bool:
        """
        Check if database connection is working.

        Args:
            db: Database session

        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            db.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    @staticmethod
    def get_health_status(db: Session) -> dict:
        """
        Get comprehensive health status of the application.

        Args:
            db: Database session

        Returns:
            dict: Health status including database connectivity

        Raises:
            Exception: If database connection fails
        """
        is_db_healthy = HealthService.check_database_connection(db)

        if not is_db_healthy:
            raise Exception("Database connection failed")

        return {"status": "healthy", "database": "connected", "service": "ParchMark API", "version": "1.0.0"}


# Singleton instance
health_service = HealthService()
