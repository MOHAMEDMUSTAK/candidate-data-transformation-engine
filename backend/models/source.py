from __future__ import annotations

"""
Eightfold AI - Source Type Definitions

Defines all supported input source types with their priority levels
for deterministic conflict resolution.
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class SourceType(str, Enum):
    """
    Supported input source types ordered by trust priority.
    Lower numeric priority = higher trust.
    """
    VERIFIED = "verified"
    RECRUITER_CSV = "recruiter_csv"
    ATS_JSON = "ats_json"
    LINKEDIN_JSON = "linkedin_json"
    RESUME_PDF = "resume_pdf"
    RESUME_DOCX = "resume_docx"
    RECRUITER_NOTES = "recruiter_notes"
    UNKNOWN = "unknown"


# Deterministic priority map — lower number = higher trust
SOURCE_PRIORITY: dict[SourceType, int] = {
    SourceType.VERIFIED: 1,
    SourceType.RECRUITER_CSV: 2,
    SourceType.ATS_JSON: 3,
    SourceType.LINKEDIN_JSON: 4,
    SourceType.RESUME_PDF: 5,
    SourceType.RESUME_DOCX: 5,  # Same priority as PDF
    SourceType.RECRUITER_NOTES: 6,
    SourceType.UNKNOWN: 7,
}


def get_source_priority(source_type: SourceType) -> int:
    """Return the numeric priority for a source type. Lower = higher trust."""
    return SOURCE_PRIORITY.get(source_type, 99)


def get_source_display_name(source_type: SourceType) -> str:
    """Return a human-readable name for a source type."""
    display_names = {
        SourceType.VERIFIED: "Verified Data",
        SourceType.RECRUITER_CSV: "Recruiter CSV",
        SourceType.ATS_JSON: "ATS JSON",
        SourceType.LINKEDIN_JSON: "LinkedIn JSON",
        SourceType.RESUME_PDF: "Resume PDF",
        SourceType.RESUME_DOCX: "Resume DOCX",
        SourceType.RECRUITER_NOTES: "Recruiter Notes",
        SourceType.UNKNOWN: "Unknown Source",
    }
    return display_names.get(source_type, "Unknown")


class SourceMetadata(BaseModel):
    """Metadata about an input source file."""
    filename: str
    source_type: SourceType
    file_size_bytes: int = 0
    mime_type: Optional[str] = None
    priority: int = Field(default=99)
    record_count: int = 0

    def model_post_init(self, __context) -> None:
        """Auto-set priority from source type after init."""
        if self.priority == 99:
            self.priority = get_source_priority(self.source_type)
