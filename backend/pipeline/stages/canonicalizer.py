from __future__ import annotations

"""
Eightfold AI - Stage 5: Canonicalization

Canonicalizes field values — primarily skill names — using
the canonical dictionary. Converts aliases to standard forms.
"""

import logging

from backend.pipeline.base import PipelineStage
from backend.models.pipeline import PipelineContext
from backend.models.provenance import RuleApplication
from backend.normalizers.skill_normalizer import normalize_skills

logger = logging.getLogger(__name__)


class CanonicalizationStage(PipelineStage):
    """Stage 5: Canonicalize skill names and other dictionary-mapped values."""

    @property
    def stage_name(self) -> str:
        return "Canonicalization"

    @property
    def stage_index(self) -> int:
        return 4

    def _execute(self, context: PipelineContext) -> PipelineContext:
        total_canonicalized = 0
        total_skill_dups = 0

        for record in context.intermediate_records:
            if record.skills:
                rules_log: list[RuleApplication] = []
                original_skills = list(record.skills)

                record.skills, skill_dups = normalize_skills(record.skills, rules_log)
                total_skill_dups += skill_dups

                # Count actual canonicalizations
                canonicalized = sum(
                    1 for r in rules_log
                    if r.rule_name == "skill_canonicalize"
                )
                total_canonicalized += canonicalized

                context.rule_applications.extend(rules_log)

                self._add_change(context, {
                    "record": record.source_file,
                    "original_skills": original_skills,
                    "canonical_skills": record.skills,
                    "canonicalized": canonicalized,
                    "duplicates_removed": skill_dups,
                })

                # Track transformation chain
                if field_key := "skills":
                    if field_key not in context.transformation_chains:
                        context.transformation_chains[field_key] = {
                            "field": field_key, "steps": [],
                            "total_transformations": 0, "final_value": None,
                        }
                    chain = context.transformation_chains[field_key]
                    chain["steps"].append({
                        "step_name": "Canonicalize Skills",
                        "stage": "canonicalization",
                        "input_value": str(original_skills),
                        "output_value": str(record.skills),
                        "rule_applied": "canonical skill dictionary",
                        "explanation": f"Skills canonicalized: {canonicalized} mappings applied, {skill_dups} duplicates removed",
                    })
                    chain["total_transformations"] = len(chain["steps"])
                    chain["final_value"] = record.skills

        context.analytics["duplicates_removed"] = (
            context.analytics.get("duplicates_removed", 0) + total_skill_dups
        )
        self._set_fields_transformed(context, total_canonicalized)
        self._set_records_processed(context, len(context.intermediate_records))

        return context
