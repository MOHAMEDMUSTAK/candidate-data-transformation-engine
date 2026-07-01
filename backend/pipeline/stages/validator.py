from __future__ import annotations

"""
Eightfold AI - Stage 10: Validation

Validates the projected output using Pydantic models.
Produces human-readable validation errors. Never crashes.
"""

import logging
from typing import Any

from pydantic import ValidationError

from backend.pipeline.base import PipelineStage
from backend.models.pipeline import PipelineContext
from backend.models.canonical import CanonicalCandidate

logger = logging.getLogger(__name__)


class ValidationStage(PipelineStage):
    """Stage 10: Validate output using Pydantic with readable error messages."""

    @property
    def stage_name(self) -> str:
        return "Validation"

    @property
    def stage_index(self) -> int:
        return 9

    def _execute(self, context: PipelineContext) -> PipelineContext:
        candidate = context.canonical_candidate
        if not candidate:
            self._add_error(context, "No candidate to validate")
            return context

        errors_found = 0

        # Validate the canonical candidate model
        try:
            # Re-validate by round-tripping through the model
            validated = CanonicalCandidate.model_validate(candidate.model_dump())
            context.canonical_candidate = validated
        except ValidationError as e:
            for error in e.errors():
                field = " → ".join(str(loc) for loc in error["loc"])
                readable_error = {
                    "field": field,
                    "error": error["msg"],
                    "type": error["type"],
                    "input": str(error.get("input", ""))[:100],
                }
                context.validation_errors.append(readable_error)
                errors_found += 1
                self._add_warning(context, f"Validation error on '{field}': {error['msg']}")

        # Additional business logic validations
        errors_found += self._validate_business_rules(candidate, context)

        # Validate projected output if custom config was used
        if context.projected_output:
            errors_found += self._validate_projected_output(context)

        context.analytics["validation_errors"] = errors_found
        self._set_fields_transformed(context, errors_found)
        self._set_records_processed(context, 1)

        if errors_found == 0:
            self._add_change(context, {"result": "All validations passed"})
        else:
            self._add_change(context, {"result": f"{errors_found} validation issues found"})

        return context

    def _validate_business_rules(self, candidate: CanonicalCandidate, context: PipelineContext) -> int:
        """Run additional business rule validations."""
        errors = 0

        # Check for empty candidate
        if not candidate.full_name:
            self._add_warning(context, "Candidate has no name")
            context.validation_errors.append({
                "field": "full_name",
                "error": "Candidate name is empty",
                "type": "missing_value",
            })
            errors += 1

        # Check email format (should already be normalized)
        for email in candidate.emails:
            if "@" not in email:
                context.validation_errors.append({
                    "field": "emails",
                    "error": f"Invalid email format: {email}",
                    "type": "format_error",
                })
                errors += 1

        # Check phone format (should be E.164)
        for phone in candidate.phones:
            if not phone.startswith("+"):
                context.validation_errors.append({
                    "field": "phones",
                    "error": f"Phone not in E.164 format: {phone}",
                    "type": "format_error",
                })
                errors += 1

        # Check confidence range
        if not (0 <= candidate.overall_confidence <= 1):
            context.validation_errors.append({
                "field": "overall_confidence",
                "error": f"Confidence {candidate.overall_confidence} out of range [0, 1]",
                "type": "range_error",
            })
            errors += 1

        return errors

    def _validate_projected_output(self, context: PipelineContext) -> int:
        """Validate the projected output for required fields."""
        errors = 0
        output = context.projected_output

        if not isinstance(output, dict):
            return errors

        # Check for any required field errors from projection
        for ve in list(context.validation_errors):
            if ve.get("source_path"):
                errors += 1

        return errors
