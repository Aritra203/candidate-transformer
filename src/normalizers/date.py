"""Date normalization to YYYY-MM format.

Handles a wide variety of date formats commonly found in resumes and
recruiter data. Uses ``python-dateutil`` for flexible parsing.

Design decisions:
- Output format is always YYYY-MM (no day component — resumes rarely
  specify exact days, and adding a synthetic day would be inventing data).
- ``dayfirst=False`` — American date convention (month before day) since
  most recruiter data is US-centric. This is a documented assumption.
- Unparseable dates return None — we never guess.
- "Present", "Current", "Now" are returned as-is (they're not dates,
  they're sentinels for "ongoing").
"""

from __future__ import annotations

import re

from dateutil import parser as dateutil_parser

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Sentinel values that mean "ongoing" — not actual dates
_ONGOING_SENTINELS = {"present", "current", "now", "ongoing"}


def normalize_date(raw: str) -> str | None:
    """Normalize a date string to YYYY-MM format.

    Args:
        raw: Raw date string (e.g. "Jan 2024", "2024/01", "01-2024",
             "January 2024", "2024").

    Returns:
        Date string in YYYY-MM format, or None if unparseable.
        Returns None for ongoing sentinels (caller should handle separately).

    Examples:
        >>> normalize_date("Jan 2024")
        '2024-01'
        >>> normalize_date("2024/01")
        '2024-01'
        >>> normalize_date("01-2024")
        '2024-01'
        >>> normalize_date("Present")
        None
        >>> normalize_date("garbage")
        None
    """
    raw = raw.strip()
    if not raw:
        return None

    # Check for ongoing sentinels
    if raw.lower() in _ONGOING_SENTINELS:
        return None

    # Handle year-only input (e.g. "2024") — emit as YYYY-01
    # This is a pragmatic choice: a bare year means "sometime in that year",
    # and January is the least-wrong default.
    if re.match(r"^\d{4}$", raw):
        return f"{raw}-01"

    # Handle MM-YYYY and MM/YYYY patterns explicitly, because dateutil
    # can misparse these (it may interpret the month as a day).
    mm_yyyy = re.match(r"^(\d{1,2})[/\-](\d{4})$", raw)
    if mm_yyyy:
        month = int(mm_yyyy.group(1))
        year = int(mm_yyyy.group(2))
        if 1 <= month <= 12 and 1900 <= year <= 2100:
            return f"{year:04d}-{month:02d}"

    # Handle YYYY/MM and YYYY-MM patterns
    yyyy_mm = re.match(r"^(\d{4})[/\-](\d{1,2})$", raw)
    if yyyy_mm:
        year = int(yyyy_mm.group(1))
        month = int(yyyy_mm.group(2))
        if 1 <= month <= 12 and 1900 <= year <= 2100:
            return f"{year:04d}-{month:02d}"

    # Fall back to dateutil for fuzzy parsing
    try:
        parsed = dateutil_parser.parse(raw, fuzzy=True, dayfirst=False)
        result = f"{parsed.year:04d}-{parsed.month:02d}"
        logger.debug("Normalized date: '%s' → '%s'", raw, result)
        return result
    except (ValueError, OverflowError):
        logger.debug("Cannot parse date: '%s'", raw)
        return None


def is_ongoing(raw: str) -> bool:
    """Check if a date string represents an ongoing/current position.

    Args:
        raw: Raw date string.

    Returns:
        True if the string is a sentinel for "ongoing".
    """
    return raw.strip().lower() in _ONGOING_SENTINELS
