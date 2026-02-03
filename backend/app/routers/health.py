"""
Health check endpoint for container orchestration and load balancers.
Provides comprehensive health status including database connectivity.
"""

from fastapi import APIRouter, HTTPException

from app.services.health_service import health_service

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint.

    Returns:
        dict: Health status including database connectivity

    Raises:
        HTTPException: 503 if service is unhealthy
    """
    try:
        return await health_service.get_health_status()
    except Exception as e:
        raise HTTPException(status_code=503, detail="Service unhealthy: Database connection failed") from e
