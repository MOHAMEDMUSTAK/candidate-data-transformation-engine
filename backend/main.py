from __future__ import annotations

"""
Eightfold AI - Multi-Source Candidate Data Transformation Engine

FastAPI application entry point.
Configures CORS, mounts routers, and initializes logging.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.utils.logging_config import setup_logging
from backend.routers import pipeline_router, config_router, health_router

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Production-grade multi-source candidate data transformation engine. "
        "Accepts structured and unstructured candidate data, extracts information, "
        "normalizes values, canonicalizes fields, merges records, resolves conflicts "
        "deterministically, tracks provenance, and exports clean JSON."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(health_router.router)
app.include_router(pipeline_router.router)
app.include_router(config_router.router)


@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info(f"{settings.app_name} v{settings.app_version} starting up")
    logger.info(f"CORS origins: {settings.cors_origins}")
    logger.info(f"Default phone region: {settings.default_phone_region}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Application shutting down")
