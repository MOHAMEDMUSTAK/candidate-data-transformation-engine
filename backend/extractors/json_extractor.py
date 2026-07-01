from __future__ import annotations

"""
Eightfold AI - JSON Extractor

Parses ATS JSON blobs and LinkedIn JSON profiles into intermediate records.
Handles non-standard field names, malformed JSON, and missing fields gracefully.
"""

import json
import logging
from typing import Any

from backend.models.pipeline import IntermediateRecord
from backend.models.source import SourceType

logger = logging.getLogger(__name__)

# ATS systems use non-standard field names — map them to canonical
ATS_FIELD_MAPPINGS: dict[str, list[str]] = {
    "full_name": ["full_name", "name", "candidate_name", "applicant_name", "fullName", "candidateName"],
    "emails": ["email", "emails", "email_address", "emailAddress", "contact_email", "primaryEmail"],
    "phones": ["phone", "phones", "phone_number", "phoneNumber", "mobile", "contactPhone"],
    "city": ["city", "location_city", "locationCity", "address_city"],
    "region": ["state", "region", "province", "location_state", "locationState"],
    "country": ["country", "location_country", "countryCode", "country_code"],
    "headline": ["headline", "title", "job_title", "jobTitle", "current_title", "currentTitle", "position"],
    "skills": ["skills", "skill_list", "skillList", "key_skills", "keySkills", "competencies", "technologies"],
    "company": ["company", "current_company", "currentCompany", "employer", "organization"],
    "experience": ["experience", "work_experience", "workExperience", "employment_history", "positions"],
    "education": ["education", "education_history", "educationHistory", "degrees", "academic"],
    "linkedin": ["linkedin", "linkedin_url", "linkedinUrl", "linkedin_profile", "linkedInProfile"],
    "github": ["github", "github_url", "githubUrl", "github_profile"],
    "portfolio": ["portfolio", "website", "personal_website", "portfolioUrl"],
    "years_experience": ["years_experience", "yearsExperience", "experience_years", "yoe", "totalExperience"],
    "summary": ["summary", "bio", "about", "professional_summary", "profileSummary"],
}

# LinkedIn-specific field mappings
LINKEDIN_FIELD_MAPPINGS: dict[str, list[str]] = {
    "full_name": ["firstName+lastName", "fullName", "name", "formattedName"],
    "headline": ["headline", "title", "professionalHeadline"],
    "emails": ["emailAddress", "email", "emails"],
    "location": ["location", "locationName", "geoLocation"],
    "skills": ["skills", "skillEndorsements", "topSkills"],
    "experience": ["positions", "experience", "workExperience"],
    "education": ["education", "educations", "schools"],
    "linkedin": ["publicProfileUrl", "profileUrl", "vanityName"],
    "summary": ["summary", "about", "headline"],
}


def _get_field(data: dict[str, Any], canonical: str, mappings: dict[str, list[str]]) -> Any:
    """Look up a field using flexible name mappings."""
    for alias in mappings.get(canonical, []):
        if "+" in alias:
            # Handle composite fields like "firstName+lastName"
            parts = alias.split("+")
            values = [str(data.get(p, "")).strip() for p in parts if data.get(p)]
            if values:
                return " ".join(values)
        elif alias in data:
            return data[alias]
    return None


def _to_list(value: Any) -> list[str]:
    """Convert various value types to a list of strings."""
    if value is None:
        return []
    if isinstance(value, list):
        result = []
        for item in value:
            if isinstance(item, str):
                result.append(item.strip())
            elif isinstance(item, dict):
                # Extract name or value from dict
                for key in ["name", "value", "skill", "skillName"]:
                    if key in item:
                        result.append(str(item[key]).strip())
                        break
        return [r for r in result if r]
    if isinstance(value, str):
        # Try comma-separated
        return [s.strip() for s in value.split(",") if s.strip()]
    return []


