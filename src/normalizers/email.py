"""Email validation and normalization.

Uses ``email-validator`` for RFC 5322 validation. Emails that fail
validation are returned as None — we never emit a syntactically
invalid email address.

Design decisions:
- Lowercase and strip before validation (email local parts are
  case-insensitive in practice, even though RFC 5322 allows case).
- ``check_deliverability=False`` — we don't do DNS lookups during
  normalization. Deliverability checks are slow, network-dependent,
  and outside the scope of a data transformer.
- Deduplication is by the normalized (lowercase, stripped) form.
"""

from __future__ import annotations

from email_validator import EmailNotValidError, validate_email

from src.utils.logging import get_logger

logger = get_logger(__name__)


def normalize_email(raw: str) -> str | None:
    """Normalize and validate a single email address.

    Args:
        raw: Raw email string.

    Returns:
        Normalized email (lowercase, stripped) if valid, None otherwise.

    Examples:
        >>> normalize_email("  User@Example.COM  ")
        'user@example.com'
        >>> normalize_email("not-an-email")
        None
    """
    raw = raw.strip().lower()
    if not raw:
        return None

    try:
        result = validate_email(raw, check_deliverability=False)
        normalized = result.normalized.lower()
        logger.debug("Validated email: '%s' → '%s'", raw, normalized)
        return normalized
    except EmailNotValidError as exc:
        logger.debug("Invalid email '%s': %s", raw, exc)
        return None


def normalize_emails(raw_emails: list[str]) -> list[str]:
    """Normalize a list of emails, filtering out invalid ones.

    Args:
        raw_emails: List of raw email strings.

    Returns:
        Deduplicated list of valid, normalized email addresses.
    """
    seen: set[str] = set()
    result: list[str] = []

    for raw in raw_emails:
        normalized = normalize_email(raw)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)

    return result
