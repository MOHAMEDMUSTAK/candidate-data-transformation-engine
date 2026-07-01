from __future__ import annotations

"""
Eightfold AI - Stage 11: Quality Scoring

Generates a candidate profile quality/completeness score.
Identifies missing fields and suggests improvements.
"""

import logging

from backend.pipeline.base import PipelineStage
from backend.models.pipeline import PipelineContext
from backend.models.canonical import QualityScore

logger = logging.getLogger(__name__)

# Fields and their weights for quality scoring
QUALITY_FIELDS = {
    "full_name": {"weight": 15, "label": "Full Name"},
    "emails": {"weight": 12, "label": "Email Address"},
    "phones": {"weight": 10, "label": "Phone Number"},
    "location": {"weight": 8, "label": "Location"},
    "headline": {"weight": 8, "label": "Professional Headline"},
    "skills": {"weight": 15, "label": "Skills"},
    "experience": {"weight": 15, "label": "Work Experience"},
    "education": {"weight": 10, "label": "Education"},
    "linkedin": {"weight": 4, "label": "LinkedIn Profile"},
    "github": {"weight": 3, "label": "GitHub Profile"},
}

SUGGESTION_MAP = {
    "full_name": "Add the candidate's full name for better identification",
    "emails": "Add a verified email address for communication",
    "phones": "Add a verified phone number in E.164 format",
    "location": "Add location details (city, country) for geo-matching",
    "headline": "Add a professional headline to summarize the candidate's role",
    "skills": "Add technical and professional skills for better matching",
    "experience": "Add work experience entries with company, title, and dates",
    "education": "Add education details (institution, degree, field)",
    "linkedin": "Add a LinkedIn profile URL for cross-referencing",
    "github": "Add a GitHub profile URL to showcase technical work",
}


class QualityScoringStage(PipelineStage):
    """Stage 11: Calculate profile completeness and quality score."""

    @property
    def stage_name(self) -> str:
        return "Quality Scoring"

    @property
    def stage_index(self) -> int:
        return 10

    def _execute(self, context: PipelineContext) -> PipelineContext:
        candidate = context.canonical_candidate
        if not candidate:
            self._add_error(context, "No candidate for quality scoring")
            return context

        total_weight = sum(f["weight"] for f in QUALITY_FIELDS.values())
        earned_weight = 0
        missing: list[str] = []
        suggestions: list[str] = []
        completeness: dict[str, bool] = {}

        for field_key, field_info in QUALITY_FIELDS.items():
            is_complete = self._check_field_completeness(candidate, field_key)
            completeness[field_info["label"]] = is_complete

            if is_complete:
                earned_weight += field_info["weight"]
            else:
                missing.append(field_info["label"])
                if field_key in SUGGESTION_MAP:
                    suggestions.append(SUGGESTION_MAP[field_key])

        score = round((earned_weight / total_weight) * 100, 1)

        quality = QualityScore(
            overall_score=score,
            missing_fields=missing,
            suggestions=suggestions,
            field_completeness=completeness,
        )

        candidate.quality_score = quality
        context.analytics["quality_score"] = score

        self._set_fields_transformed(context, len(QUALITY_FIELDS))
        self._set_records_processed(context, 1)

        self._add_change(context, {
            "quality_score": score,
            "missing_fields": missing,
            "complete_fields": [k for k, v in completeness.items() if v],
        })

        return context

    def _check_field_completeness(self, candidate, field_key: str) -> bool:
        """Check if a field has meaningful data."""
        if field_key == "full_name":
            return bool(candidate.full_name and len(candidate.full_name) > 1)
        elif field_key == "emails":
            return bool(candidate.emails and len(candidate.emails) > 0)
        elif field_key == "phones":
            return bool(candidate.phones and len(candidate.phones) > 0)
        elif field_key == "location":
            return bool(candidate.location and (candidate.location.city or candidate.location.country))
        elif field_key == "headline":
            return bool(candidate.headline)
        elif field_key == "skills":
            return bool(candidate.skills and len(candidate.skills) >= 1)
        elif field_key == "experience":
            return bool(candidate.experience and len(candidate.experience) > 0)
        elif field_key == "education":
            return bool(candidate.education and len(candidate.education) > 0)
        elif field_key == "linkedin":
            return bool(candidate.links and candidate.links.linkedin)
        elif field_key == "github":
            return bool(candidate.links and candidate.links.github)
        return False