def _parse_experience(exp_data: Any) -> list[dict[str, Any]]:
    """Parse experience data from various JSON formats."""
    if not exp_data:
        return []
    if not isinstance(exp_data, list):
        exp_data = [exp_data]

    result = []
    for item in exp_data:
        if not isinstance(item, dict):
            continue
        entry = {
            "company": item.get("company") or item.get("companyName") or item.get("organization"),
            "title": item.get("title") or item.get("position") or item.get("role") or item.get("jobTitle"),
            "start": item.get("start") or item.get("startDate") or item.get("start_date"),
            "end": item.get("end") or item.get("endDate") or item.get("end_date"),
            "summary": item.get("summary") or item.get("description"),
        }
        # Handle nested date objects
        if isinstance(entry["start"], dict):
            year = entry["start"].get("year", "")
            month = entry["start"].get("month", "")
            entry["start"] = f"{year}-{str(month).zfill(2)}" if year else None
        if isinstance(entry["end"], dict):
            year = entry["end"].get("year", "")
            month = entry["end"].get("month", "")
            entry["end"] = f"{year}-{str(month).zfill(2)}" if year else None

        if entry["company"] or entry["title"]:
            result.append(entry)

    return result


def _parse_education(edu_data: Any) -> list[dict[str, Any]]:
    """Parse education data from various JSON formats."""
    if not edu_data:
        return []
    if not isinstance(edu_data, list):
        edu_data = [edu_data]

    result = []
    for item in edu_data:
        if not isinstance(item, dict):
            continue
        entry = {
            "institution": (
                item.get("institution") or item.get("school") or
                item.get("schoolName") or item.get("university")
            ),
            "degree": item.get("degree") or item.get("degreeName"),
            "field": (
                item.get("field") or item.get("fieldOfStudy") or
                item.get("major") or item.get("specialization")
            ),
            "end_year": item.get("end_year") or item.get("endYear") or item.get("graduation_year"),
        }
        # Extract end_year from nested date
        if isinstance(entry["end_year"], dict):
            entry["end_year"] = entry["end_year"].get("year")
        if entry["end_year"]:
            try:
                entry["end_year"] = int(entry["end_year"])
            except (ValueError, TypeError):
                entry["end_year"] = None

        if entry["institution"] or entry["degree"]:
            result.append(entry)

    return result


