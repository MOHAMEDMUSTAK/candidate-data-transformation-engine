from __future__ import annotations

"""
Eightfold AI - PDF Resume Extractor

Extracts candidate information from PDF resumes using PyPDF2.
Uses regex-based heuristic extraction for emails, phones, skills,
sections, and dates. No ML/NLP — this is an honest tradeoff.
"""

import re
import logging
from typing import Any

from PyPDF2 import PdfReader
import io

from backend.models.pipeline import IntermediateRecord
from backend.models.source import SourceType

logger = logging.getLogger(__name__)

# Regex patterns for structured data extraction
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_PATTERN = re.compile(
    r'(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?'
    r'\d{3,5}[-.\s]?\d{3,5}(?:[-.\s]?\d{1,5})?'
)
URL_PATTERN = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
LINKEDIN_PATTERN = re.compile(r'(?:https?://)?(?:www\.)?linkedin\.com/in/[^\s<>"]+')
GITHUB_PATTERN = re.compile(r'(?:https?://)?(?:www\.)?github\.com/[^\s<>"]+')

# Section header patterns
SECTION_PATTERNS = {
    "experience": re.compile(
        r'(?:^|\n)\s*(?:work\s+)?experience|employment\s+history|professional\s+experience|work\s+history',
        re.IGNORECASE
    ),
    "education": re.compile(
        r'(?:^|\n)\s*education|academic|qualifications|degrees',
        re.IGNORECASE
    ),
    "skills": re.compile(
        r'(?:^|\n)\s*(?:technical\s+)?skills|competencies|technologies|expertise|proficiencies',
        re.IGNORECASE
    ),
    "summary": re.compile(
        r'(?:^|\n)\s*(?:professional\s+)?summary|objective|profile|about',
        re.IGNORECASE
    ),
}

# Common skill keywords to extract
SKILL_KEYWORDS = {
    "python", "java", "javascript", "typescript", "react", "angular", "vue",
    "node.js", "nodejs", "express", "django", "flask", "fastapi", "spring",
    "sql", "nosql", "mongodb", "postgresql", "mysql", "redis", "elasticsearch",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins",
    "git", "ci/cd", "agile", "scrum", "rest", "graphql", "microservices",
    "machine learning", "deep learning", "nlp", "computer vision", "ai",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "spark",
    "html", "css", "sass", "tailwind", "bootstrap", "figma",
    "c++", "c#", "go", "rust", "kotlin", "swift", "ruby", "php", "scala",
    "linux", "unix", "bash", "powershell", "data structures", "algorithms",
}

# Date patterns for experience/education
DATE_PATTERN = re.compile(
    r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
    r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
    r'\s*\d{4}',
    re.IGNORECASE
)
YEAR_PATTERN = re.compile(r'\b(19|20)\d{2}\b')


def _extract_name(text: str) -> str | None:
    """
    Extract candidate name from the first few lines of the resume.
    Heuristic: The name is typically the first non-empty line that
    isn't an email, phone, or URL.
    """
    lines = text.strip().split("\n")
    for line in lines[:5]:
        line = line.strip()
        if not line or len(line) < 2:
            continue
        if EMAIL_PATTERN.search(line):
            continue
        if PHONE_PATTERN.search(line) and len(line) < 20:
            continue
        if URL_PATTERN.search(line):
            continue
        # Name should be mostly letters and spaces, reasonably short
        if len(line) < 50 and re.match(r'^[A-Za-z\s.\-\']+$', line):
            return line.strip()

    return None


def _extract_skills_from_text(text: str) -> list[str]:
    """Extract skills by matching against known skill keywords."""
    found_skills: list[str] = []
    text_lower = text.lower()

    for skill in SKILL_KEYWORDS:
        # Word boundary matching
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.append(skill)

    return sorted(set(found_skills))


def _extract_section(text: str, section: str) -> str:
    """Extract content between section headers."""
    pattern = SECTION_PATTERNS.get(section)
    if not pattern:
        return ""

    match = pattern.search(text)
    if not match:
        return ""

    start = match.end()

    # Find the next section header
    next_section_start = len(text)
    for other_section, other_pattern in SECTION_PATTERNS.items():
        if other_section == section:
            continue
        other_match = other_pattern.search(text[start:])
        if other_match:
            pos = start + other_match.start()
            if pos < next_section_start:
                next_section_start = pos

    return text[start:next_section_start].strip()


def _parse_experience_section(section_text: str) -> list[dict[str, Any]]:
    """Parse work experience from section text using heuristics."""
    experiences: list[dict[str, Any]] = []
    if not section_text:
        return experiences

    # Split by double newline or date patterns to separate entries
    lines = section_text.split("\n")
    current_entry: dict[str, Any] = {}
    current_lines: list[str] = []

    for line in lines:
        line = line.strip()
        if not line:
            if current_lines:
                entry = _build_experience_entry(current_lines)
                if entry.get("company") or entry.get("title"):
                    experiences.append(entry)
                current_lines = []
            continue
        current_lines.append(line)

    # Don't forget the last entry
    if current_lines:
        entry = _build_experience_entry(current_lines)
        if entry.get("company") or entry.get("title"):
            experiences.append(entry)

    return experiences


