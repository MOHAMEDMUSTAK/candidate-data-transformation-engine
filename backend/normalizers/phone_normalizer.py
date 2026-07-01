from __future__ import annotations

"""
Eightfold AI - Phone Normalizer

Converts phone numbers to E.164 international format using the
phonenumbers library. Default region is configurable (defaults to IN).
"""

import logging
import re
from typing import Any

import phonenumbers

from backend.models.provenance import RuleApplication
from backend.config import settings

logger = logging.getLogger(__name__)


def normalize_phone(
    phone: str,
    default_region: str | None = None,
    rules_log: list[RuleApplication] | None = None,
) -> str | None:
    """
    Normalize a single phone number to E.164 format.

    Args:
        phone: Raw phone string
        default_region: ISO country code for numbers without country code (e.g., "IN")
        rules_log: Optional list to record applied rules

    Returns:
        E.164 formatted phone string or None if invalid.
    """
    original = phone
    region = default_region or settings.default_phone_region

    # Clean the input
    phone = phone.strip()
    if not phone:
        return None

    try:
        parsed = phonenumbers.parse(phone, region)

        if not phonenumbers.is_valid_number(parsed):
            # Try without region
            try:
                parsed = phonenumbers.parse(phone, None)
                if not phonenumbers.is_valid_number(parsed):
                    if rules_log is not None:
                        rules_log.append(RuleApplication(
                            rule_name="phone_validation_failed",
                            rule_category="phone",
                            description=f"Phone '{original}' is not a valid number",
                            field="phones",
                            original_value=original,
                            transformed_value=None,
                            stage="normalization",
                        ))
                    return None
            except phonenumbers.NumberParseException:
                if rules_log is not None:
                    rules_log.append(RuleApplication(
                        rule_name="phone_validation_failed",
                        rule_category="phone",
                        description=f"Phone '{original}' is not a valid number",
                        field="phones",
                        original_value=original,
                        transformed_value=None,
                        stage="normalization",
                    ))
                return None

        e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

        # Detect the country
        country_code = phonenumbers.region_code_for_number(parsed)

        if rules_log is not None:
            rules_log.append(RuleApplication(
                rule_name="convert_to_e164",
                rule_category="phone",
                description=f"Converted to E.164 format (detected country: {country_code})",
                field="phones",
                original_value=original,
                transformed_value=e164,
                stage="normalization",
            ))

        return e164

    except phonenumbers.NumberParseException as e:
        if rules_log is not None:
            rules_log.append(RuleApplication(
                rule_name="phone_parse_failed",
                rule_category="phone",
                description=f"Phone '{original}' could not be parsed: {str(e)}",
                field="phones",
                original_value=original,
                transformed_value=None,
                stage="normalization",
            ))
        logger.debug(f"Phone '{original}' parse failed: {e}")
        return None


def normalize_phones(
    phones: list[str],
    default_region: str | None = None,
    rules_log: list[RuleApplication] | None = None,
) -> tuple[list[str], int]:
    """
    Normalize and deduplicate a list of phone numbers.

    Returns:
        Tuple of (normalized_phones, duplicates_removed_count)
    """
    normalized: list[str] = []
    seen: set[str] = set()
    duplicates = 0

    for phone in phones:
        result = normalize_phone(phone, default_region, rules_log)
        if result is None:
            continue
        if result in seen:
            duplicates += 1
            if rules_log is not None:
                rules_log.append(RuleApplication(
                    rule_name="remove_duplicate_phone",
                    rule_category="phone",
                    description=f"Duplicate phone '{result}' removed",
                    field="phones",
                    original_value=result,
                    transformed_value=None,
                    stage="normalization",
                ))
            continue
        seen.add(result)
        normalized.append(result)

    return sorted(normalized), duplicates
