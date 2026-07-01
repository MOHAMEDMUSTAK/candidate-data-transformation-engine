from __future__ import annotations

"""
Eightfold AI - Pipeline Stage Models

Models for pipeline execution context, stage results,
and the overall pipeline response.
"""

from pydantic import BaseModel, Field
from typing import Any, Optional
from enum import Enum
from datetime import datetime

from backend.models.canonical import CanonicalCandidate
from backend.models.provenance import (
    ProvenanceEntry,
    FieldProvenance,
    FieldTransformationChain,
    RuleApplication,
)
from backend.models.source import SourceMetadata, SourceType


class StageStatus(str, Enum):
    """Status of a pipeline stage execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


class StageResult(BaseModel):
    """Result of executing a single pipeline stage."""
    stage_name: str
    stage_index: int
    status: StageStatus = StageStatus.PENDING
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    execution_time_ms: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    fields_transformed: int = 0
    records_processed: int = 0
    details: dict[str, Any] = Field(default_factory=dict)
    changes: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of specific changes made in this stage"
    )


class IntermediateRecord(BaseModel):
    """
    Intermediate representation of candidate data from a single source.
    This is the normalized intermediate format before merging.
    """
    source_type: SourceType
    source_file: str
    candidate_id: Optional[str] = None
    full_name: Optional[str] = None
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    headline: Optional[str] = None
    years_experience: Optional[int] = None
    skills: list[str] = Field(default_factory=list)
    experience: list[dict[str, Any]] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    other_links: list[str] = Field(default_factory=list)
    raw_text: Optional[str] = None
    extra_fields: dict[str, Any] = Field(default_factory=dict)


class ConflictRecord(BaseModel):
    """Record of a conflict between sources for a single field."""
    field: str
    candidates: list[dict[str, Any]] = Field(
        default_factory=list,
        description="[{value, source, source_type, priority}]"
    )
    winner: Optional[dict[str, Any]] = None
    rejected: list[dict[str, Any]] = Field(default_factory=list)
    explanation: str = ""
    confidence: float = 0.0


class PipelineContext(BaseModel):
    """
    Mutable context flowing through all pipeline stages.
    Accumulates data, provenance, decisions, and analytics.
    """
    # Input
    source_metadata: list[SourceMetadata] = Field(default_factory=list)
    raw_contents: dict[str, Any] = Field(default_factory=dict)

    # Intermediate data
    intermediate_records: list[IntermediateRecord] = Field(default_factory=list)
    normalized_records: list[IntermediateRecord] = Field(default_factory=list)

    # Output
    canonical_candidate: Optional[CanonicalCandidate] = None
    projected_output: Optional[dict[str, Any]] = None
    exported_json: Optional[str] = None

    # Provenance & Decisions
    provenance_entries: list[ProvenanceEntry] = Field(default_factory=list)
    field_provenance: dict[str, FieldProvenance] = Field(default_factory=dict)
    transformation_chains: dict[str, FieldTransformationChain] = Field(default_factory=dict)
    rule_applications: list[RuleApplication] = Field(default_factory=list)
    conflicts: list[ConflictRecord] = Field(default_factory=list)

    # Pipeline execution tracking
    stage_results: list[StageResult] = Field(default_factory=list)

    # Analytics counters
    analytics: dict[str, Any] = Field(default_factory=lambda: {
        "files_uploaded": 0,
        "fields_parsed": 0,
        "fields_normalized": 0,
        "duplicates_removed": 0,
        "conflicts_detected": 0,
        "conflicts_resolved": 0,
        "validation_errors": 0,
        "warnings": 0,
        "processing_time_ms": 0.0,
        "average_confidence": 0.0,
        "quality_score": 0.0,
    })

    # Validation
    validation_errors: list[dict[str, Any]] = Field(default_factory=list)

    # Configuration (set before pipeline starts)
    output_config: Optional[dict[str, Any]] = None

    # Logging
    log_entries: list[dict[str, Any]] = Field(default_factory=list)


class PipelineResponse(BaseModel):
    """Complete response from a pipeline execution."""
    success: bool = True
    candidate: Optional[dict[str, Any]] = None
    projected_output: Optional[dict[str, Any]] = None
    exported_json: Optional[str] = None
    stage_results: list[StageResult] = Field(default_factory=list)
    provenance: list[dict[str, Any]] = Field(default_factory=list)
    field_provenance: dict[str, Any] = Field(default_factory=dict)
    transformation_chains: dict[str, Any] = Field(default_factory=dict)
    rule_applications: list[dict[str, Any]] = Field(default_factory=list)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    analytics: dict[str, Any] = Field(default_factory=dict)
    validation_errors: list[dict[str, Any]] = Field(default_factory=list)
    log_entries: list[dict[str, Any]] = Field(default_factory=list)
    field_confidences: list[dict[str, Any]] = Field(default_factory=list)
    quality_score: Optional[dict[str, Any]] = None
    total_time_ms: float = 0.0
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )
