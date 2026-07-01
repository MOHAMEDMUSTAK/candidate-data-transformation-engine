from __future__ import annotations

"""
Eightfold AI - Stage 4: Normalization

Normalizes field values across all intermediate records:
- Emails: trim, lowercase, validate, dedup
- Phones: convert to E.164
- Dates: convert to YYYY-MM
- Countries: convert to ISO-3166 Alpha-2
"""

import logging
from typing import Any

from backend.pipeline.base import PipelineStage
from backend.models.pipeline import PipelineContext, IntermediateRecord
from backend.models.provenance import RuleApplication, TransformationStep, FieldTransformationChain
from backend.normalizers.email_normalizer import normalize_emails
from backend.normalizers.phone_normalizer import normalize_phones
from backend.normalizers.date_normalizer import normalize_date
from backend.normalizers.location_normalizer import normalize_country

logger = logging.getLogger(__name__)


class NormalizationStage(PipelineStage):
    """Stage 4: Normalize field values across all records."""

    @property
    def stage_name(self) -> str:
        return "Normalization"

    @property
    def stage_index(self) -> int:
        return 3

    def _execute(self, context: PipelineContext) -> PipelineContext:
        fields_normalized = 0
        total_duplicates = 0

        for record in context.intermediate_records:
            rules_log: list[RuleApplication] = []

            # Normalize emails
            if record.emails:
                original_emails = list(record.emails)
                record.emails, email_dups = normalize_emails(record.emails, rules_log)
                total_duplicates += email_dups
                if record.emails != original_emails:
                    fields_normalized += 1
                    self._track_transformation(
                        context, "emails", original_emails, record.emails,
                        "normalization", record.source_file
                    )

            # Normalize phones
            if record.phones:
                original_phones = list(record.phones)
                record.phones, phone_dups = normalize_phones(record.phones, rules_log=rules_log)
                total_duplicates += phone_dups
                if record.phones != original_phones:
                    fields_normalized += 1
                    self._track_transformation(
                        context, "phones", original_phones, record.phones,
                        "normalization", record.source_file
                    )

            # Normalize country
            if record.country:
                original_country = record.country
                record.country = normalize_country(record.country, rules_log)
                if record.country != original_country:
                    fields_normalized += 1
                    self._track_transformation(
                        context, "location.country", original_country, record.country,
                        "normalization", record.source_file
                    )

            # Normalize dates in experience
            for exp in record.experience:
                if exp.get("start"):
                    original_start = exp["start"]
                    exp["start"] = normalize_date(exp["start"], rules_log, "experience.start")
                    if exp["start"] != original_start:
                        fields_normalized += 1

                if exp.get("end"):
                    original_end = exp["end"]
                    exp["end"] = normalize_date(exp["end"], rules_log, "experience.end")
                    if exp["end"] != original_end:
                        fields_normalized += 1

            # Store all rule applications in context
            context.rule_applications.extend(rules_log)

            self._add_change(context, {
                "record": record.source_file,
                "fields_normalized": fields_normalized,
                "duplicates_removed": total_duplicates,
            })

        # Copy intermediate to normalized (in this design they're the same list, mutated)
        context.normalized_records = list(context.intermediate_records)

        context.analytics["fields_normalized"] = fields_normalized
        context.analytics["duplicates_removed"] = total_duplicates
        self._set_fields_transformed(context, fields_normalized)
        self._set_records_processed(context, len(context.intermediate_records))

        return context

    def _track_transformation(
        self, context: PipelineContext, field: str,
        original: Any, normalized: Any, stage: str, source: str
    ) -> None:
        """Track a transformation step for the replay feature."""
        if field not in context.transformation_chains:
            context.transformation_chains[field] = FieldTransformationChain(
                field=field
            ).model_dump()

        chain = context.transformation_chains[field]
        if isinstance(chain, dict):
            if "steps" not in chain:
                chain["steps"] = []
            chain["steps"].append({
                "step_name": f"Normalize {field}",
                "stage": stage,
                "input_value": original if not isinstance(original, list) else str(original),
                "output_value": normalized if not isinstance(normalized, list) else str(normalized),
                "rule_applied": f"{field} normalization",
                "explanation": f"Value normalized from {original} to {normalized}",
            })
            chain["total_transformations"] = len(chain["steps"])
            chain["final_value"] = normalized
