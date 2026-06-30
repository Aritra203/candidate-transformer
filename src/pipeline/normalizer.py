"""Normalizer orchestrator.

Applies all field-level normalizers to a ``ParsedCandidate``, transforming
raw extracted values into their canonical forms. This is a pure data
transformation — no I/O, no side effects beyond logging.

The orchestrator modifies the ``ParsedCandidate`` in place and returns it.
This is intentional: the ParsedCandidate is a mutable intermediate
representation that will be consumed by the merger. Creating copies would
be wasteful since each candidate is processed exactly once.

Order of normalization does not matter — each normalizer operates on
independent fields. We normalize in a fixed order for determinism.
"""

from __future__ import annotations

from src.models.candidate import Experience, ParsedCandidate
from src.normalizers.date import is_ongoing, normalize_date
from src.normalizers.email import normalize_emails
from src.normalizers.location import normalize_city, normalize_country, normalize_region
from src.normalizers.phone import normalize_phones
from src.normalizers.skill import canonicalize_skills
from src.utils.logging import get_logger

logger = get_logger(__name__)


def normalize_candidate(candidate: ParsedCandidate) -> ParsedCandidate:
    """Apply all normalizations to a parsed candidate.

    Modifies the candidate in place and returns it for chaining.

    Args:
        candidate: A parsed candidate with raw extracted values.

    Returns:
        The same candidate instance with normalized values.
    """
    source = candidate.source_file
    logger.debug("Normalizing candidate from '%s'", source)

    # --- Emails ---
    if candidate.emails:
        original_count = len(candidate.emails)
        candidate.emails = normalize_emails(candidate.emails)
        logger.debug(
            "Emails: %d raw → %d normalized",
            original_count,
            len(candidate.emails),
        )

    # --- Phones ---
    if candidate.phones:
        original_count = len(candidate.phones)
        candidate.phones = normalize_phones(candidate.phones)
        logger.debug(
            "Phones: %d raw → %d normalized",
            original_count,
            len(candidate.phones),
        )

    # --- Location ---
    candidate.city = normalize_city(candidate.city)
    candidate.region = normalize_region(candidate.region)
    if candidate.country:
        candidate.country = normalize_country(candidate.country)

    # --- Skills ---
    if candidate.skills:
        original_count = len(candidate.skills)
        candidate.skills = canonicalize_skills(candidate.skills)
        logger.debug(
            "Skills: %d raw → %d normalized",
            original_count,
            len(candidate.skills),
        )

    # --- Experience dates ---
    for exp in candidate.experience:
        _normalize_experience_dates(exp)

    # --- Name cleanup ---
    if candidate.full_name:
        # Normalize casing: "PRIYA SHARMA" → "Priya Sharma"
        name = candidate.full_name.strip()
        if name.isupper() or name.islower():
            candidate.full_name = name.title()
        else:
            candidate.full_name = name

    logger.debug("Normalization complete for '%s'", source)
    return candidate


def _normalize_experience_dates(exp: Experience) -> None:
    """Normalize start/end dates on an experience entry.

    Modifies the Experience object in place.

    Args:
        exp: An experience entry with raw date strings.
    """
    if exp.start:
        normalized = normalize_date(exp.start)
        if normalized:
            # Use model_copy since Experience fields can be set directly
            # Actually Experience is not frozen, but we use object.__setattr__
            # for Pydantic models
            object.__setattr__(exp, "start", normalized)

    if exp.end:
        if is_ongoing(exp.end):
            object.__setattr__(exp, "end", None)
        else:
            normalized = normalize_date(exp.end)
            if normalized:
                object.__setattr__(exp, "end", normalized)
