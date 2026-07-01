from __future__ import annotations

"""
Eightfold AI - Stage 3: Parsing

Validates and cleans intermediate records after extraction.
Ensures all records have consistent field types before normalization.
"""

import logging
import hashlib
from typing import Any

from backend.pipeline.base import PipelineStage
from backend.models.pipeline import PipelineContext, IntermediateRecord

logger = logging.getLogger(__name__)


class ParsingStage(PipelineStage):
    """Stage 3: Validate and clean intermediate records."""

    @property
    def stage_name(self) -> str:
        return "Parsing"

    @property
    def stage_index(self) -> int:
        return 2

    def _execute(self, context: PipelineContext) -> PipelineContext:
        parsed_count = 0
        fields_parsed = 0

        for record in context.intermediate_records:
            # Generate candidate_id if missing
            if not record.candidate_id:
                record.candidate_id = self._generate_candidate_id(record)

            # Clean string fields
            if record.full_name:
                record.full_name = record.full_name.strip()
                fields_parsed += 1

            if record.headline:
                record.headline = record.headline.strip()
                fields_parsed += 1

            # Ensure list fields are actually lists of strings
            record.emails = [str(e).strip() for e in record.emails if e]
            record.phones = [str(p).strip() for p in record.phones if p]
            record.skills = [str(s).strip() for s in record.skills if s]
            fields_parsed += len(record.emails) + len(record.phones) + len(record.skills)

            # Clean experience entries
            for exp in record.experience:
                for key in ["company", "title", "summary"]:
                    if key in exp and exp[key]:
                        exp[key] = str(exp[key]).strip()
                        fields_parsed += 1

            # Clean education entries
            for edu in record.education:
                for key in ["institution", "degree", "field"]:
                    if key in edu and edu[key]:
                        edu[key] = str(edu[key]).strip()
                        fields_parsed += 1

            parsed_count += 1
            self._add_change(context, {
                "record": record.source_file,
                "source_type": record.source_type.value,
                "candidate_id": record.candidate_id,
                "fields": fields_parsed,
            })

        context.analytics["fields_parsed"] = fields_parsed
        self._set_fields_transformed(context, fields_parsed)
        self._set_records_processed(context, parsed_count)

        return context

    def _generate_candidate_id(self, record: IntermediateRecord) -> str:
        """
        Generate a deterministic candidate ID from available data.
        Uses hash of name + first email for consistency.
        """
        parts: list[str] = []
        if record.full_name:
            parts.append(record.full_name.lower().strip())
        if record.emails:
            parts.append(record.emails[0].lower().strip())

        if not parts:
            # Fallback: use source file name
            parts.append(record.source_file)

        raw = "|".join(parts)
        return "CND-" + hashlib.sha256(raw.encode()).hexdigest()[:12].upper()
