"""Skill canonicalization and deduplication.

Two-pass normalization:
1. **Alias map** (deterministic): exact lookup in ``SKILL_ALIAS_MAP``.
   This handles the common cases (ReactJS → React, NodeJS → Node.js).
2. **Fuzzy dedup** (fallback): uses RapidFuzz to detect near-duplicates
   that slipped through the alias map (e.g. "React Native" vs "ReactNative").

Design decisions:
- The alias map is the primary mechanism — it's deterministic and explainable.
  Fuzzy matching is only used for deduplication, not for canonicalization.
- Skills not found in the alias map are title-cased as a reasonable default,
  unless they match certain known patterns (all-caps acronyms like "AWS").
- Deduplication is case-insensitive and whitespace-insensitive.
- Empty strings and whitespace-only strings are filtered out.
"""

from __future__ import annotations

import re

from rapidfuzz import fuzz

from src.utils.constants import SKILL_ALIAS_MAP
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Threshold for fuzzy dedup — two skills are considered duplicates if their
# similarity ratio exceeds this value. Set conservatively high to avoid
# false positives (e.g. "React" vs "React Native" should NOT merge).
_FUZZY_DEDUP_THRESHOLD = 90

# Patterns that should stay uppercase (acronyms, etc.)
_ACRONYM_RE = re.compile(r"^[A-Z][A-Z0-9./+#\-]{0,10}$")


def canonicalize_skill(raw: str) -> str | None:
    """Canonicalize a single skill name.

    Args:
        raw: Raw skill string (e.g. "ReactJS", "react.js", "PYTHON").

    Returns:
        Canonical skill name, or None if the input is empty/whitespace.

    Examples:
        >>> canonicalize_skill("ReactJS")
        'React'
        >>> canonicalize_skill("node.js")
        'Node.js'
        >>> canonicalize_skill("typescript")
        'TypeScript'
        >>> canonicalize_skill("Some Unknown Skill")
        'Some Unknown Skill'
    """
    raw = raw.strip()
    if not raw:
        return None

    # Lookup in alias map (case-insensitive)
    lookup_key = raw.lower().strip()
    if lookup_key in SKILL_ALIAS_MAP:
        canonical = SKILL_ALIAS_MAP[lookup_key]
        logger.debug("Canonicalized skill: '%s' → '%s' (alias map)", raw, canonical)
        return canonical

    # Not in alias map — apply default formatting
    if _ACRONYM_RE.match(raw):
        # Looks like an acronym (AWS, SQL, CI/CD) — keep as-is
        return raw

    # Title case for multi-word skills not in the map
    # But preserve casing for known patterns like "macOS", "iOS"
    return raw.strip()


def canonicalize_skills(raw_skills: list[str]) -> list[str]:
    """Canonicalize and deduplicate a list of skills.

    Args:
        raw_skills: List of raw skill strings.

    Returns:
        Deduplicated list of canonical skill names, preserving the order
        of first appearance.
    """
    # Phase 1: Canonicalize each skill
    canonicalized: list[str] = []
    for raw in raw_skills:
        canonical = canonicalize_skill(raw)
        if canonical:
            canonicalized.append(canonical)

    # Phase 2: Exact dedup (case-insensitive)
    seen_lower: set[str] = set()
    deduped: list[str] = []
    for skill in canonicalized:
        key = skill.lower()
        if key not in seen_lower:
            seen_lower.add(key)
            deduped.append(skill)

    # Phase 3: Fuzzy dedup — remove near-duplicates
    # We iterate and check each skill against all previously accepted skills.
    # If a fuzzy match is found, we skip the duplicate (keep the first one).
    final: list[str] = []
    for skill in deduped:
        is_duplicate = False
        for accepted in final:
            similarity = fuzz.ratio(skill.lower(), accepted.lower())
            if similarity >= _FUZZY_DEDUP_THRESHOLD:
                logger.debug(
                    "Fuzzy dedup: '%s' matches '%s' (score=%d) — keeping '%s'",
                    skill,
                    accepted,
                    similarity,
                    accepted,
                )
                is_duplicate = True
                break
        if not is_duplicate:
            final.append(skill)

    return final
