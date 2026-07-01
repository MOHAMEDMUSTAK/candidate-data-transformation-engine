from __future__ import annotations

"""
Eightfold AI - Stage 12: Export

Exports the final canonical candidate as clean, formatted JSON.
Assembles provenance entries for the output.
"""

import json
import logging
from typing import Any

from backend.pipeline.base import PipelineStage
from backend.models.pipeline import PipelineContext

logger = logging.getLogger(__name__)


class ExportStage(PipelineStage):
    """Stage 12: Export final output as formatted JSON."""

    @property
    def stage_name(self) -> str:
        return "Export"

    @property
    def stage_index(self) -> int:
        return 11

    def _execute(self, context: PipelineContext) -> PipelineContext:
        candidate = context.canonical_candidate
        if not candidate:
            self._add_error(context, "No candidate to export")
            return context

        # Build provenance summary for output
        provenance_summary = []
        for prov in context.provenance_entries:
            if prov.accepted:
                provenance_summary.append({
                    "field": prov.field,
                    "source": prov.source,
                    "method": prov.extraction_method,
                })

        candidate.provenance = provenance_summary

        # Determine what to export
        if context.projected_output:
            output = context.projected_output
            # Update provenance in projected output
            if "provenance" in output:
                output["provenance"] = provenance_summary
        else:
            output = candidate.model_dump(exclude={"field_confidences", "quality_score"})

        # Format as pretty JSON
        try:
            exported = json.dumps(output, indent=2, ensure_ascii=False, default=str)
            context.exported_json = exported
        except (TypeError, ValueError) as e:
            self._add_error(context, f"JSON serialization failed: {str(e)}")
            context.exported_json = json.dumps({"error": str(e)})

        self._set_fields_transformed(context, len(output) if isinstance(output, dict) else 1)
        self._set_records_processed(context, 1)

        self._add_change(context, {
            "output_size_bytes": len(context.exported_json) if context.exported_json else 0,
            "fields_exported": len(output) if isinstance(output, dict) else 0,
        })

        return context
