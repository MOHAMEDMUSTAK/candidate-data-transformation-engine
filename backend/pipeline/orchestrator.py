from __future__ import annotations

"""
Eightfold AI - Pipeline Orchestrator

Runs all 12 pipeline stages sequentially, collecting results,
provenance, analytics, and timing information.
"""

import time
import logging
from datetime import datetime
from typing import Any

from backend.models.pipeline import PipelineContext, PipelineResponse
from backend.pipeline.stages.input_detector import InputDetectionStage
from backend.pipeline.stages.extractor import ExtractionStage
from backend.pipeline.stages.parser import ParsingStage
from backend.pipeline.stages.normalizer import NormalizationStage
from backend.pipeline.stages.canonicalizer import CanonicalizationStage
from backend.pipeline.stages.merger import MergeStage
from backend.pipeline.stages.conflict_resolver import ConflictResolutionStage
from backend.pipeline.stages.confidence import ConfidenceCalculationStage
from backend.pipeline.stages.projector import ProjectionStage
from backend.pipeline.stages.validator import ValidationStage
from backend.pipeline.stages.quality_scorer import QualityScoringStage
from backend.pipeline.stages.exporter import ExportStage

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Orchestrates the 12-stage candidate data transformation pipeline.

    Each stage receives the PipelineContext, mutates it, and passes it on.
    The orchestrator wraps the entire execution with timing and error handling.
    """

    def __init__(self):
        """Initialize all pipeline stages in order."""
        self.stages = [
            InputDetectionStage(),      # 0: Input Detection
            ExtractionStage(),          # 1: Extraction
            ParsingStage(),             # 2: Parsing
            NormalizationStage(),       # 3: Normalization
            CanonicalizationStage(),    # 4: Canonicalization
            MergeStage(),               # 5: Merge
            ConflictResolutionStage(),  # 6: Conflict Resolution
            ConfidenceCalculationStage(), # 7: Confidence
            ProjectionStage(),          # 8: Projection
            ValidationStage(),          # 9: Validation
            QualityScoringStage(),      # 10: Quality Scoring
            ExportStage(),              # 11: Export
        ]

    def execute(
        self,
        files: dict[str, bytes],
        output_config: dict[str, Any] | None = None,
    ) -> PipelineResponse:
        """
        Run the full pipeline on uploaded files.

        Args:
            files: Dict of filename → file content bytes
            output_config: Optional runtime output configuration

        Returns:
            PipelineResponse with all results, provenance, and analytics
        """
        pipeline_start = time.perf_counter()

        # Initialize context
        context = PipelineContext(
            raw_contents=files,
            output_config=output_config,
        )

        logger.info(f"Pipeline started with {len(files)} files")

        # Execute each stage sequentially
        for stage in self.stages:
            try:
                context = stage.execute(context)
            except Exception as e:
                logger.exception(f"Critical error in stage '{stage.stage_name}'")
                # Continue to next stage — don't crash the pipeline

        total_ms = (time.perf_counter() - pipeline_start) * 1000
        context.analytics["processing_time_ms"] = round(total_ms, 2)

        # Build response
        response = self._build_response(context, total_ms)

        logger.info(f"Pipeline completed in {total_ms:.1f}ms")
        return response

    def _build_response(self, context: PipelineContext, total_ms: float) -> PipelineResponse:
        """Build the API response from the pipeline context."""
        candidate_dict = None
        if context.canonical_candidate:
            candidate_dict = context.canonical_candidate.model_dump()

        # Serialize field provenance
        field_prov_serialized = {}
        for key, value in context.field_provenance.items():
            if hasattr(value, "model_dump"):
                field_prov_serialized[key] = value.model_dump()
            else:
                field_prov_serialized[key] = value

        # Serialize transformation chains
        chains_serialized = {}
        for key, value in context.transformation_chains.items():
            if hasattr(value, "model_dump"):
                chains_serialized[key] = value.model_dump()
            else:
                chains_serialized[key] = value

        # Serialize field confidences
        field_confidences = []
        if context.canonical_candidate and context.canonical_candidate.field_confidences:
            field_confidences = [fc.model_dump() for fc in context.canonical_candidate.field_confidences]

        # Serialize quality score
        quality_score = None
        if context.canonical_candidate and context.canonical_candidate.quality_score:
            quality_score = context.canonical_candidate.quality_score.model_dump()

        return PipelineResponse(
            success=len(context.validation_errors) == 0,
            candidate=candidate_dict,
            projected_output=context.projected_output,
            exported_json=context.exported_json,
            stage_results=[sr.model_dump() for sr in context.stage_results],
            provenance=[p.model_dump() for p in context.provenance_entries],
            field_provenance=field_prov_serialized,
            transformation_chains=chains_serialized,
            rule_applications=[r.model_dump() for r in context.rule_applications],
            conflicts=[c.model_dump() for c in context.conflicts],
            analytics=context.analytics,
            validation_errors=context.validation_errors,
            log_entries=context.log_entries,
            field_confidences=field_confidences,
            quality_score=quality_score,
            total_time_ms=round(total_ms, 2),
        )
