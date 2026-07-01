from __future__ import annotations

"""
Eightfold AI - Date Normalizer

Normalizes dates to YYYY-MM format using python-dateutil.
Handles various input formats: "Jan 2025", "January 2025",
"01/2025", "2025-01-15", etc.
"""

import logging
import re
from typing import Any

from dateutil import parser as dateutil_parser

from backend.models.provenance import RuleApplication

logger = logging.getLogger(__name__)


def normalize_date(
    date_str: str,
    rules_log: list[RuleApplication] | None = None,
    field_name: str = "date",
) -> str | None:
    """
    Normalize a date string to YYYY-MM format.

    Args:
        date_str: Raw date string
        rules_log: Optional list to record applied rules
        field_name: Field name for provenance tracking

    Returns:
        Date in YYYY-MM format or None if unparseable.
    """
    original = date_str
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()
    if not date_str:
        return None

    # Handle "Present" / "Current" as-is
    if date_str.lower() in ("present", "current", "now", "ongoing"):
        return "Present"

    # Try direct YYYY-MM pattern first
    match = re.match(r'^(\d{4})-(\d{2})$', date_str)
    if match:
        return date_str  # Already normalized

    # Try YYYY pattern (year only)
    match = re.match(r'^(\d{4})$', date_str)
    if match:
        result = f"{date_str}-01"
        if rules_log is not None:
            rules_log.append(RuleApplication(
                rule_name="date_year_only",
                rule_category="date",
                description=f"Year-only date '{original}' defaulted to January",
                field=field_name,
                original_value=original,
                transformed_value=result,
                stage="normalization",
            ))
        return result

    # Try dateutil for everything else
    try:
        parsed = dateutil_parser.parse(date_str, fuzzy=True)
        result = parsed.strftime("%Y-%m")

        if rules_log is not None and result != original:
            rules_log.append(RuleApplication(
                rule_name="date_format_normalize",
                rule_category="date",
                description=f"Date '{original}' normalized to YYYY-MM format",
                field=field_name,
                original_value=original,
                transformed_value=result,
                stage="normalization",
            ))

        return result

    except (ValueError, OverflowError) as e:
        if rules_log is not None:
            rules_log.append(RuleApplication(
                rule_name="date_parse_failed",
                rule_category="date",
                description=f"Date '{original}' could not be parsed: {str(e)}",
                field=field_name,
                original_value=original,
                transformed_value=None,
                stage="normalization",
            ))
        logger.debug(f"Date '{original}' parse failed: {e}")
        return None
