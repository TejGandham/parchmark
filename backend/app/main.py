"""
ParchMark Backend API

A modern FastAPI-based backend for the ParchMark markdown note-taking application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, notes

# Create FastAPI application
app = FastAPI(
    title="ParchMark API",
    description="Backend API for ParchMark - A modern markdown note-taking application",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(notes.router, prefix="/api/notes", tags=["notes"])


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "message": "ParchMark API is running",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "parchmark-api"}
