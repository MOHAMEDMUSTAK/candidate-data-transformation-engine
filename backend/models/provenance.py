from __future__ import annotations

"""
Eightfold AI - Provenance Models

Every field transformation is tracked with full provenance:
- What the original value was
- How it was normalized
- Which source it came from
- Whether it was accepted or rejected
- A human-readable explanation of the decision
"""

from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime


class ProvenanceEntry(BaseModel):
    """
    Complete provenance record for a single field value from a single source.

    Stores the full transformation chain: original → normalized → final,
    along with the decision reasoning and confidence.
    """
    field: str = Field(..., description="Canonical field name (e.g., 'emails', 'phones')")
    original_value: Any = Field(default=None, description="Raw value as extracted from source")
    normalized_value: Any = Field(default=None, description="Value after normalization rules")
    winning_value: Any = Field(default=None, description="Final selected value after conflict resolution")
    source: str = Field(..., description="Source filename")
    source_type: str = Field(..., description="Source type (e.g., 'recruiter_csv')")
    source_priority: int = Field(default=99, description="Numeric priority (lower = higher trust)")
    extraction_method: str = Field(default="direct", description="How the value was extracted")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="ISO 8601 timestamp of processing"
    )
    rules_applied: list[str] = Field(
        default_factory=list,
        description="List of transformation rule names applied"
    )
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Per-field confidence score")
    accepted: bool = Field(default=False, description="Whether this value was selected as the winner")
    explanation: str = Field(
        default="",
        description="Human-readable explanation of why this value was accepted or rejected"
    )


class FieldProvenance(BaseModel):
    """
    Aggregated provenance for a single field across all sources.
    Contains the winning entry and all rejected alternatives.
    """
    field: str
    winning_entry: Optional[ProvenanceEntry] = None
    rejected_entries: list[ProvenanceEntry] = Field(default_factory=list)
    all_entries: list[ProvenanceEntry] = Field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        """True if multiple sources provided values for this field."""
        return len(self.all_entries) > 1

    @property
    def conflict_count(self) -> int:
        """Number of rejected alternative values."""
        return len(self.rejected_entries)


class TransformationStep(BaseModel):
    """A single step in a field's transformation chain for replay."""
    step_name: str = Field(..., description="Name of the transformation step")
    stage: str = Field(..., description="Pipeline stage (e.g., 'normalization')")
    input_value: Any = Field(default=None, description="Value before this step")
    output_value: Any = Field(default=None, description="Value after this step")
    rule_applied: str = Field(default="", description="Rule that caused the transformation")
    explanation: str = Field(default="", description="Human-readable explanation")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )


class FieldTransformationChain(BaseModel):
    """Complete transformation chain for a single field — for replay feature."""
    field: str
    steps: list[TransformationStep] = Field(default_factory=list)
    final_value: Any = None
    total_transformations: int = 0


class RuleApplication(BaseModel):
    """Record of a single rule being applied during the pipeline."""
    rule_name: str = Field(..., description="Name of the rule")
    rule_category: str = Field(default="general", description="Category (email, phone, skill, date)")
    description: str = Field(default="", description="What the rule does")
    field: str = Field(..., description="Which field was affected")
    original_value: Any = Field(default=None)
    transformed_value: Any = Field(default=None)
    stage: str = Field(default="", description="Pipeline stage where applied")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )
