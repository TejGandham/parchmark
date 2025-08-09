"""
FastAPI main application entry point for ParchMark backend.
This file will be configured in a later task.
"""

from fastapi import FastAPI

app = FastAPI(
    title="ParchMark API",
    description="Backend API for ParchMark note-taking application",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "ParchMark API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