def _build_experience_entry(lines: list[str]) -> dict[str, Any]:
    """Build an experience entry from a block of text lines."""
    entry: dict[str, Any] = {
        "company": None,
        "title": None,
        "start": None,
        "end": None,
        "summary": None,
    }

    if not lines:
        return entry

    # First line is usually title or company
    entry["title"] = lines[0] if lines else None

    # Look for dates
    full_text = " ".join(lines)
    dates = DATE_PATTERN.findall(full_text)
    if len(dates) >= 2:
        entry["start"] = dates[0]
        entry["end"] = dates[1]
    elif len(dates) == 1:
        entry["start"] = dates[0]

    # Second line might be company
    if len(lines) > 1:
        second_line = lines[1]
        if not DATE_PATTERN.search(second_line):
            entry["company"] = second_line

    # Rest is summary
    summary_lines = lines[2:] if len(lines) > 2 else []
    if summary_lines:
        entry["summary"] = " ".join(summary_lines)[:500]

    return entry


def _parse_education_section(section_text: str) -> list[dict[str, Any]]:
    """Parse education entries from section text."""
    education: list[dict[str, Any]] = []
    if not section_text:
        return education

    lines = section_text.split("\n")
    current_lines: list[str] = []

    for line in lines:
        line = line.strip()
        if not line:
            if current_lines:
                entry = _build_education_entry(current_lines)
                if entry.get("institution") or entry.get("degree"):
                    education.append(entry)
                current_lines = []
            continue
        current_lines.append(line)

    if current_lines:
        entry = _build_education_entry(current_lines)
        if entry.get("institution") or entry.get("degree"):
            education.append(entry)

    return education


def _build_education_entry(lines: list[str]) -> dict[str, Any]:
    """Build an education entry from text lines."""
    entry: dict[str, Any] = {
        "institution": None,
        "degree": None,
        "field": None,
        "end_year": None,
    }

    if not lines:
        return entry

    full_text = " ".join(lines)

    # Extract year
    years = YEAR_PATTERN.findall(full_text)
    if years:
        try:
            entry["end_year"] = int(years[-1])
        except ValueError:
            pass

    # First line is typically institution or degree
    entry["institution"] = lines[0] if lines else None

    # Look for degree keywords
    degree_patterns = [
        r"(?:Bachelor|Master|PhD|Ph\.D|B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?|B\.?E\.?|M\.?E\.?|"
        r"B\.?Tech|M\.?Tech|MBA|Associate|Diploma)[^\n]*"
    ]
    for pattern in degree_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            entry["degree"] = match.group(0).strip()
            break

    # Look for field of study
    if len(lines) > 1:
        for line in lines[1:]:
            if not YEAR_PATTERN.search(line) and len(line) > 3:
                if not entry["degree"]:
                    entry["degree"] = line
                else:
                    entry["field"] = line
                break

    return entry


def extract_pdf(content: bytes, filename: str) -> list[IntermediateRecord]:
    """
    Extract candidate information from a PDF resume.

    Uses PyPDF2 for text extraction and regex-based heuristics
    for field identification. Gracefully handles corrupt/empty PDFs.

    Args:
        content: Raw PDF file bytes
        filename: Original filename for provenance

    Returns:
        List containing one IntermediateRecord (one resume = one candidate)
    """
    records: list[IntermediateRecord] = []

    try:
        reader = PdfReader(io.BytesIO(content))
    except Exception as e:
        logger.warning(f"PDF '{filename}' could not be opened: {e}")
        return records

    # Extract all text
    text_parts: list[str] = []
    for page in reader.pages:
        try:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        except Exception as e:
            logger.warning(f"PDF '{filename}' page extraction error: {e}")
            continue

    if not text_parts:
        logger.warning(f"PDF '{filename}' contains no extractable text")
        return records

    full_text = "\n".join(text_parts)

    # Extract structured fields
    name = _extract_name(full_text)
    emails = list(set(EMAIL_PATTERN.findall(full_text)))
    phones = list(set(PHONE_PATTERN.findall(full_text)))
    skills = _extract_skills_from_text(full_text)

    # Extract URLs
    linkedin = None
    github = None
    other_links: list[str] = []

    linkedin_matches = LINKEDIN_PATTERN.findall(full_text)
    if linkedin_matches:
        linkedin = linkedin_matches[0]

    github_matches = GITHUB_PATTERN.findall(full_text)
    if github_matches:
        github = github_matches[0]

    all_urls = URL_PATTERN.findall(full_text)
    for url in all_urls:
        if "linkedin" not in url.lower() and "github" not in url.lower():
            other_links.append(url)

    # Extract sections
    experience = _parse_experience_section(_extract_section(full_text, "experience"))
    education = _parse_education_section(_extract_section(full_text, "education"))

    # Clean phone numbers (remove very short/long matches that are likely false positives)
    phones = [p.strip() for p in phones if 7 <= len(re.sub(r'\D', '', p)) <= 15]

    record = IntermediateRecord(
        source_type=SourceType.RESUME_PDF,
        source_file=filename,
        full_name=name,
        emails=sorted(set(emails)),
        phones=sorted(set(phones)),
        skills=skills,
        experience=experience,
        education=education,
        linkedin=linkedin,
        github=github,
        other_links=other_links,
        raw_text=full_text[:5000],  # Store first 5000 chars for reference
    )
    records.append(record)

    logger.info(
        f"PDF '{filename}': extracted name='{name}', "
        f"{len(emails)} emails, {len(phones)} phones, "
        f"{len(skills)} skills, {len(experience)} experience entries"
    )
    return records
