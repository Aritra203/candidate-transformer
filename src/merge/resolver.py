"""Conflict resolver — applies merge rules to produce a unified profile.

This module is the bridge between raw merge rules and the final
``CandidateProfile``. It takes a list of normalized ``ParsedCandidate``
objects, applies the appropriate merge rule to each field, collects
all provenance records and merge decisions, and constructs the
immutable canonical profile.

Design decisions:
- Candidates are sorted by source priority before merging (deterministic).
- Skill merging produces ``Skill`` objects with confidence and source lists
  by aggregating across all sources that mentioned each skill.
- Experience/education dedup uses a composite key (company+title+start
  for experience, institution+degree for education).
- The ``fill_experience`` / ``fill_education`` helpers allow lower-priority
  sources to fill in missing fields on an entry (e.g. CSV has company
  name but not summary; resume has both).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.merge.rules import MergeDecision, merge_list, merge_nested_list, merge_scalar
from src.models.candidate import (
    CandidateProfile,
    Education,
    Experience,
    Links,
    Location,
    ParsedCandidate,
    Skill,
)
from src.models.provenance import ProvenanceRecord
from src.utils.constants import SOURCE_PRIORITY
from src.utils.logging import get_logger

logger = get_logger(__name__)


def resolve(candidates: list[ParsedCandidate]) -> CandidateProfile:
    """Merge multiple parsed candidates into a single canonical profile.

    Args:
        candidates: List of normalized ParsedCandidate instances,
                    potentially from different sources.

    Returns:
        A frozen CandidateProfile with all fields merged, provenance
        tracked, and candidate_id computed.
    """
    if not candidates:
        return CandidateProfile(candidate_id=CandidateProfile.compute_candidate_id(None, [], []))

    # Sort by priority for deterministic processing
    sorted_candidates = sorted(
        candidates,
        key=lambda c: SOURCE_PRIORITY.get(c.source_type, 0),
        reverse=True,
    )

    all_provenance: list[ProvenanceRecord] = []
    merge_decisions: list[MergeDecision] = []

    # Collect all provenance from individual parsers
    for c in sorted_candidates:
        all_provenance.extend(c.provenance)

    # --- Scalar fields ---
    full_name, name_decision = _merge_scalar_field(
        "full_name", sorted_candidates, lambda c: c.full_name
    )
    if name_decision:
        merge_decisions.append(name_decision)

    headline, headline_decision = _merge_scalar_field(
        "headline", sorted_candidates, lambda c: c.headline
    )
    if headline_decision:
        merge_decisions.append(headline_decision)

    years_exp, yoe_decision = _merge_scalar_field(
        "years_experience", sorted_candidates, lambda c: c.years_experience
    )
    if yoe_decision:
        merge_decisions.append(yoe_decision)

    # --- List fields ---
    emails, email_decision = _merge_list_field("emails", sorted_candidates, lambda c: c.emails)
    if email_decision:
        merge_decisions.append(email_decision)

    phones, phone_decision = _merge_list_field("phones", sorted_candidates, lambda c: c.phones)
    if phone_decision:
        merge_decisions.append(phone_decision)

    # --- Skills (special handling — need to build Skill objects) ---
    skills = _merge_skills(sorted_candidates)

    # --- Location (merge each sub-field independently) ---
    city, _ = _merge_scalar_field("location.city", sorted_candidates, lambda c: c.city)
    region, _ = _merge_scalar_field("location.region", sorted_candidates, lambda c: c.region)
    country, _ = _merge_scalar_field("location.country", sorted_candidates, lambda c: c.country)

    location = Location(city=city, region=region, country=country)

    # --- Links ---
    linkedin, _ = _merge_scalar_field("links.linkedin", sorted_candidates, lambda c: c.linkedin)
    github, _ = _merge_scalar_field("links.github", sorted_candidates, lambda c: c.github)
    portfolio, _ = _merge_scalar_field("links.portfolio", sorted_candidates, lambda c: c.portfolio)
    other_links, _ = _merge_list_field("links.other", sorted_candidates, lambda c: c.other_links)

    links = Links(
        linkedin=linkedin,
        github=github,
        portfolio=portfolio,
        other=other_links,
    )

    # --- Experience ---
    experience = _merge_experience(sorted_candidates)

    # --- Education ---
    education = _merge_education(sorted_candidates)

    # --- Compute candidate ID ---
    candidate_id = CandidateProfile.compute_candidate_id(full_name, emails, phones)

    # --- Log merge summary ---
    logger.info(
        "Merged %d sources → candidate_id=%s..., name=%s, "
        "emails=%d, phones=%d, skills=%d, exp=%d, edu=%d",
        len(candidates),
        candidate_id[:12],
        full_name or "(none)",
        len(emails),
        len(phones),
        len(skills),
        len(experience),
        len(education),
    )

    return CandidateProfile(
        candidate_id=candidate_id,
        full_name=full_name,
        emails=emails,
        phones=phones,
        location=location,
        links=links,
        headline=headline,
        years_experience=years_exp,
        skills=skills,
        experience=experience,
        education=education,
        provenance=all_provenance,
        overall_confidence=0.0,  # Filled by confidence engine
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _merge_scalar_field(
    field_name: str,
    candidates: list[ParsedCandidate],
    extractor: Callable[[ParsedCandidate], Any],
) -> tuple[Any, MergeDecision | None]:
    """Extract and merge a scalar field from all candidates."""
    values = []
    for c in candidates:
        val = extractor(c)
        if val is not None:
            priority = SOURCE_PRIORITY.get(c.source_type, 0)
            values.append((c.source_file, val, priority))

    return merge_scalar(field_name, values)


def _merge_list_field(
    field_name: str,
    candidates: list[ParsedCandidate],
    extractor: Callable[[ParsedCandidate], Any],
) -> tuple[list[str], MergeDecision | None]:
    """Extract and merge a list field from all candidates."""
    groups = []
    for c in candidates:
        vals = extractor(c)
        if vals:
            priority = SOURCE_PRIORITY.get(c.source_type, 0)
            groups.append((c.source_file, vals, priority))

    return merge_list(field_name, groups)


def _merge_skills(candidates: list[ParsedCandidate]) -> list[Skill]:
    """Merge skills from all candidates into Skill objects.

    Each unique skill (by canonical name) becomes one Skill object
    with confidence derived from how many sources mentioned it, and
    a list of source files.
    """
    skill_sources: dict[str, list[str]] = {}  # canonical_name → [sources]
    skill_confidences: dict[str, list[float]] = {}

    for c in candidates:
        # Find skill-related provenance for this source
        skill_prov = [p for p in c.provenance if p.field == "skills"]
        base_conf = skill_prov[0].confidence if skill_prov else 0.8

        for skill_name in c.skills:
            key = skill_name.lower()
            if key not in skill_sources:
                skill_sources[key] = []
                skill_confidences[key] = []
            if c.source_file not in skill_sources[key]:
                skill_sources[key].append(c.source_file)
                skill_confidences[key].append(base_conf)

    skills: list[Skill] = []
    # Process in deterministic order (sorted by canonical key)
    for key in sorted(skill_sources.keys()):
        sources = skill_sources[key]
        confidences = skill_confidences[key]

        # Find the canonical name from the highest-priority source
        canonical_name = key  # fallback
        for c in candidates:
            for s in c.skills:
                if s.lower() == key:
                    canonical_name = s
                    break
            if canonical_name != key:
                break

        # Confidence: average across sources, boosted slightly for multi-source
        avg_conf = sum(confidences) / len(confidences)
        multi_source_boost = min(0.05 * (len(sources) - 1), 0.10)
        final_conf = min(avg_conf + multi_source_boost, 1.0)

        skills.append(
            Skill(
                name=canonical_name,
                confidence=round(final_conf, 4),
                sources=sources,
            )
        )

    return skills


def _experience_key(exp: Experience) -> str:
    """Compute a dedup key for experience entries."""
    parts = [
        (exp.company or "").lower().strip(),
        (exp.title or "").lower().strip(),
    ]
    return "|".join(parts)


def _fill_experience(winner: Experience, loser: Experience) -> Experience:
    """Fill None fields in winner from loser."""
    return Experience(
        company=winner.company or loser.company,
        title=winner.title or loser.title,
        start=winner.start or loser.start,
        end=winner.end or loser.end,
        summary=winner.summary or loser.summary,
    )


def _merge_experience(candidates: list[ParsedCandidate]) -> list[Experience]:
    """Merge experience entries across sources."""
    groups = []
    for c in candidates:
        if c.experience:
            priority = SOURCE_PRIORITY.get(c.source_type, 0)
            groups.append((c.source_file, c.experience, priority))

    if not groups:
        return []

    merged, _ = merge_nested_list(
        "experience",
        groups,
        key_fn=_experience_key,
        fill_fn=_fill_experience,
    )
    return merged


def _education_key(edu: Education) -> str:
    """Compute a dedup key for education entries."""
    parts = [
        (edu.institution or "").lower().strip(),
        (edu.degree or "").lower().strip(),
    ]
    return "|".join(parts)


def _fill_education(winner: Education, loser: Education) -> Education:
    """Fill None fields in winner from loser."""
    return Education(
        institution=winner.institution or loser.institution,
        degree=winner.degree or loser.degree,
        field=winner.field or loser.field,
        end_year=winner.end_year or loser.end_year,
    )


def _merge_education(candidates: list[ParsedCandidate]) -> list[Education]:
    """Merge education entries across sources."""
    groups = []
    for c in candidates:
        if c.education:
            priority = SOURCE_PRIORITY.get(c.source_type, 0)
            groups.append((c.source_file, c.education, priority))

    if not groups:
        return []

    merged, _ = merge_nested_list(
        "education",
        groups,
        key_fn=_education_key,
        fill_fn=_fill_education,
    )
    return merged
