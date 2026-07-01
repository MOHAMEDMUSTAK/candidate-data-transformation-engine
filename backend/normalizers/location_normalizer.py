from __future__ import annotations

"""
Eightfold AI - Location Normalizer

Normalizes country names to ISO-3166 Alpha-2 codes using pycountry.
Includes fuzzy matching for common abbreviations and misspellings.
"""

import logging
from typing import Any

import pycountry

from backend.models.provenance import RuleApplication

logger = logging.getLogger(__name__)

# Common country name aliases not handled by pycountry
COUNTRY_ALIASES: dict[str, str] = {
    "usa": "US",
    "us": "US",
    "u.s.": "US",
    "u.s.a.": "US",
    "united states": "US",
    "united states of america": "US",
    "america": "US",
    "uk": "GB",
    "u.k.": "GB",
    "united kingdom": "GB",
    "great britain": "GB",
    "england": "GB",
    "britain": "GB",
    "india": "IN",
    "in": "IN",
    "canada": "CA",
    "ca": "CA",
    "australia": "AU",
    "au": "AU",
    "germany": "DE",
    "de": "DE",
    "france": "FR",
    "fr": "FR",
    "japan": "JP",
    "jp": "JP",
    "china": "CN",
    "cn": "CN",
    "brazil": "BR",
    "br": "BR",
    "singapore": "SG",
    "sg": "SG",
    "uae": "AE",
    "united arab emirates": "AE",
    "netherlands": "NL",
    "holland": "NL",
    "south korea": "KR",
    "korea": "KR",
    "israel": "IL",
    "ireland": "IE",
    "new zealand": "NZ",
    "sweden": "SE",
    "switzerland": "CH",
    "spain": "ES",
    "italy": "IT",
    "russia": "RU",
    "mexico": "MX",
}


def normalize_country(
    country: str,
    rules_log: list[RuleApplication] | None = None,
) -> str | None:
    """
    Normalize a country name or code to ISO-3166 Alpha-2.

    Resolution order:
        1. Check if already a valid Alpha-2 code
        2. Check alias dictionary
        3. Try pycountry name lookup
        4. Try pycountry fuzzy search

    Returns:
        ISO-3166 Alpha-2 code or None if unresolvable.
    """
    if not country or not isinstance(country, str):
        return None

    original = country
    country = country.strip()
    if not country:
        return None

    # Step 1: Already a valid Alpha-2 code?
    if len(country) == 2:
        upper = country.upper()
        try:
            pycountry.countries.get(alpha_2=upper)
            if rules_log is not None and upper != original:
                rules_log.append(RuleApplication(
                    rule_name="country_code_uppercase",
                    rule_category="location",
                    description=f"Country code '{original}' uppercased to '{upper}'",
                    field="location.country",
                    original_value=original,
                    transformed_value=upper,
                    stage="normalization",
                ))
            return upper
        except (KeyError, LookupError):
            pass

    # Step 2: Alias dictionary
    lower = country.lower().strip()
    if lower in COUNTRY_ALIASES:
        result = COUNTRY_ALIASES[lower]
        if rules_log is not None:
            rules_log.append(RuleApplication(
                rule_name="country_alias_resolve",
                rule_category="location",
                description=f"Country '{original}' resolved to ISO-3166 '{result}' via alias",
                field="location.country",
                original_value=original,
                transformed_value=result,
                stage="normalization",
            ))
        return result

    # Step 3: pycountry name lookup
    try:
        result_country = pycountry.countries.get(name=country)
        if result_country:
            code = result_country.alpha_2
            if rules_log is not None:
                rules_log.append(RuleApplication(
                    rule_name="country_name_resolve",
                    rule_category="location",
                    description=f"Country '{original}' resolved to ISO-3166 '{code}'",
                    field="location.country",
                    original_value=original,
                    transformed_value=code,
                    stage="normalization",
                ))
            return code
    except (KeyError, LookupError):
        pass

    # Step 4: Fuzzy search
    try:
        results = pycountry.countries.search_fuzzy(country)
        if results:
            code = results[0].alpha_2
            if rules_log is not None:
                rules_log.append(RuleApplication(
                    rule_name="country_fuzzy_resolve",
                    rule_category="location",
                    description=f"Country '{original}' fuzzy-matched to ISO-3166 '{code}' ({results[0].name})",
                    field="location.country",
                    original_value=original,
                    transformed_value=code,
                    stage="normalization",
                ))
            return code
    except LookupError:
        pass

    # Unresolvable
    if rules_log is not None:
        rules_log.append(RuleApplication(
            rule_name="country_resolve_failed",
            rule_category="location",
            description=f"Country '{original}' could not be resolved to ISO-3166",
            field="location.country",
            original_value=original,
            transformed_value=None,
            stage="normalization",
        ))
    logger.debug(f"Country '{original}' could not be resolved")
    return None
