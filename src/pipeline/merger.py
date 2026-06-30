"""Merge orchestrator.

Thin orchestration layer that groups ``ParsedCandidate`` objects by
identity, then delegates to the conflict resolver for actual merging.

Identity matching uses two signals:
1. **Email overlap**: if two candidates share any email, they're the same person.
2. **Name similarity**: if two candidates have the same normalized name
   (case-insensitive, trimmed), they're likely the same person.

For v1, we merge ALL candidates into a single profile (the assignment
specifies that all input files describe one candidate). The identity-matching
logic is here for architectural completeness — it will be needed when
processing batch CSVs with multiple candidates.
"""

from __future__ import annotations

from src.merge.resolver import resolve
from src.models.candidate import CandidateProfile, ParsedCandidate
from src.utils.logging import get_logger

logger = get_logger(__name__)


def merge_candidates(candidates: list[ParsedCandidate]) -> list[CandidateProfile]:
    """Merge a list of parsed candidates into canonical profiles.

    Groups candidates by identity, then merges each group into a single
    CandidateProfile.

    Args:
        candidates: List of normalized ParsedCandidate instances.

    Returns:
        List of merged CandidateProfile instances (one per unique candidate).
    """
    if not candidates:
        logger.warning("No candidates to merge")
        return []

    # Group by identity
    groups = _group_by_identity(candidates)
    logger.info(
        "Grouped %d parsed candidates into %d unique identities",
        len(candidates),
        len(groups),
    )

    # Merge each group
    profiles: list[CandidateProfile] = []
    for group in groups:
        profile = resolve(group)
        profiles.append(profile)

    return profiles


def _group_by_identity(
    candidates: list[ParsedCandidate],
) -> list[list[ParsedCandidate]]:
    """Group candidates that represent the same person.

    Uses email overlap and name matching as identity signals.

    Args:
        candidates: List of parsed candidates.

    Returns:
        List of groups, where each group contains candidates for one person.
    """
    # Union-Find approach for grouping
    n = len(candidates)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    # Build email → candidate index mapping
    email_index: dict[str, int] = {}
    for i, c in enumerate(candidates):
        for email in c.emails:
            key = email.lower().strip()
            if key in email_index:
                union(i, email_index[key])
            else:
                email_index[key] = i

    # Match by name (case-insensitive)
    name_index: dict[str, int] = {}
    for i, c in enumerate(candidates):
        if c.full_name:
            key = c.full_name.strip().lower()
            if key in name_index:
                union(i, name_index[key])
            else:
                name_index[key] = i

    # Collect groups
    groups_map: dict[int, list[int]] = {}
    for i in range(n):
        root = find(i)
        if root not in groups_map:
            groups_map[root] = []
        groups_map[root].append(i)

    return [[candidates[i] for i in indices] for indices in groups_map.values()]
