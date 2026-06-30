"""Phone number normalization to E.164 format.

Uses the ``phonenumbers`` library for parsing and validation. Numbers
that cannot be parsed or validated are returned as None — we never emit
a garbage phone number.

Design decisions:
- Default region is US (configurable via DEFAULT_PHONE_REGION constant).
- We attempt parsing with the default region first. If that fails, we try
  without a region (for numbers with explicit country codes).
- Only numbers that pass ``is_valid_number()`` are emitted. This rejects
  numbers with wrong digit counts or invalid area codes.
- The E.164 format is canonical: "+14155551234" (no spaces, dashes, parens).
"""

from __future__ import annotations

import phonenumbers

from src.utils.constants import DEFAULT_PHONE_REGION
from src.utils.logging import get_logger

logger = get_logger(__name__)


def normalize_phone(raw: str, default_region: str = DEFAULT_PHONE_REGION) -> str | None:
    """Normalize a phone number string to E.164 format.

    Args:
        raw: Raw phone number string (e.g. "(415) 555-1234", "+1-415-555-1234").
        default_region: ISO 3166 alpha-2 country code for numbers without
                        an explicit country code. Defaults to "US".

    Returns:
        E.164 formatted string (e.g. "+14155551234"), or None if the
        number cannot be parsed or is invalid.

    Examples:
        >>> normalize_phone("(415) 555-1234")
        '+14155551234'
        >>> normalize_phone("+44 20 7946 0958", "GB")
        '+442079460958'
        >>> normalize_phone("not a number")
        None
    """
    raw = raw.strip()
    if not raw:
        return None

    # Try parsing with default region
    try:
        parsed = phonenumbers.parse(raw, default_region)
    except phonenumbers.NumberParseException:
        # Try without region (may work if number has country code)
        try:
            parsed = phonenumbers.parse(raw, None)
        except phonenumbers.NumberParseException:
            logger.debug("Cannot parse phone number: '%s'", raw)
            return None

    if not phonenumbers.is_valid_number(parsed):
        logger.debug(
            "Phone number parsed but invalid: '%s' → %s",
            raw,
            phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
        )
        return None

    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    logger.debug("Normalized phone: '%s' → '%s'", raw, e164)
    return e164


def normalize_phones(raw_phones: list[str]) -> list[str]:
    """Normalize a list of phone numbers, filtering out invalid ones.

    Args:
        raw_phones: List of raw phone number strings.

    Returns:
        Deduplicated list of valid E.164 phone numbers.
    """
    seen: set[str] = set()
    result: list[str] = []

    for raw in raw_phones:
        normalized = normalize_phone(raw)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)

    return result
