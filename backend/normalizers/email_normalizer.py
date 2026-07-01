from __future__ import annotations

"""
Eightfold AI - Email Normalizer

Normalizes email addresses: trim whitespace, lowercase, deduplicate,
and validate against RFC 5322 basic patterns.
"""

import re
import logging
from typing import Any

from backend.models.provenance import RuleApplication

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def normalize_email(email: str, rules_log: list[RuleApplication] | None = None) -> str | None:
    """
    Normalize a single email address.

    Steps:
        1. Strip whitespace
        2. Convert to lowercase
        3. Validate format

    Returns:
        Normalized email or None if invalid.
    """
    original = email
    rules: list[str] = []

    # Step 1: Trim
    email = email.strip()
    if email != original:
        rules.append("trim_whitespace")

    # Step 2: Lowercase
    lower = email.lower()
    if lower != email:
        rules.append("lowercase")
    email = lower

    # Step 3: Validate
    if not EMAIL_REGEX.match(email):
        if rules_log is not None:
            rules_log.append(RuleApplication(
                rule_name="email_validation_failed",
                rule_category="email",
                description=f"Email '{original}' failed RFC validation",
                field="emails",
                original_value=original,
                transformed_value=None,
                stage="normalization",
            ))
        logger.debug(f"Email '{original}' failed validation")
        return None

    # Log applied rules
    if rules_log is not None and rules:
        for rule_name in rules:
            rules_log.append(RuleApplication(
                rule_name=rule_name,
                rule_category="email",
                description=f"Email {rule_name.replace('_', ' ')}",
                field="emails",
                original_value=original,
                transformed_value=email,
                stage="normalization",
            ))

    return email


def normalize_emails(
    emails: list[str],
    rules_log: list[RuleApplication] | None = None,
) -> tuple[list[str], int]:
    """
    Normalize and deduplicate a list of email addresses.

    Returns:
        Tuple of (normalized_emails, duplicates_removed_count)
    """
    normalized: list[str] = []
    seen: set[str] = set()
    duplicates = 0

    for email in emails:
        result = normalize_email(email, rules_log)
        if result is None:
            continue
        if result in seen:
            duplicates += 1
            if rules_log is not None:
                rules_log.append(RuleApplication(
                    rule_name="remove_duplicate_email",
                    rule_category="email",
                    description=f"Duplicate email '{result}' removed",
                    field="emails",
                    original_value=result,
                    transformed_value=None,
                    stage="normalization",
                ))
            continue
        seen.add(result)
        normalized.append(result)

    return sorted(normalized), duplicates
