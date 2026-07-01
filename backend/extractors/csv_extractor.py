from __future__ import annotations

"""
Eightfold AI - CSV Extractor

Parses recruiter CSV exports into intermediate records.
Handles flexible column naming, missing columns, encoding issues,
and empty rows gracefully.
"""

import logging
import io
from typing import Any

import pandas as pd

from backend.models.pipeline import IntermediateRecord
from backend.models.source import SourceType

logger = logging.getLogger(__name__)

# Flexible column mapping — maps various header names to canonical fields
COLUMN_MAPPINGS: dict[str, list[str]] = {
    "full_name": ["full_name", "name", "candidate_name", "full name", "candidate"],
    "emails": ["email", "emails", "email_address", "e-mail", "email address", "contact_email"],
    "phones": ["phone", "phones", "phone_number", "telephone", "mobile", "contact_phone", "phone number"],
    "city": ["city", "location_city", "candidate_city"],
    "region": ["state", "region", "province", "location_state"],
    "country": ["country", "location_country", "country_code"],
    "headline": ["headline", "title", "job_title", "current_title", "position", "current title"],
    "company": ["company", "current_company", "employer", "organization", "current company"],
    "skills": ["skills", "skill_list", "key_skills", "competencies"],
    "experience_years": ["years_experience", "experience_years", "yoe", "years of experience", "experience"],
    "linkedin": ["linkedin", "linkedin_url", "linkedin_profile"],
    "github": ["github", "github_url", "github_profile"],
}


def _find_column(df_columns: list[str], canonical_field: str) -> str | None:
    """Find a matching column name using flexible mapping."""
    lower_columns = {col.lower().strip(): col for col in df_columns}

    for alias in COLUMN_MAPPINGS.get(canonical_field, []):
        if alias.lower() in lower_columns:
            return lower_columns[alias.lower()]

    return None


def _safe_str(value: Any) -> str | None:
    """Convert a value to string safely, returning None for NaN/empty."""
    if pd.isna(value) or value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _safe_list(value: Any, delimiter: str = ",") -> list[str]:
    """Convert a potentially delimited string to a list."""
    if pd.isna(value) or value is None:
        return []
    s = str(value).strip()
    if not s:
        return []
    items = [item.strip() for item in s.split(delimiter) if item.strip()]
    return items


def extract_csv(content: bytes, filename: str) -> list[IntermediateRecord]:
    """
    Extract candidate records from a recruiter CSV file.

    Args:
        content: Raw CSV file bytes
        filename: Original filename for provenance tracking

    Returns:
        List of intermediate records, one per CSV row

    Handles:
        - Flexible column headers
        - Missing columns (warns, doesn't crash)
        - Empty rows (skipped)
        - Encoding issues (tries utf-8, then latin-1)
    """
    records: list[IntermediateRecord] = []

    # Try parsing with different encodings
    df = None
    for encoding in ["utf-8", "latin-1", "cp1252"]:
        try:
            df = pd.read_csv(io.BytesIO(content), encoding=encoding)
            break
        except Exception:
            continue

    if df is None or df.empty:
        logger.warning(f"CSV file '{filename}' could not be parsed or is empty")
        return records

    logger.info(f"CSV '{filename}': {len(df)} rows, columns: {list(df.columns)}")

    for idx, row in df.iterrows():
        try:
            # Map columns flexibly
            name_col = _find_column(list(df.columns), "full_name")
            email_col = _find_column(list(df.columns), "emails")
            phone_col = _find_column(list(df.columns), "phones")
            city_col = _find_column(list(df.columns), "city")
            region_col = _find_column(list(df.columns), "region")
            country_col = _find_column(list(df.columns), "country")
            headline_col = _find_column(list(df.columns), "headline")
            company_col = _find_column(list(df.columns), "company")
            skills_col = _find_column(list(df.columns), "skills")
            exp_years_col = _find_column(list(df.columns), "experience_years")
            linkedin_col = _find_column(list(df.columns), "linkedin")
            github_col = _find_column(list(df.columns), "github")

            full_name = _safe_str(row.get(name_col)) if name_col else None
            if not full_name:
                continue  # Skip rows without a name

            emails = _safe_list(row.get(email_col)) if email_col else []
            phones = _safe_list(row.get(phone_col)) if phone_col else []
            skills = _safe_list(row.get(skills_col)) if skills_col else []

            # Build experience from headline + company
            experience = []
            company = _safe_str(row.get(company_col)) if company_col else None
            headline = _safe_str(row.get(headline_col)) if headline_col else None
            if company or headline:
                experience.append({
                    "company": company,
                    "title": headline,
                    "start": None,
                    "end": None,
                    "summary": None,
                })

            # Parse years of experience
            years_exp = None
            if exp_years_col:
                try:
                    val = row.get(exp_years_col)
                    if not pd.isna(val):
                        years_exp = int(float(val))
                except (ValueError, TypeError):
                    pass

            record = IntermediateRecord(
                source_type=SourceType.RECRUITER_CSV,
                source_file=filename,
                full_name=full_name,
                emails=emails,
                phones=phones,
                city=_safe_str(row.get(city_col)) if city_col else None,
                region=_safe_str(row.get(region_col)) if region_col else None,
                country=_safe_str(row.get(country_col)) if country_col else None,
                headline=headline,
                years_experience=years_exp,
                skills=skills,
                experience=experience,
                linkedin=_safe_str(row.get(linkedin_col)) if linkedin_col else None,
                github=_safe_str(row.get(github_col)) if github_col else None,
            )
            records.append(record)

        except Exception as e:
            logger.warning(f"CSV row {idx} in '{filename}' skipped: {e}")
            continue

    logger.info(f"CSV '{filename}': extracted {len(records)} records")
    return records
