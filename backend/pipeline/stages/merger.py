from __future__ import annotations

"""
Eightfold AI - Stage 6: Merge

Merges multiple intermediate records into a single canonical candidate.
Combines all values before conflict resolution.
"""

import logging
from typing import Any

from backend.pipeline.base import PipelineStage
from backend.models.pipeline import PipelineContext, IntermediateRecord
from backend.models.canonical import (
    CanonicalCandidate, LocationModel, LinksModel, SkillEntry,
    ExperienceEntry, EducationEntry,
)
from backend.models.source import get_source_priority

logger = logging.getLogger(__name__)


class MergeStage(PipelineStage):
    """Stage 6: Merge all intermediate records into one candidate."""

    @property
    def stage_name(self) -> str:
        return "Merge"

    @property
    def stage_index(self) -> int:
        return 5

    def _execute(self, context: PipelineContext) -> PipelineContext:
        records = context.intermediate_records
        if not records:
            self._add_warning(context, "No records to merge")
            return context

        # Sort records by source priority (highest trust first) for determinism
        sorted_records = sorted(
            records,
            key=lambda r: get_source_priority(r.source_type)
        )

        # Use the candidate_id from the highest-priority record
        candidate_id = sorted_records[0].candidate_id or "CND-UNKNOWN"

        # Merge all fields
        all_emails: list[str] = []
        all_phones: list[str] = []
        all_skills_raw: list[tuple[str, str, str]] = []  # (skill, source_type, source_file)
        all_experience: list[ExperienceEntry] = []
        all_education: list[EducationEntry] = []
        names: list[tuple[str, int, str]] = []  # (name, priority, source)
        headlines: list[tuple[str, int, str]] = []
        cities: list[tuple[str, int, str]] = []
        regions: list[tuple[str, int, str]] = []
        countries: list[tuple[str, int, str]] = []
        years_exp: list[tuple[int, int, str]] = []
        linkedins: list[tuple[str, int, str]] = []
        githubs: list[tuple[str, int, str]] = []
        portfolios: list[tuple[str, int, str]] = []
        other_links: list[str] = []

        for record in sorted_records:
            priority = get_source_priority(record.source_type)
            source = record.source_file

            if record.full_name:
                names.append((record.full_name, priority, source))
            if record.headline:
                headlines.append((record.headline, priority, source))
            if record.city:
                cities.append((record.city, priority, source))
            if record.region:
                regions.append((record.region, priority, source))
            if record.country:
                countries.append((record.country, priority, source))
            if record.years_experience is not None:
                years_exp.append((record.years_experience, priority, source))
            if record.linkedin:
                linkedins.append((record.linkedin, priority, source))
            if record.github:
                githubs.append((record.github, priority, source))
            if record.portfolio:
                portfolios.append((record.portfolio, priority, source))

            all_emails.extend(record.emails)
            all_phones.extend(record.phones)

            for skill in record.skills:
                all_skills_raw.append((skill, record.source_type.value, source))

            for exp_dict in record.experience:
                all_experience.append(ExperienceEntry(
                    company=exp_dict.get("company"),
                    title=exp_dict.get("title"),
                    start=exp_dict.get("start"),
                    end=exp_dict.get("end"),
                    summary=exp_dict.get("summary"),
                ))

            for edu_dict in record.education:
                all_education.append(EducationEntry(
                    institution=edu_dict.get("institution"),
                    degree=edu_dict.get("degree"),
                    field=edu_dict.get("field"),
                    end_year=edu_dict.get("end_year"),
                ))

            other_links.extend(record.other_links)

        # Deduplicate list fields
        unique_emails = sorted(set(e.lower().strip() for e in all_emails if e))
        unique_phones = sorted(set(all_phones))

        # Build skill entries with source tracking
        skill_map: dict[str, SkillEntry] = {}
        for skill_name, source_type, source_file in all_skills_raw:
            key = skill_name.lower()
            if key not in skill_map:
                skill_map[key] = SkillEntry(name=skill_name, sources=[source_type])
            else:
                if source_type not in skill_map[key].sources:
                    skill_map[key].sources.append(source_type)
        skills = sorted(skill_map.values(), key=lambda s: s.name)

        # Select scalar values (highest priority wins — will be refined in conflict resolution)
        full_name = names[0][0] if names else ""
        headline = headlines[0][0] if headlines else None
        city = cities[0][0] if cities else None
        region = regions[0][0] if regions else None
        country = countries[0][0] if countries else None
        yoe = years_exp[0][0] if years_exp else None
        linkedin = linkedins[0][0] if linkedins else None
        github = githubs[0][0] if githubs else None
        portfolio = portfolios[0][0] if portfolios else None

        # Store merge candidates in context for conflict resolution
        context.conflicts = []  # Will be populated by conflict resolution stage

        # Store all candidate values for each scalar field
        field_candidates = {
            "full_name": [(n, p, s) for n, p, s in names],
            "headline": [(h, p, s) for h, p, s in headlines],
            "location.city": [(c, p, s) for c, p, s in cities],
            "location.region": [(r, p, s) for r, p, s in regions],
            "location.country": [(c, p, s) for c, p, s in countries],
            "years_experience": [(y, p, s) for y, p, s in years_exp],
            "links.linkedin": [(l, p, s) for l, p, s in linkedins],
            "links.github": [(g, p, s) for g, p, s in githubs],
            "links.portfolio": [(p_val, p, s) for p_val, p, s in portfolios],
        }

        # Store for conflict resolution stage
        context.analytics["_field_candidates"] = {
            k: [{"value": v, "priority": p, "source": s} for v, p, s in candidates]
            for k, candidates in field_candidates.items()
            if len(candidates) > 1
        }

        # Build canonical candidate
        candidate = CanonicalCandidate(
            candidate_id=candidate_id,
            full_name=full_name,
            emails=unique_emails,
            phones=unique_phones,
            location=LocationModel(city=city, region=region, country=country),
            headline=headline,
            years_experience=yoe,
            skills=skills,
            experience=all_experience,
            education=all_education,
            links=LinksModel(
                linkedin=linkedin,
                github=github,
                portfolio=portfolio,
                other=sorted(set(other_links)),
            ),
        )

        context.canonical_candidate = candidate

        self._add_change(context, {
            "candidate_id": candidate_id,
            "records_merged": len(records),
            "total_emails": len(unique_emails),
            "total_phones": len(unique_phones),
            "total_skills": len(skills),
            "total_experience": len(all_experience),
            "total_education": len(all_education),
        })

        self._set_fields_transformed(context, len(unique_emails) + len(unique_phones) + len(skills))
        self._set_records_processed(context, len(records))

        return context
