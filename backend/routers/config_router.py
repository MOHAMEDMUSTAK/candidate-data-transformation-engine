from __future__ import annotations

"""
Eightfold AI - Config Router

API endpoints for managing runtime configuration.
"""

import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.models.config_schema import DEFAULT_CONFIG, EXAMPLE_CUSTOM_CONFIG

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/config", tags=["configuration"])


@router.get("/default")
async def get_default_config():
    """Return the default output configuration."""
    return JSONResponse(content=DEFAULT_CONFIG.model_dump())


@router.get("/example")
async def get_example_config():
    """Return an example custom configuration matching the assignment spec."""
    return JSONResponse(content=EXAMPLE_CUSTOM_CONFIG.model_dump(by_alias=True))


@router.get("/schema")
async def get_config_schema():
    """Return the configuration JSON schema for UI validation."""
    return JSONResponse(content={
        "description": "Runtime output configuration for the transformation pipeline",
        "properties": {
            "fields": {
                "type": "array",
                "description": "Custom field projections",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Output field name"},
                        "from": {"type": "string", "description": "Source canonical path"},
                        "type": {"type": "string", "enum": ["string", "number", "boolean", "string[]"]},
                        "required": {"type": "boolean"},
                        "normalize": {"type": "string", "enum": ["E164", "canonical", "lowercase"]},
                    },
                    "required": ["path"],
                },
            },
            "include_confidence": {"type": "boolean", "default": True},
            "include_provenance": {"type": "boolean", "default": True},
            "on_missing": {"type": "string", "enum": ["null", "omit", "error"], "default": "null"},
        },
    })
