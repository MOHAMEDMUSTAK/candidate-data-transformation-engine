from __future__ import annotations

"""
Eightfold AI - Stage 9: Projection

Applies runtime configuration to project the canonical candidate
into the requested output format. Supports field selection,
renaming, type coercion, and missing value strategies.

IMPORTANT: Projection never modifies the canonical data.
It creates a view/copy.
"""

import logging
import re
from typing import Any

from backend.pipeline.base import PipelineStage
from backend.models.pipeline import PipelineContext
from backend.models.config_schema import OutputConfig

logger = logging.getLogger(__name__)


class ProjectionStage(PipelineStage):
    """Stage 9: Apply output configuration to project canonical data."""

    @property
    def stage_name(self) -> str:
        return "Projection"

    @property
    def stage_index(self) -> int:
        return 8

    def _execute(self, context: PipelineContext) -> PipelineContext:
        candidate = context.canonical_candidate
        if not candidate:
            self._add_error(context, "No candidate for projection")
            return context

        # Parse output config
        config = self._parse_config(context.output_config)

        if config.has_custom_fields():
            # Custom projection — only include specified fields
            projected = self._apply_custom_projection(candidate, config, context)
        else:
            # Default projection — full canonical schema
            projected = candidate.model_dump(exclude={"field_confidences", "quality_score"})

        # Handle confidence and provenance toggles
        if not config.include_confidence:
            projected.pop("overall_confidence", None)
            projected.pop("field_confidences", None)

        if not config.include_provenance:
            projected.pop("provenance", None)

        context.projected_output = projected

        self._set_fields_transformed(context, len(projected))
        self._set_records_processed(context, 1)

        self._add_change(context, {
            "fields_projected": list(projected.keys()),
            "custom_config": config.has_custom_fields(),
        })

        return context

    def _parse_config(self, config_dict: dict[str, Any] | None) -> OutputConfig:
        """Parse output config from dict, with graceful error handling."""
        if not config_dict:
            return OutputConfig()
        try:
            return OutputConfig(**config_dict)
        except Exception as e:
            logger.warning(f"Invalid output config, using default: {e}")
            return OutputConfig()

    def _apply_custom_projection(
        self, candidate: Any, config: OutputConfig, context: PipelineContext
    ) -> dict[str, Any]:
        """Apply custom field projections to the canonical candidate."""
        canonical_dict = candidate.model_dump()
        projected: dict[str, Any] = {}

        for field_proj in config.fields:
            output_path = field_proj.path
            source_path = field_proj.source_from or output_path

            try:
                value = self._resolve_path(canonical_dict, source_path)
            except (KeyError, IndexError, TypeError):
                value = None

            if value is None:
                if config.on_missing == "null":
                    projected[output_path] = None
                elif config.on_missing == "omit":
                    continue
                elif config.on_missing == "error":
                    if field_proj.required:
                        context.validation_errors.append({
                            "field": output_path,
                            "error": f"Required field '{output_path}' is missing",
                            "source_path": source_path,
                        })
                    projected[output_path] = None
            else:
                projected[output_path] = value

        # Always include confidence and provenance if configured
        if config.include_confidence:
            projected["overall_confidence"] = candidate.overall_confidence

        if config.include_provenance:
            projected["provenance"] = canonical_dict.get("provenance", [])

        return projected

    def _resolve_path(self, data: dict[str, Any], path: str) -> Any:
        """
        Resolve a dotted/indexed path against a dictionary.

        Supports:
            - "full_name" → data["full_name"]
            - "emails[0]" → data["emails"][0]
            - "skills[].name" → [s["name"] for s in data["skills"]]
            - "location.country" → data["location"]["country"]
        """
        # Handle array projection: "skills[].name"
        if "[]." in path:
            array_part, field_part = path.split("[].", 1)
            array_val = self._resolve_path(data, array_part)
            if isinstance(array_val, list):
                return [
                    item.get(field_part) if isinstance(item, dict) else None
                    for item in array_val
                ]
            return None

        parts = re.split(r'\.', path)
        current = data

        for part in parts:
            # Handle indexed access: "emails[0]"
            match = re.match(r'^(\w+)\[(\d+)\]$', part)
            if match:
                key = match.group(1)
                idx = int(match.group(2))
                if isinstance(current, dict) and key in current:
                    current = current[key]
                    if isinstance(current, list) and idx < len(current):
                        current = current[idx]
                    else:
                        return None
                else:
                    return None
            elif isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return None
            else:
                return None

        return current
