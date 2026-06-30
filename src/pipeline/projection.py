"""Projection layer — reshapes the canonical profile per runtime config.

This is the most important architectural boundary in the system: the
canonical ``CandidateProfile`` is never mutated. Instead, the projection
layer reads from it and constructs a new dict matching the config's
requested shape.

Supported path syntax in ``from`` fields:
- Simple:      ``full_name``          → profile.full_name
- Dot:         ``location.country``   → profile.location.country
- Index:       ``emails[0]``          → profile.emails[0]
- Pluck:       ``skills[].name``      → [s.name for s in profile.skills]

Design decisions:
- Path resolution is implemented as a recursive descent over the model's
  dict representation. This avoids coupling to Pydantic internals and
  makes the logic testable with plain dicts.
- Missing values follow the ``on_missing`` config: null, omit, or error.
  This is applied per-field, not globally per-record — so one missing
  optional field doesn't blow up the whole projection.
- Per-field normalization (``E164``, ``canonical``) re-applies normalizers
  to the already-normalized value. This is idempotent by design.
- The projection produces a plain dict, not a Pydantic model — the output
  shape is dynamic and defined by the config, not by a static schema.
"""

from __future__ import annotations

import re
from typing import Any

from src.models.candidate import CandidateProfile
from src.models.config import ProjectionConfig
from src.normalizers.phone import normalize_phone
from src.normalizers.skill import canonicalize_skill
from src.utils.constants import OnMissing
from src.utils.exceptions import ProjectionError
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Regex for array index: "emails[0]", "skills[2]"
_INDEX_RE = re.compile(r"^(.+?)\[(\d+)\]$")

# Regex for array pluck: "skills[].name"
_PLUCK_RE = re.compile(r"^(.+?)\[\]\.(.+)$")


def project(
    profile: CandidateProfile,
    config: ProjectionConfig,
) -> dict[str, Any]:
    """Project a canonical profile into the shape defined by config.

    Args:
        profile: The frozen canonical candidate profile.
        config: Runtime projection configuration.

    Returns:
        A plain dict matching the config's requested shape.

    Raises:
        ProjectionError: If a required field is missing and on_missing="error",
                         or if a path cannot be resolved.
    """
    # Convert profile to a nested dict for uniform path resolution
    profile_dict = profile.model_dump(mode="python")

    result: dict[str, Any] = {}

    for field_config in config.fields:
        value = _resolve_path(profile_dict, field_config.source_path)

        # Apply per-field normalization if requested
        if value is not None and field_config.normalize:
            value = _apply_field_normalization(value, field_config.normalize)

        # Handle missing values
        if value is None:
            if field_config.required and config.on_missing == OnMissing.ERROR:
                raise ProjectionError(
                    f"Required field '{field_config.path}' is missing "
                    f"(source path: '{field_config.source_path}')"
                )
            if config.on_missing == OnMissing.OMIT and not field_config.required:
                logger.debug(
                    "Omitting missing field '%s' (on_missing=omit)",
                    field_config.path,
                )
                continue
            # on_missing=null or required field: include as null
            result[field_config.path] = None
        else:
            result[field_config.path] = value

    # Add confidence if configured
    if config.include_confidence:
        result["overall_confidence"] = profile.overall_confidence

    # Add provenance if configured
    if config.include_provenance:
        result["provenance"] = [record.model_dump(mode="python") for record in profile.provenance]

    logger.debug(
        "Projected %d fields from canonical profile",
        len(result),
    )
    return result


def _resolve_path(data: dict[str, Any], path: str) -> Any:
    """Resolve a dotted/indexed path against a nested dict.

    Supports:
    - ``"full_name"``         → data["full_name"]
    - ``"location.country"``  → data["location"]["country"]
    - ``"emails[0]"``         → data["emails"][0]
    - ``"skills[].name"``     → [item["name"] for item in data["skills"]]

    Args:
        data: Nested dict (from model_dump).
        path: Path string to resolve.

    Returns:
        The resolved value, or None if any step in the path is missing.
    """
    # Check for array pluck pattern: "skills[].name"
    pluck_match = _PLUCK_RE.match(path)
    if pluck_match:
        array_path = pluck_match.group(1)
        item_field = pluck_match.group(2)
        array_val = _resolve_path(data, array_path)
        if array_val is None or not isinstance(array_val, list):
            return None
        return [
            (
                _resolve_path(item, item_field)
                if isinstance(item, dict)
                else getattr(item, item_field, None)
            )
            for item in array_val
        ]

    # Check for array index pattern: "emails[0]"
    index_match = _INDEX_RE.match(path)
    if index_match:
        array_path = index_match.group(1)
        index = int(index_match.group(2))
        array_val = _resolve_path(data, array_path)
        if array_val is None or not isinstance(array_val, list):
            return None
        if index >= len(array_val):
            return None
        return array_val[index]

    # Dot-notation resolution
    parts = path.split(".")
    current: Any = data
    for part in parts:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            return None

    # Treat empty strings and empty lists as None for missing-value purposes
    if current == "" or current == []:
        return None

    return current


def _apply_field_normalization(value: Any, normalize: str) -> Any:
    """Apply per-field normalization to an already-resolved value.

    Args:
        value: The resolved field value.
        normalize: Normalization directive ("E164" or "canonical").

    Returns:
        The normalized value.
    """
    if normalize == "E164":
        if isinstance(value, str):
            return normalize_phone(value) or value
        if isinstance(value, list):
            return [normalize_phone(v) or v if isinstance(v, str) else v for v in value]

    elif normalize == "canonical":
        if isinstance(value, str):
            return canonicalize_skill(value) or value
        if isinstance(value, list):
            return [canonicalize_skill(v) or v if isinstance(v, str) else v for v in value]

    return value
