from __future__ import annotations

"""
Eightfold AI - Health Router

Basic health check endpoint for monitoring.
"""

from fastapi import APIRouter
from backend.config import settings

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }
