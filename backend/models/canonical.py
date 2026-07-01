from __future__ import annotations

"""
Eightfold AI - Canonical Candidate Model

The single source of truth for candidate data.
Matches the assignment specification exactly.
All downstream projections derive from this model.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Any, Optional


class LocationModel(BaseModel):
    """Candidate location with ISO-3166 Alpha-2 country code."""
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = Field(
        default=None,
        description="ISO-3166 Alpha-2 country code"
    )


class LinksModel(BaseModel):
    """Candidate web presence links."""
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    other: list[str] = Field(default_factory=list)


class SkillEntry(BaseModel):
    """A single skill with confidence and source tracking."""
    name: str = Field(..., description="Canonical skill name")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    sources: list[str] = Field(default_factory=list, description="Source types that reported this skill")


class ExperienceEntry(BaseModel):
    """A single work experience entry."""
    company: Optional[str] = None
    title: Optional[str] = None
    start: Optional[str] = Field(default=None, description="Start date in YYYY-MM format")
    end: Optional[str] = Field(default=None, description="End date in YYYY-MM format or 'Present'")
    summary: Optional[str] = None


class EducationEntry(BaseModel):
    """A single education entry."""
    institution: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    end_year: Optional[int] = None


class FieldConfidence(BaseModel):
    """Per-field confidence score for visualization."""
    field: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_count: int = 0
    sources_agreeing: int = 0


class QualityScore(BaseModel):
    """Profile completeness and quality assessment."""
    overall_score: float = Field(ge=0.0, le=100.0, description="Percentage 0-100")
    missing_fields: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    field_completeness: dict[str, bool] = Field(default_factory=dict)


class CanonicalCandidate(BaseModel):
    """
    The canonical candidate profile — the single output of the pipeline.

    This model is immutable after creation. Projection creates views
    of this model without modifying it.
    """
    candidate_id: str = Field(..., description="Deterministic candidate identifier")
    full_name: str = Field(default="", description="Full name of the candidate")
    emails: list[str] = Field(default_factory=list, description="Deduplicated, lowercased emails")
    phones: list[str] = Field(default_factory=list, description="E.164 formatted phone numbers")
    location: LocationModel = Field(default_factory=LocationModel)
    headline: Optional[str] = None
    years_experience: Optional[int] = None
    skills: list[SkillEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    links: LinksModel = Field(default_factory=LinksModel)
    provenance: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Provenance entries — [{field, source, method}]"
    )
    overall_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Weighted average confidence across all fields"
    )

    # Extended fields for novelty features (not part of export by default)
    field_confidences: list[FieldConfidence] = Field(default_factory=list)
    quality_score: Optional[QualityScore] = None

    @field_validator("emails", mode="before")
    @classmethod
    def deduplicate_emails(cls, v: list[str]) -> list[str]:
        """Ensure emails are unique and sorted for determinism."""
        if not v:
            return []
        seen: set[str] = set()
        result: list[str] = []
        for email in v:
            lower = email.strip().lower()
            if lower and lower not in seen:
                seen.add(lower)
                result.append(lower)
        return sorted(result)

    @field_validator("phones", mode="before")
    @classmethod
    def deduplicate_phones(cls, v: list[str]) -> list[str]:
        """Ensure phones are unique and sorted for determinism."""
        if not v:
            return []
        seen: set[str] = set()
        result: list[str] = []
        for phone in v:
            cleaned = phone.strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                result.append(cleaned)
        return sorted(result)
