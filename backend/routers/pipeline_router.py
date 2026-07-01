from __future__ import annotations

"""
Eightfold AI - Pipeline Router

API endpoints for running the transformation pipeline,
retrieving results, and managing configurations.
"""

import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.models.config_schema import DEFAULT_CONFIG, EXAMPLE_CUSTOM_CONFIG

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

# Store last pipeline result in memory (production would use a database)
_last_result: dict[str, Any] | None = None


@router.post("/run")
async def run_pipeline(
    files: list[UploadFile] = File(...),
    config: Optional[str] = Form(None),
):
    """
    Run the full 12-stage candidate data transformation pipeline.

    Accepts multiple files (CSV, JSON, PDF, DOCX, TXT) and an optional
    runtime output configuration as JSON string.
    """
    global _last_result

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    # Read all file contents
    file_contents: dict[str, bytes] = {}
    for upload_file in files:
        try:
            content = await upload_file.read()
            file_contents[upload_file.filename or "unknown"] = content
        except Exception as e:
            logger.error(f"Failed to read file '{upload_file.filename}': {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to read file '{upload_file.filename}': {str(e)}"
            )

    # Parse output config
    output_config = None
    if config:
        try:
            output_config = json.loads(config)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid configuration JSON: {str(e)}"
            )

    # Run pipeline
    orchestrator = PipelineOrchestrator()
    result = orchestrator.execute(file_contents, output_config)

    # Store result
    result_dict = result.model_dump()
    _last_result = result_dict

    return JSONResponse(content=result_dict)


@router.get("/last-result")
async def get_last_result():
    """Retrieve the last pipeline execution result."""
    if _last_result is None:
        raise HTTPException(status_code=404, detail="No pipeline results available")
    return JSONResponse(content=_last_result)


@router.get("/status")
async def get_pipeline_status():
    """Get the current pipeline status."""
    return {
        "has_result": _last_result is not None,
        "stages": 12,
        "stage_names": [
            "Input Detection", "Extraction", "Parsing", "Normalization",
            "Canonicalization", "Merge", "Conflict Resolution",
            "Confidence Calculation", "Projection", "Validation",
            "Quality Scoring", "Export",
        ],
    }
