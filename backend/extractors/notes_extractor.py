from __future__ import annotations

"""
Eightfold AI - Recruiter Notes Extractor

Extracts basic candidate information (emails, phones, skills, name)
from free-text recruiter notes using regex heuristics.
"""

import logging
import re
from typing import Any

from backend.models.pipeline import IntermediateRecord
from backend.models.source import SourceType
from backend.extractors.pdf_extractor import (
    EMAIL_PATTERN,
    PHONE_PATTERN,
    _extract_skills_from_text,
)

logger = logging.getLogger(__name__)

# Very basic heuristic for finding a name in short notes
# "Candidate: John Doe" or "Name: Jane Smith"
NAME_PATTERN = re.compile(r'(?:Candidate|Name|Profile):\s*([A-Za-z\s.\-\']+)', re.IGNORECASE)


def extract_notes(content: bytes, filename: str) -> list[IntermediateRecord]:
    """
    Extract candidate information from free-text notes (.txt).
    """
    records: list[IntermediateRecord] = []

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = content.decode("latin-1")
        except Exception as e:
            logger.warning(f"Notes file '{filename}' could not be decoded: {e}")
            return records

    if not text.strip():
        logger.warning(f"Notes file '{filename}' is empty")
        return records

    name = None
    name_match = NAME_PATTERN.search(text)
    if name_match:
        name_candidate = name_match.group(1).strip()
        if len(name_candidate.split()) <= 4:  # Reasonable name length
            name = name_candidate

    emails = list(set(EMAIL_PATTERN.findall(text)))
    phones = list(set(PHONE_PATTERN.findall(text)))
    skills = _extract_skills_from_text(text)

    # Clean phone numbers
    phones = [p.strip() for p in phones if 7 <= len(re.sub(r'\D', '', p)) <= 15]

    record = IntermediateRecord(
        source_type=SourceType.RECRUITER_NOTES,
        source_file=filename,
        full_name=name,
        emails=sorted(set(emails)),
        phones=sorted(set(phones)),
        skills=skills,
        raw_text=text[:1000],  # Store first 1000 chars
    )
    records.append(record)

    logger.info(
        f"Notes '{filename}': extracted name='{name}', "
        f"{len(emails)} emails, {len(phones)} phones"
    )
    return records