def extract_ats_json(content: bytes, filename: str) -> list[IntermediateRecord]:
    """
    Extract candidate records from an ATS JSON blob.

    Handles single candidate objects and arrays of candidates.
    """
    records: list[IntermediateRecord] = []

    try:
        data = json.loads(content.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.warning(f"ATS JSON '{filename}' could not be parsed: {e}")
        return records

    # Handle both single object and array of candidates
    candidates = data if isinstance(data, list) else [data]

    # If the JSON has a "candidates" or "records" key, use that
    if isinstance(data, dict):
        for key in ["candidates", "records", "data", "results", "applicants"]:
            if key in data and isinstance(data[key], list):
                candidates = data[key]
                break

    for item in candidates:
        if not isinstance(item, dict):
            continue

        try:
            full_name = _get_field(item, "full_name", ATS_FIELD_MAPPINGS)
            if not full_name:
                continue

            emails = _to_list(_get_field(item, "emails", ATS_FIELD_MAPPINGS))
            phones = _to_list(_get_field(item, "phones", ATS_FIELD_MAPPINGS))
            skills = _to_list(_get_field(item, "skills", ATS_FIELD_MAPPINGS))

            # Parse location
            location = _get_field(item, "city", ATS_FIELD_MAPPINGS)
            city = None
            region = None
            country = None
            if isinstance(location, dict):
                city = location.get("city")
                region = location.get("state") or location.get("region")
                country = location.get("country")
            elif isinstance(location, str):
                city = location
            else:
                city = _get_field(item, "city", ATS_FIELD_MAPPINGS)

            if not isinstance(city, str):
                city = None
            region = _get_field(item, "region", ATS_FIELD_MAPPINGS)
            if not isinstance(region, str):
                region = None
            country = _get_field(item, "country", ATS_FIELD_MAPPINGS)
            if not isinstance(country, str):
                country = None

            # Parse years of experience
            years_exp = _get_field(item, "years_experience", ATS_FIELD_MAPPINGS)
            if years_exp is not None:
                try:
                    years_exp = int(float(years_exp))
                except (ValueError, TypeError):
                    years_exp = None

            record = IntermediateRecord(
                source_type=SourceType.ATS_JSON,
                source_file=filename,
                full_name=str(full_name).strip() if full_name else None,
                emails=emails,
                phones=phones,
                city=city,
                region=region,
                country=country,
                headline=_get_field(item, "headline", ATS_FIELD_MAPPINGS),
                years_experience=years_exp,
                skills=skills,
                experience=_parse_experience(_get_field(item, "experience", ATS_FIELD_MAPPINGS)),
                education=_parse_education(_get_field(item, "education", ATS_FIELD_MAPPINGS)),
                linkedin=_get_field(item, "linkedin", ATS_FIELD_MAPPINGS),
                github=_get_field(item, "github", ATS_FIELD_MAPPINGS),
                portfolio=_get_field(item, "portfolio", ATS_FIELD_MAPPINGS),
            )
            records.append(record)

        except Exception as e:
            logger.warning(f"ATS JSON record in '{filename}' skipped: {e}")
            continue

    logger.info(f"ATS JSON '{filename}': extracted {len(records)} records")
    return records


def extract_linkedin_json(content: bytes, filename: str) -> list[IntermediateRecord]:
    """
    Extract candidate data from a LinkedIn JSON profile.

    Handles LinkedIn-specific field naming and nested structures.
    """
    records: list[IntermediateRecord] = []

    try:
        data = json.loads(content.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.warning(f"LinkedIn JSON '{filename}' could not be parsed: {e}")
        return records

    if isinstance(data, list):
        items = data
    else:
        items = [data]

    for item in items:
        if not isinstance(item, dict):
            continue

        try:
            full_name = _get_field(item, "full_name", LINKEDIN_FIELD_MAPPINGS)
            if not full_name:
                # Try firstName + lastName
                first = item.get("firstName", "")
                last = item.get("lastName", "")
                full_name = f"{first} {last}".strip() if (first or last) else None

            if not full_name:
                continue

            emails = _to_list(_get_field(item, "emails", LINKEDIN_FIELD_MAPPINGS))
            skills = _to_list(_get_field(item, "skills", LINKEDIN_FIELD_MAPPINGS))

            # Location handling
            location = _get_field(item, "location", LINKEDIN_FIELD_MAPPINGS)
            city = None
            country = None
            if isinstance(location, dict):
                city = location.get("name") or location.get("city")
                country = location.get("country") or location.get("countryCode")
            elif isinstance(location, str):
                city = location

            record = IntermediateRecord(
                source_type=SourceType.LINKEDIN_JSON,
                source_file=filename,
                full_name=str(full_name).strip(),
                emails=emails,
                headline=_get_field(item, "headline", LINKEDIN_FIELD_MAPPINGS),
                city=city,
                country=country,
                skills=skills,
                experience=_parse_experience(_get_field(item, "experience", LINKEDIN_FIELD_MAPPINGS)),
                education=_parse_education(_get_field(item, "education", LINKEDIN_FIELD_MAPPINGS)),
                linkedin=_get_field(item, "linkedin", LINKEDIN_FIELD_MAPPINGS),
            )
            records.append(record)

        except Exception as e:
            logger.warning(f"LinkedIn record in '{filename}' skipped: {e}")
            continue

    logger.info(f"LinkedIn JSON '{filename}': extracted {len(records)} records")
    return records
