"""
FastAPI main application entry point for ParchMark backend.
Configures CORS, routers, database initialization, and exception handlers.
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database.database import async_engine
from app.database.init_db import init_database
from app.routers import auth, health, notes, settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting ParchMark API...")

    # Initialize database
    try:
        success = init_database()
        if success:
            logger.info("Database initialized successfully")
        else:
            logger.error("Failed to initialize database")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

    logger.info("ParchMark API startup complete")

    yield

    # Shutdown
    logger.info("Shutting down ParchMark API...")

    # Dispose async engine to close all connections cleanly
    await async_engine.dispose()
    logger.info("Database connections closed")


# Create FastAPI application with enhanced configuration
app = FastAPI(
    title="ParchMark API",
    description="""
    Backend API for ParchMark note-taking application.

    ## Features

    * **Authentication**: JWT-based user authentication
    * **Notes Management**: Full CRUD operations for markdown notes
    * **User Authorization**: Secure access to user-specific data
    * **Markdown Processing**: Automatic title extraction from H1 headings

    ## Authentication

    Most endpoints require authentication via JWT Bearer token.
    Use the `/auth/login` endpoint to obtain a token.
    """,
    version="1.0.0",
    contact={
        "name": "ParchMark API Support",
        "email": "support@parchmark.com",
    },
    license_info={
        "name": "MIT",
    },
    lifespan=lifespan,
)

# Configure CORS middleware for frontend integration
# Get allowed origins from environment variable or use defaults for development
allowed_origins_str = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:8080",
)
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

logger.info(f"CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom HTTP exception handler.
    Returns consistent error response format.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path),
        },
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    General exception handler for unhandled exceptions.
    Returns 500 Internal Server Error with minimal information.
    """
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "status_code": 500,
            "path": str(request.url.path),
        },
    )


# Register routers with /api prefix
app.include_router(auth.router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(health.router)


# Root endpoints
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint providing API information.
    """
    return {
        "message": "ParchMark API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    """
    return {"status": "healthy", "service": "ParchMark API", "version": "1.0.0"}
