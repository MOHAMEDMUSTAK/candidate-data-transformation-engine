from __future__ import annotations

"""
Eightfold AI - Pipeline Stage Base Class

Abstract base class for all pipeline stages.
Provides automatic timing, structured logging, error handling,
and stage result metadata collection.
"""

import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from backend.models.pipeline import PipelineContext, StageResult, StageStatus

logger = logging.getLogger(__name__)


class PipelineStage(ABC):
    """
    Base class for all pipeline stages.

    Subclasses must implement:
        - stage_name: str property
        - stage_index: int property
        - _execute(context): the actual stage logic

    The base class wraps _execute with:
        - Timing measurement
        - Error capture (stages never crash the pipeline)
        - Structured logging
        - Stage result creation
    """

    @property
    @abstractmethod
    def stage_name(self) -> str:
        """Human-readable name for this stage."""
        ...

    @property
    @abstractmethod
    def stage_index(self) -> int:
        """Zero-based index in the pipeline sequence."""
        ...

    @abstractmethod
    def _execute(self, context: PipelineContext) -> PipelineContext:
        """
        Execute the stage logic.

        Args:
            context: The pipeline context with accumulated data.

        Returns:
            The updated pipeline context.
        """
        ...

    def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Execute the stage with timing, logging, and error handling.

        This is the public method called by the orchestrator.
        It wraps _execute with cross-cutting concerns.
        """
        start_time = time.perf_counter()
        start_iso = datetime.utcnow().isoformat() + "Z"

        stage_result = StageResult(
            stage_name=self.stage_name,
            stage_index=self.stage_index,
            status=StageStatus.RUNNING,
            start_time=start_iso,
        )

        self._log(context, "INFO", f"Stage '{self.stage_name}' started")

        try:
            context = self._execute(context)

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            stage_result.end_time = datetime.utcnow().isoformat() + "Z"
            stage_result.execution_time_ms = round(elapsed_ms, 2)

            if stage_result.errors:
                stage_result.status = StageStatus.ERROR
            elif stage_result.warnings:
                stage_result.status = StageStatus.WARNING
            else:
                stage_result.status = StageStatus.SUCCESS

            # Update result with any warnings/errors added during execution
            for existing in context.stage_results:
                if existing.stage_name == self.stage_name:
                    stage_result.warnings = existing.warnings
                    stage_result.errors = existing.errors
                    stage_result.fields_transformed = existing.fields_transformed
                    stage_result.records_processed = existing.records_processed
                    stage_result.details = existing.details
                    stage_result.changes = existing.changes
                    if existing.errors:
                        stage_result.status = StageStatus.ERROR
                    elif existing.warnings:
                        stage_result.status = StageStatus.WARNING
                    break

            # Remove any existing result for this stage and add the final one
            context.stage_results = [
                r for r in context.stage_results
                if r.stage_name != self.stage_name
            ]
            context.stage_results.append(stage_result)

            self._log(
                context, "INFO",
                f"Stage '{self.stage_name}' completed in {elapsed_ms:.1f}ms "
                f"({stage_result.fields_transformed} fields transformed)"
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            stage_result.end_time = datetime.utcnow().isoformat() + "Z"
            stage_result.execution_time_ms = round(elapsed_ms, 2)
            stage_result.status = StageStatus.ERROR
            stage_result.errors.append(f"Unhandled error: {str(e)}")

            # Remove any existing result for this stage and add error result
            context.stage_results = [
                r for r in context.stage_results
                if r.stage_name != self.stage_name
            ]
            context.stage_results.append(stage_result)

            self._log(context, "ERROR", f"Stage '{self.stage_name}' failed: {str(e)}")
            logger.exception(f"Pipeline stage '{self.stage_name}' failed")

        return context

    def _add_warning(self, context: PipelineContext, message: str) -> None:
        """Add a warning to the current stage result."""
        for result in context.stage_results:
            if result.stage_name == self.stage_name:
                result.warnings.append(message)
                context.analytics["warnings"] = context.analytics.get("warnings", 0) + 1
                return
        # If no result yet, create a placeholder
        context.stage_results.append(StageResult(
            stage_name=self.stage_name,
            stage_index=self.stage_index,
            warnings=[message],
        ))
        context.analytics["warnings"] = context.analytics.get("warnings", 0) + 1

    def _add_error(self, context: PipelineContext, message: str) -> None:
        """Add an error to the current stage result."""
        for result in context.stage_results:
            if result.stage_name == self.stage_name:
                result.errors.append(message)
                return
        context.stage_results.append(StageResult(
            stage_name=self.stage_name,
            stage_index=self.stage_index,
            errors=[message],
        ))

    def _set_fields_transformed(self, context: PipelineContext, count: int) -> None:
        """Set the fields_transformed count for this stage."""
        for result in context.stage_results:
            if result.stage_name == self.stage_name:
                result.fields_transformed = count
                return
        context.stage_results.append(StageResult(
            stage_name=self.stage_name,
            stage_index=self.stage_index,
            fields_transformed=count,
        ))

    def _set_records_processed(self, context: PipelineContext, count: int) -> None:
        """Set the records_processed count for this stage."""
        for result in context.stage_results:
            if result.stage_name == self.stage_name:
                result.records_processed = count
                return
        context.stage_results.append(StageResult(
            stage_name=self.stage_name,
            stage_index=self.stage_index,
            records_processed=count,
        ))

    def _add_change(self, context: PipelineContext, change: dict) -> None:
        """Add a specific change record to this stage."""
        for result in context.stage_results:
            if result.stage_name == self.stage_name:
                result.changes.append(change)
                return
        context.stage_results.append(StageResult(
            stage_name=self.stage_name,
            stage_index=self.stage_index,
            changes=[change],
        ))

    def _log(self, context: PipelineContext, level: str, message: str) -> None:
        """Add a structured log entry to the pipeline context."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "stage": self.stage_name,
            "stage_index": self.stage_index,
            "message": message,
        }
        context.log_entries.append(entry)

        # Also log to Python logger
        log_fn = getattr(logger, level.lower(), logger.info)
        log_fn(f"[{self.stage_name}] {message}")
