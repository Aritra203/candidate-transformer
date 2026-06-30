"""Location normalization — country names/codes to ISO 3166 alpha-2.

Uses ``pycountry`` for standard lookups and includes a manual alias
map for common abbreviations and informal names that pycountry doesn't
handle (e.g. "US", "USA", "United States" all → "US").

Design decisions:
- We normalize country only, not city or region. City/region normalization
  is a much harder problem (requires a geocoding API or a large gazetteer)
  and is intentionally out of scope.
- City and region are cleaned (trimmed, title-cased) but not validated.
- Unknown countries return None — we never guess.
- Common US state abbreviations in the region field are preserved as-is
  (they're already in a standard form).
"""

from __future__ import annotations

import pycountry

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Manual alias map for country names/codes that pycountry doesn't resolve.
# Keys are lowercase.
_COUNTRY_ALIASES: dict[str, str] = {
    "us": "US",
    "usa": "US",
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
    "scotland": "GB",
    "wales": "GB",
    "northern ireland": "GB",
    "india": "IN",
    "canada": "CA",
    "australia": "AU",
    "germany": "DE",
    "france": "FR",
    "japan": "JP",
    "china": "CN",
    "brazil": "BR",
    "south korea": "KR",
    "korea": "KR",
    "singapore": "SG",
    "israel": "IL",
    "ireland": "IE",
    "netherlands": "NL",
    "holland": "NL",
    "spain": "ES",
    "italy": "IT",
    "sweden": "SE",
    "switzerland": "CH",
    "norway": "NO",
    "denmark": "DK",
    "finland": "FI",
    "new zealand": "NZ",
    "uae": "AE",
    "united arab emirates": "AE",
    "russia": "RU",
    "mexico": "MX",
    "indonesia": "ID",
    "philippines": "PH",
    "taiwan": "TW",
    "poland": "PL",
    "portugal": "PT",
    "belgium": "BE",
    "austria": "AT",
    "czech republic": "CZ",
    "czechia": "CZ",
}


def normalize_country(raw: str) -> str | None:
    """Normalize a country name or code to ISO 3166 alpha-2.

    Args:
        raw: Raw country string (e.g. "United States", "US", "USA", "India").

    Returns:
        ISO 3166 alpha-2 code (e.g. "US", "IN"), or None if unrecognized.

    Examples:
        >>> normalize_country("United States")
        'US'
        >>> normalize_country("IN")
        'IN'
        >>> normalize_country("USA")
        'US'
        >>> normalize_country("unknown place")
        None
    """
    raw = raw.strip()
    if not raw:
        return None

    lookup = raw.lower().strip()

    # 1. Check manual alias map first (fast, handles common cases)
    if lookup in _COUNTRY_ALIASES:
        result = _COUNTRY_ALIASES[lookup]
        logger.debug("Normalized country: '%s' → '%s' (alias map)", raw, result)
        return result

    # 2. Try pycountry alpha-2 lookup (already a valid code?)
    if len(raw) == 2 and raw.isalpha():
        country = pycountry.countries.get(alpha_2=raw.upper())
        if country:
            logger.debug("Normalized country: '%s' → '%s' (alpha-2)", raw, country.alpha_2)
            return country.alpha_2

    # 3. Try pycountry alpha-3 lookup
    if len(raw) == 3 and raw.isalpha():
        country = pycountry.countries.get(alpha_3=raw.upper())
        if country:
            logger.debug("Normalized country: '%s' → '%s' (alpha-3)", raw, country.alpha_2)
            return country.alpha_2

    # 4. Try pycountry name lookup
    country = pycountry.countries.get(name=raw)
    if country:
        logger.debug("Normalized country: '%s' → '%s' (name)", raw, country.alpha_2)
        return country.alpha_2

    # 5. Try pycountry fuzzy search
    try:
        results = pycountry.countries.search_fuzzy(raw)
        if results:
            logger.debug("Normalized country: '%s' → '%s' (fuzzy)", raw, results[0].alpha_2)
            return results[0].alpha_2
    except LookupError:
        pass

    logger.debug("Cannot normalize country: '%s'", raw)
    return None


def normalize_city(raw: str | None) -> str | None:
    """Clean a city name (trim, title-case).

    No validation — city names are too diverse for a simple normalizer.

    Args:
        raw: Raw city string.

    Returns:
        Cleaned city string, or None if empty.
    """
    if not raw:
        return None
    cleaned = raw.strip()
    if not cleaned:
        return None
    # Title-case, but handle edge cases like "San Francisco" correctly
    return cleaned.title() if cleaned.upper() == cleaned or cleaned.lower() == cleaned else cleaned


def normalize_region(raw: str | None) -> str | None:
    """Clean a region/state name (trim).

    US state abbreviations are kept as-is (already standard).

    Args:
        raw: Raw region string.

    Returns:
        Cleaned region string, or None if empty.
    """
    if not raw:
        return None
    cleaned = raw.strip()
    return cleaned if cleaned else None
