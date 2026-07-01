from __future__ import annotations

"""
Eightfold AI - Stage 2: Extraction

Extracts raw content from detected files using the appropriate extractor.
Dispatches to CSV, JSON, PDF, DOCX, or Notes extractor based on source type.
"""

import logging

from backend.pipeline.base import PipelineStage
from backend.models.pipeline import PipelineContext
from backend.models.source import SourceType
from backend.extractors.csv_extractor import extract_csv
from backend.extractors.json_extractor import extract_ats_json, extract_linkedin_json
from backend.extractors.pdf_extractor import extract_pdf
from backend.extractors.docx_extractor import extract_docx
from backend.extractors.notes_extractor import extract_notes

logger = logging.getLogger(__name__)


class ExtractionStage(PipelineStage):
    """Stage 2: Extract content from files using appropriate extractors."""

    @property
    def stage_name(self) -> str:
        return "Extraction"

    @property
    def stage_index(self) -> int:
        return 1

    def _execute(self, context: PipelineContext) -> PipelineContext:
        total_records = 0

        for metadata in context.source_metadata:
            content = context.raw_contents.get(metadata.filename)
            if content is None:
                self._add_warning(context, f"No content for '{metadata.filename}'")
                continue

            # Ensure content is bytes
            if isinstance(content, str):
                content = content.encode("utf-8")

            try:
                records = self._extract(metadata.source_type, content, metadata.filename)
                metadata.record_count = len(records)
                context.intermediate_records.extend(records)
                total_records += len(records)

                self._add_change(context, {
                    "file": metadata.filename,
                    "source_type": metadata.source_type.value,
                    "records_extracted": len(records),
                })
                self._log(
                    context, "INFO",
                    f"Extracted {len(records)} records from '{metadata.filename}'"
                )

            except Exception as e:
                self._add_error(context, f"Extraction failed for '{metadata.filename}': {str(e)}")
                self._log(context, "ERROR", f"Extraction failed for '{metadata.filename}': {str(e)}")

        self._set_records_processed(context, total_records)
        self._set_fields_transformed(context, total_records)
        return context

    def _extract(self, source_type: SourceType, content: bytes, filename: str):
        """Dispatch to the appropriate extractor based on source type."""
        extractors = {
            SourceType.RECRUITER_CSV: extract_csv,
            SourceType.ATS_JSON: extract_ats_json,
            SourceType.LINKEDIN_JSON: extract_linkedin_json,
            SourceType.RESUME_PDF: extract_pdf,
            SourceType.RESUME_DOCX: extract_docx,
            SourceType.RECRUITER_NOTES: extract_notes,
        }

        extractor = extractors.get(source_type)
        if extractor is None:
            logger.warning(f"No extractor for source type '{source_type}'")
            return []

        return extractor(content, filename)
