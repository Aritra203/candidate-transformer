"""Confidence engine — scores every field and computes overall confidence.

The confidence engine runs after merging, enriching the frozen
``CandidateProfile`` with per-field confidence scores (via provenance
records) and a weighted overall confidence.

Scoring model (documented in DESIGN.md):

    field_confidence = source_base × method_modifier

    overall_confidence = Σ(field_confidence × field_weight) / Σ(field_weight)

    where sums are over non-null fields only.

Design decisions:
- Confidence is derived purely from source type and extraction method —
  these are objective, deterministic signals. We do not use heuristics
  like "string length" or "looks reasonable" because those are subjective
  and hard to explain.
- Multi-source corroboration boosts confidence: if N sources agree on a
  field value, confidence = max(individual confidences) + 0.03 × (N-1),
  capped at 1.0. This reflects the intuition that independent confirmation
  increases trustworthiness.
- The overall score is a weighted average, not a simple mean. Weights
  reflect field importance for downstream hiring decisions (name and
  contact info matter more than headline).
- CandidateProfile is frozen, so we return a new instance with the
  updated overall_confidence.
"""

from __future__ import annotations

from src.models.candidate import CandidateProfile
from src.models.provenance import ProvenanceRecord
from src.utils.constants import FIELD_IMPORTANCE_WEIGHTS
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Corroboration bonus per additional source agreeing on a field
_CORROBORATION_BONUS_PER_SOURCE = 0.03


def compute_confidence(profile: CandidateProfile) -> CandidateProfile:
    """Compute per-field and overall confidence for a merged profile.

    Per-field confidence is already stored in the provenance records
    (set by parsers at extraction time). This function:
    1. Aggregates per-field confidence from provenance records.
    2. Applies multi-source corroboration bonuses.
    3. Computes the weighted overall confidence.
    4. Returns a new CandidateProfile with updated overall_confidence.

    Args:
        profile: A merged CandidateProfile (overall_confidence may be 0.0).

    Returns:
        A new CandidateProfile with overall_confidence computed.
    """
    field_scores = _aggregate_field_confidence(profile.provenance)

    # Filter to fields that are actually non-null in the profile
    active_fields = _get_active_fields(profile)
    active_scores: dict[str, float] = {}
    for field_name in active_fields:
        # Look for exact match or parent match (e.g. "location" matches "location.city")
        best_score = 0.0
        for prov_field, score in field_scores.items():
            if prov_field == field_name or prov_field.startswith(f"{field_name}.") or field_name.startswith(f"{prov_field}."):
                best_score = max(best_score, score)
        if best_score > 0:
            active_scores[field_name] = best_score

    # Compute weighted average
    overall = _weighted_average(active_scores)

    logger.info(
        "Confidence computed: overall=%.4f, fields scored: %s",
        overall,
        {k: round(v, 4) for k, v in active_scores.items()},
    )

    # Return new frozen instance with updated confidence
    return profile.model_copy(update={"overall_confidence": round(overall, 4)})


def _aggregate_field_confidence(
    provenance: list[ProvenanceRecord],
) -> dict[str, float]:
    """Aggregate confidence per field from provenance records.

    For each field:
    - Base confidence = max confidence across all provenance records.
    - Corroboration bonus = 0.03 × (number_of_unique_sources - 1).
    - Final = min(base + bonus, 1.0).

    Args:
        provenance: List of provenance records.

    Returns:
        Dict mapping field name → aggregated confidence score.
    """
    # Group provenance by field
    field_provenance: dict[str, list[ProvenanceRecord]] = {}
    for record in provenance:
        # Normalize to top-level field for aggregation
        top_field = record.field.split(".")[0]
        if top_field not in field_provenance:
            field_provenance[top_field] = []
        field_provenance[top_field].append(record)

    field_scores: dict[str, float] = {}
    for field_name, records in field_provenance.items():
        # Max confidence across records
        max_conf = max(r.confidence for r in records)

        # Count unique sources
        unique_sources = len(set(r.source for r in records))

        # Apply corroboration bonus
        bonus = _CORROBORATION_BONUS_PER_SOURCE * max(unique_sources - 1, 0)
        final = min(max_conf + bonus, 1.0)

        field_scores[field_name] = final
        logger.debug(
            "Field '%s': max_conf=%.4f, sources=%d, bonus=%.4f, final=%.4f",
            field_name,
            max_conf,
            unique_sources,
            bonus,
            final,
        )

    return field_scores


def _get_active_fields(profile: CandidateProfile) -> list[str]:
    """Determine which top-level fields are non-null/non-empty.

    Args:
        profile: The candidate profile to inspect.

    Returns:
        List of field names that have non-null, non-empty values.
    """
    active: list[str] = []

    if profile.full_name:
        active.append("full_name")
    if profile.emails:
        active.append("emails")
    if profile.phones:
        active.append("phones")
    if profile.location.city or profile.location.region or profile.location.country:
        active.append("location")
    if profile.links.linkedin or profile.links.github or profile.links.portfolio:
        active.append("links")
    if profile.headline:
        active.append("headline")
    if profile.years_experience is not None:
        active.append("years_experience")
    if profile.skills:
        active.append("skills")
    if profile.experience:
        active.append("experience")
    if profile.education:
        active.append("education")

    return active


def _weighted_average(field_scores: dict[str, float]) -> float:
    """Compute weighted average confidence.

    Weights come from ``FIELD_IMPORTANCE_WEIGHTS``. Fields not in the
    weight table get a default weight of 1.0.

    Args:
        field_scores: Dict mapping field name → confidence score.

    Returns:
        Weighted average confidence, or 0.0 if no fields scored.
    """
    if not field_scores:
        return 0.0

    total_weighted = 0.0
    total_weight = 0.0

    for field_name, score in field_scores.items():
        weight = FIELD_IMPORTANCE_WEIGHTS.get(field_name, 1.0)
        total_weighted += score * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    return total_weighted / total_weight
