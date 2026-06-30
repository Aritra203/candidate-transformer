"""Merge rules by field type.

Defines how different field types are combined when multiple sources
provide data for the same candidate. Every rule is deterministic —
given the same inputs in the same order, the output is identical.

Three rule types:
1. **Scalar**: highest-priority source wins (e.g. full_name, headline).
2. **List**: union-merge with deduplication (e.g. emails, phones).
3. **Nested list**: deduplicate by composite key, fill gaps from
   lower-priority sources (e.g. experience, education).

Design decisions:
- Rules never invent data. If no source has a value, the result is None.
- Every merge decision is recorded as a ``MergeDecision`` for the
  provenance trail.
- List merging preserves order: higher-priority values come first.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dc_field
from typing import Any


@dataclass(frozen=True)
class MergeDecision:
    """Records a single merge decision for the provenance trail.

    Attributes:
        field: Canonical field name.
        winner_source: Source file that provided the winning value.
        loser_sources: Source files whose values were overridden.
        reason: Human-readable explanation of why this value won.
    """

    field: str
    winner_source: str
    loser_sources: list[str] = dc_field(default_factory=list)
    reason: str = ""


def merge_scalar(
    field_name: str,
    values: list[tuple[str, Any, int]],
) -> tuple[Any, MergeDecision | None]:
    """Merge scalar values by priority.

    The value from the highest-priority source wins. If multiple sources
    have the same priority, the first one encountered wins (stable sort).

    Args:
        field_name: Canonical field name for provenance.
        values: List of (source_file, value, priority) tuples.
                Only non-None values should be included.

    Returns:
        Tuple of (winning_value, merge_decision). merge_decision is None
        if there was only one non-None value (no conflict to resolve).
    """
    if not values:
        return None, None

    # Sort by priority descending (stable — preserves insertion order for ties)
    sorted_values = sorted(values, key=lambda x: x[2], reverse=True)

    winner_source, winner_value, _ = sorted_values[0]

    if len(sorted_values) == 1:
        # No conflict — single source
        decision = MergeDecision(
            field=field_name,
            winner_source=winner_source,
            reason="single source",
        )
        return winner_value, decision

    # Conflict — record all losers
    loser_sources = [src for src, _, _ in sorted_values[1:]]
    decision = MergeDecision(
        field=field_name,
        winner_source=winner_source,
        loser_sources=loser_sources,
        reason=f"priority: {winner_source} > {', '.join(loser_sources)}",
    )
    return winner_value, decision


def merge_list(
    field_name: str,
    value_groups: list[tuple[str, list[str], int]],
    *,
    dedup_key: Any = None,
) -> tuple[list[str], MergeDecision | None]:
    """Union-merge list values with deduplication.

    Higher-priority values appear first. Deduplication is by the
    ``dedup_key`` function (defaults to lowercase identity).

    Args:
        field_name: Canonical field name for provenance.
        value_groups: List of (source_file, values_list, priority) tuples.
        dedup_key: Optional function to compute dedup key from a value.
                   Defaults to ``str.lower``.

    Returns:
        Tuple of (merged_list, merge_decision).
    """
    if not value_groups:
        return [], None

    key_fn = dedup_key or str.lower

    # Sort groups by priority descending
    sorted_groups = sorted(value_groups, key=lambda x: x[2], reverse=True)

    seen_keys: set[str] = set()
    merged: list[str] = []
    contributing_sources: list[str] = []

    for source, values, _ in sorted_groups:
        added_from_source = False
        for val in values:
            key = key_fn(val)
            if key not in seen_keys:
                seen_keys.add(key)
                merged.append(val)
                added_from_source = True
        if added_from_source:
            contributing_sources.append(source)

    if not merged:
        return [], None

    decision = MergeDecision(
        field=field_name,
        winner_source=contributing_sources[0] if contributing_sources else "",
        loser_sources=contributing_sources[1:],
        reason=f"union merge from {len(contributing_sources)} source(s)",
    )
    return merged, decision


def merge_nested_list(
    field_name: str,
    entry_groups: list[tuple[str, list[Any], int]],
    *,
    key_fn: Any,
    fill_fn: Any | None = None,
) -> tuple[list[Any], MergeDecision | None]:
    """Merge nested list entries (experience, education) by composite key.

    Entries from different sources with the same key are considered duplicates.
    The entry from the highest-priority source is kept. If ``fill_fn`` is
    provided, non-None fields from lower-priority duplicates are used to
    fill gaps in the winner.

    Args:
        field_name: Canonical field name for provenance.
        entry_groups: List of (source_file, entries, priority) tuples.
        key_fn: Function that extracts a dedup key from an entry.
        fill_fn: Optional function ``(winner, loser) -> merged`` that fills
                 None fields in the winner from the loser.

    Returns:
        Tuple of (merged_entries, merge_decision).
    """
    if not entry_groups:
        return [], None

    # Sort by priority descending
    sorted_groups = sorted(entry_groups, key=lambda x: x[2], reverse=True)

    seen_keys: dict[str, Any] = {}
    merged: list[Any] = []
    contributing_sources: list[str] = []

    for source, entries, _ in sorted_groups:
        added = False
        for entry in entries:
            key = key_fn(entry)
            if key not in seen_keys:
                seen_keys[key] = entry
                merged.append(entry)
                added = True
            elif fill_fn is not None:
                # Fill gaps in existing entry from this lower-priority one
                idx = merged.index(seen_keys[key])
                merged[idx] = fill_fn(seen_keys[key], entry)
                seen_keys[key] = merged[idx]
        if added:
            contributing_sources.append(source)

    if not merged:
        return [], None

    decision = MergeDecision(
        field=field_name,
        winner_source=contributing_sources[0] if contributing_sources else "",
        loser_sources=contributing_sources[1:],
        reason=f"nested merge ({len(merged)} entries from {len(contributing_sources)} source(s))",
    )
    return merged, decision
