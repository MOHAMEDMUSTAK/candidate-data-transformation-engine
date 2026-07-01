from __future__ import annotations

"""
Eightfold AI - Stage 7: Conflict Resolution

Deterministic priority-based conflict resolution.
When multiple sources provide different values for the same field,
the highest-priority source wins. Every decision is explained.
Rejected values are stored in provenance — never discarded.
"""

import logging
from datetime import datetime
from typing import Any

from backend.pipeline.base import PipelineStage
from backend.models.pipeline import PipelineContext, ConflictRecord
from backend.models.provenance import ProvenanceEntry, FieldProvenance
from backend.models.source import SourceType, get_source_display_name

logger = logging.getLogger(__name__)


class ConflictResolutionStage(PipelineStage):
    """Stage 7: Resolve conflicts between sources deterministically."""

    @property
    def stage_name(self) -> str:
        return "Conflict Resolution"

    @property
    def stage_index(self) -> int:
        return 6

    def _execute(self, context: PipelineContext) -> PipelineContext:
        if not context.canonical_candidate:
            self._add_error(context, "No canonical candidate to resolve conflicts for")
            return context

        field_candidates = context.analytics.get("_field_candidates", {})
        conflicts_detected = 0
        conflicts_resolved = 0

        for field_name, candidates in field_candidates.items():
            if len(candidates) <= 1:
                continue

            conflicts_detected += 1

            # Sort by priority (lower = higher trust) — deterministic
            sorted_candidates = sorted(candidates, key=lambda c: c["priority"])

            winner = sorted_candidates[0]
            rejected = sorted_candidates[1:]

            # Build human-readable explanation
            winner_source_name = self._source_name_from_file(winner["source"], context)
            explanation_parts = [
                f"'{field_name}' selected from {winner_source_name} "
                f"(priority {winner['priority']}) because it has higher source priority."
            ]
            for rej in rejected:
                rej_source = self._source_name_from_file(rej["source"], context)
                explanation_parts.append(
                    f"Rejected '{rej['value']}' from {rej_source} "
                    f"(priority {rej['priority']})."
                )
            explanation = " ".join(explanation_parts)

            # Create conflict record
            conflict = ConflictRecord(
                field=field_name,
                candidates=[
                    {"value": c["value"], "source": c["source"], "priority": c["priority"]}
                    for c in sorted_candidates
                ],
                winner={
                    "value": winner["value"],
                    "source": winner["source"],
                    "priority": winner["priority"],
                },
                rejected=[
                    {"value": r["value"], "source": r["source"], "priority": r["priority"]}
                    for r in rejected
                ],
                explanation=explanation,
            )
            context.conflicts.append(conflict)
            conflicts_resolved += 1

            # Create provenance entries for winner and all rejected
            now = datetime.utcnow().isoformat() + "Z"

            winner_provenance = ProvenanceEntry(
                field=field_name,
                original_value=winner["value"],
                normalized_value=winner["value"],
                winning_value=winner["value"],
                source=winner["source"],
                source_type=self._get_source_type(winner["source"], context),
                source_priority=winner["priority"],
                extraction_method="direct",
                timestamp=now,
                rules_applied=["priority_based_conflict_resolution"],
                accepted=True,
                explanation=f"Selected from {winner_source_name} — highest priority source.",
            )
            context.provenance_entries.append(winner_provenance)

            for rej in rejected:
                rej_source_name = self._source_name_from_file(rej["source"], context)
                rejected_provenance = ProvenanceEntry(
                    field=field_name,
                    original_value=rej["value"],
                    normalized_value=rej["value"],
                    winning_value=winner["value"],
                    source=rej["source"],
                    source_type=self._get_source_type(rej["source"], context),
                    source_priority=rej["priority"],
                    extraction_method="direct",
                    timestamp=now,
                    rules_applied=["priority_based_conflict_resolution"],
                    accepted=False,
                    explanation=(
                        f"Rejected: {rej_source_name} (priority {rej['priority']}) "
                        f"lost to {winner_source_name} (priority {winner['priority']})."
                    ),
                )
                context.provenance_entries.append(rejected_provenance)

            # Build field provenance
            fp = FieldProvenance(field=field_name)
            fp.winning_entry = winner_provenance
            fp.rejected_entries = [
                ProvenanceEntry(
                    field=field_name,
                    original_value=r["value"],
                    source=r["source"],
                    source_type=self._get_source_type(r["source"], context),
                    source_priority=r["priority"],
                    accepted=False,
                    explanation=f"Lower priority than {winner_source_name}",
                )
                for r in rejected
            ]
            fp.all_entries = [winner_provenance] + fp.rejected_entries
            context.field_provenance[field_name] = fp.model_dump()

            # Track transformation chain
            if field_name not in context.transformation_chains:
                context.transformation_chains[field_name] = {
                    "field": field_name, "steps": [],
                    "total_transformations": 0, "final_value": None,
                }
            chain = context.transformation_chains[field_name]
            chain["steps"].append({
                "step_name": f"Conflict Resolution for {field_name}",
                "stage": "conflict_resolution",
                "input_value": str([c["value"] for c in sorted_candidates]),
                "output_value": str(winner["value"]),
                "rule_applied": "priority_based_conflict_resolution",
                "explanation": explanation,
            })
            chain["total_transformations"] = len(chain["steps"])
            chain["final_value"] = winner["value"]

            self._add_change(context, {
                "field": field_name,
                "winner": winner["value"],
                "winner_source": winner["source"],
                "rejected_count": len(rejected),
                "explanation": explanation,
            })

        # Also create provenance for non-conflicting fields
        self._create_non_conflict_provenance(context)

        context.analytics["conflicts_detected"] = conflicts_detected
        context.analytics["conflicts_resolved"] = conflicts_resolved
        self._set_fields_transformed(context, conflicts_resolved)
        self._set_records_processed(context, conflicts_detected)

        # Clean up internal field
        context.analytics.pop("_field_candidates", None)

        return context

    def _create_non_conflict_provenance(self, context: PipelineContext) -> None:
        """Create provenance entries for fields that had no conflicts."""
        candidate = context.canonical_candidate
        if not candidate:
            return

        now = datetime.utcnow().isoformat() + "Z"

        # Determine primary source
        primary_source = "unknown"
        primary_type = "unknown"
        if context.source_metadata:
            primary = min(context.source_metadata, key=lambda s: s.priority)
            primary_source = primary.filename
            primary_type = primary.source_type.value

        single_source_fields = {
            "full_name": candidate.full_name,
            "emails": candidate.emails,
            "phones": candidate.phones,
            "headline": candidate.headline,
        }

        for field_name, value in single_source_fields.items():
            if field_name in context.field_provenance:
                continue  # Already handled by conflict resolution
            if value is None or value == "" or value == []:
                continue

            prov = ProvenanceEntry(
                field=field_name,
                original_value=value,
                normalized_value=value,
                winning_value=value,
                source=primary_source,
                source_type=primary_type,
                extraction_method="direct",
                timestamp=now,
                accepted=True,
                explanation=f"Single source value from {primary_source}. No conflict.",
            )
            context.provenance_entries.append(prov)
            context.field_provenance[field_name] = FieldProvenance(
                field=field_name,
                winning_entry=prov,
                all_entries=[prov],
            ).model_dump()

    def _source_name_from_file(self, filename: str, context: PipelineContext) -> str:
        """Get a display name for a source file."""
        for meta in context.source_metadata:
            if meta.filename == filename:
                return get_source_display_name(meta.source_type)
        return filename

    def _get_source_type(self, filename: str, context: PipelineContext) -> str:
        """Get the source type string for a filename."""
        for meta in context.source_metadata:
            if meta.filename == filename:
                return meta.source_type.value
        return "unknown"
