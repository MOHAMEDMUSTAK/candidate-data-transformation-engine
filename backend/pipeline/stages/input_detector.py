from __future__ import annotations

"""
Eightfold AI - Stage 1: Input Detection

Detects file types from uploaded files using extension and content analysis.
Maps each file to the appropriate SourceType for downstream extraction.
"""

import logging
import mimetypes
from pathlib import Path

from backend.pipeline.base import PipelineStage
from backend.models.pipeline import PipelineContext
from backend.models.source import SourceType, SourceMetadata

logger = logging.getLogger(__name__)

# Extension-to-source-type mapping
EXTENSION_MAP: dict[str, SourceType] = {
    ".csv": SourceType.RECRUITER_CSV,
    ".pdf": SourceType.RESUME_PDF,
    ".docx": SourceType.RESUME_DOCX,
    ".doc": SourceType.RESUME_DOCX,
    ".txt": SourceType.RECRUITER_NOTES,
}

# JSON files need content inspection to distinguish ATS from LinkedIn
JSON_EXTENSIONS = {".json"}


def _detect_json_type(content: bytes, filename: str) -> SourceType:
    """
    Distinguish ATS JSON from LinkedIn JSON by inspecting content.
    Heuristic: LinkedIn profiles typically have 'headline', 'positions',
    or 'publicProfileUrl' fields.
    """
    try:
        import json
        data = json.loads(content.decode("utf-8"))
        if isinstance(data, dict):
            linkedin_keys = {"headline", "positions", "publicProfileUrl", "firstName", "lastName", "profileUrl"}
            if linkedin_keys & set(data.keys()):
                return SourceType.LINKEDIN_JSON
        return SourceType.ATS_JSON
    except Exception:
        return SourceType.ATS_JSON


class InputDetectionStage(PipelineStage):
    """Stage 1: Detect input file types and create source metadata."""

    @property
    def stage_name(self) -> str:
        return "Input Detection"

    @property
    def stage_index(self) -> int:
        return 0

    def _execute(self, context: PipelineContext) -> PipelineContext:
        detected = 0

        for filename, content in context.raw_contents.items():
            ext = Path(filename).suffix.lower()
            mime_type = mimetypes.guess_type(filename)[0]

            if ext in EXTENSION_MAP:
                source_type = EXTENSION_MAP[ext]
            elif ext in JSON_EXTENSIONS:
                source_type = _detect_json_type(content, filename)
            else:
                source_type = SourceType.UNKNOWN
                self._add_warning(context, f"Unknown file type for '{filename}' (ext: {ext})")

            metadata = SourceMetadata(
                filename=filename,
                source_type=source_type,
                file_size_bytes=len(content) if isinstance(content, bytes) else 0,
                mime_type=mime_type,
                priority=99,  # Will be auto-set in model_post_init
            )
            context.source_metadata.append(metadata)
            detected += 1

            self._add_change(context, {
                "file": filename,
                "detected_type": source_type.value,
                "size_bytes": metadata.file_size_bytes,
            })
            self._log(context, "INFO", f"Detected '{filename}' as {source_type.value}")

        context.analytics["files_uploaded"] = detected
        self._set_fields_transformed(context, detected)
        self._set_records_processed(context, detected)

        return context
