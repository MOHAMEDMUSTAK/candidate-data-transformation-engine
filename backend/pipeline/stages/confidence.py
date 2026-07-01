from __future__ import annotations

"""
Eightfold AI - Stage 8: Confidence Calculation

Calculates per-field confidence scores based on:
- Source priority (higher priority = higher confidence)
- Source agreement (more sources agree = higher confidence)
- Validation status (valid values = higher confidence)
- Completeness (non-empty values = higher confidence)
"""

import logging
from typing import Any

from backend.pipeline.base import PipelineStage
from backend.models.pipeline import PipelineContext
from backend.models.canonical import FieldConfidence
from backend.models.source import SourceType

logger = logging.getLogger(__name__)

# Source base weights for confidence calculation
SOURCE_WEIGHTS: dict[str, float] = {
    SourceType.VERIFIED.value: 1.0,
    SourceType.RECRUITER_CSV.value: 0.95,
    SourceType.ATS_JSON.value: 0.90,
    SourceType.LINKEDIN_JSON.value: 0.85,
    SourceType.RESUME_PDF.value: 0.80,
    SourceType.RESUME_DOCX.value: 0.80,
    SourceType.RECRUITER_NOTES.value: 0.70,
    SourceType.UNKNOWN.value: 0.50,
}


class ConfidenceCalculationStage(PipelineStage):
    """Stage 8: Calculate per-field and overall confidence scores."""

    @property
    def stage_name(self) -> str:
        return "Confidence Calculation"

    @property
    def stage_index(self) -> int:
        return 7

    def _execute(self, context: PipelineContext) -> PipelineContext:
        candidate = context.canonical_candidate
        if not candidate:
            self._add_error(context, "No candidate for confidence calculation")
            return context

        field_confidences: list[FieldConfidence] = []
        total_sources = len(context.source_metadata)

        # Calculate confidence for each field
        fields_to_check = [
            ("full_name", candidate.full_name, lambda v: bool(v and len(v) > 1)),
            ("emails", candidate.emails, lambda v: bool(v and len(v) > 0)),
            ("phones", candidate.phones, lambda v: bool(v and len(v) > 0)),
            ("location", candidate.location, lambda v: bool(v and (v.city or v.country))),
            ("headline", candidate.headline, lambda v: bool(v)),
            ("skills", candidate.skills, lambda v: bool(v and len(v) > 0)),
            ("experience", candidate.experience, lambda v: bool(v and len(v) > 0)),
            ("education", candidate.education, lambda v: bool(v and len(v) > 0)),
            ("links", candidate.links, lambda v: bool(v and (v.linkedin or v.github))),
        ]

        confidence_sum = 0.0
        confidence_count = 0

        for field_name, value, validator in fields_to_check:
            conf = self._calculate_field_confidence(
                field_name, value, validator, context, total_sources
            )
            field_confidences.append(conf)
            confidence_sum += conf.confidence
            confidence_count += 1

            # Update provenance entries with confidence
            for prov in context.provenance_entries:
                if prov.field == field_name and prov.accepted:
                    prov.confidence = conf.confidence

        # Calculate overall confidence
        overall = confidence_sum / max(confidence_count, 1)
        candidate.overall_confidence = round(overall, 4)
        candidate.field_confidences = field_confidences

        context.analytics["average_confidence"] = round(overall * 100, 1)

        self._set_fields_transformed(context, confidence_count)
        self._set_records_processed(context, 1)

        self._add_change(context, {
            "overall_confidence": round(overall * 100, 1),
            "field_count": confidence_count,
            "fields": {fc.field: round(fc.confidence * 100, 1) for fc in field_confidences},
        })

        return context

    def _calculate_field_confidence(
        self, field_name: str, value: Any, validator: callable,
        context: PipelineContext, total_sources: int,
    ) -> FieldConfidence:
        """
        Calculate confidence for a single field.

        Formula:
            confidence = base_weight × validation_factor × agreement_factor × completeness_factor
        """
        # Find which sources contributed this field
        contributing_sources: list[str] = []
        for record in context.intermediate_records:
            has_value = False
            if field_name == "full_name" and record.full_name:
                has_value = True
            elif field_name == "emails" and record.emails:
                has_value = True
            elif field_name == "phones" and record.phones:
                has_value = True
            elif field_name == "skills" and record.skills:
                has_value = True
            elif field_name == "experience" and record.experience:
                has_value = True
            elif field_name == "education" and record.education:
                has_value = True
            elif field_name == "headline" and record.headline:
                has_value = True
            elif field_name == "location" and (record.city or record.country):
                has_value = True
            elif field_name == "links" and (record.linkedin or record.github):
                has_value = True

            if has_value:
                contributing_sources.append(record.source_type.value)

        # Base weight from highest-priority contributing source
        base_weight = 0.5
        if contributing_sources:
            best_weight = max(SOURCE_WEIGHTS.get(s, 0.5) for s in contributing_sources)
            base_weight = best_weight

        # Validation factor
        validation_factor = 1.0 if validator(value) else 0.3

        # Agreement factor — how many sources agree
        sources_agreeing = len(contributing_sources)
        agreement_factor = min(sources_agreeing / max(total_sources, 1), 1.0)
        # Boost: even 1 source is OK
        agreement_factor = max(agreement_factor, 0.5)

        # Completeness factor
        completeness_factor = 1.0 if validator(value) else 0.0

        confidence = base_weight * validation_factor * agreement_factor * completeness_factor
        confidence = min(max(confidence, 0.0), 1.0)

        return FieldConfidence(
            field=field_name,
            confidence=round(confidence, 4),
            source_count=total_sources,
            sources_agreeing=sources_agreeing,
        )
