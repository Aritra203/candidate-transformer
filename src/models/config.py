"""Configuration models for the projection layer.

The projection config is a JSON file that drives how the canonical
CandidateProfile is reshaped into the final output. It supports:

- Selecting a subset of fields
- Renaming/remapping fields via ``from`` (dot-notation + array indexing)
- Per-field normalization directives
- Toggling provenance and confidence in output
- Configurable missing-value behavior (null, omit, error)

Design decision: config validation is strict — unknown fields, invalid
paths, and type mismatches all fail fast at startup, not at runtime.
This is intentional: a bad config should never silently produce wrong output.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from src.utils.constants import OnMissing


class FieldProjection(BaseModel):
    """Configuration for a single projected output field.

    Attributes:
        path: The output field name in the projected JSON.
        from_path: Source path in the canonical model. If None, defaults
                   to ``path``. Supports dot-notation (``location.country``)
                   and array indexing (``emails[0]``, ``skills[].name``).
        type: Expected output type for validation.
        normalize: Optional normalization to apply (e.g. "E164", "canonical").
        required: If True, the field must be non-null in output.
    """

    path: str = Field(
        ...,
        description="Output field name in the projected JSON.",
    )
    from_path: str | None = Field(
        default=None,
        alias="from",
        description="Source path in canonical model (dot-notation, array indexing).",
    )
    type: Literal["string", "string[]", "number", "object", "object[]"] | None = None
    normalize: Literal["E164", "canonical"] | None = None
    required: bool = False

    model_config = {"populate_by_name": True}

    @property
    def source_path(self) -> str:
        """Resolve the actual source path in the canonical model.

        Falls back to ``path`` if ``from_path`` is not set.
        """
        return self.from_path if self.from_path is not None else self.path


class ProjectionConfig(BaseModel):
    """Runtime configuration for the projection layer.

    Loaded from a JSON file at startup and validated before the pipeline
    runs. Invalid configs fail fast with clear error messages.

    Attributes:
        fields: List of field projections defining output shape.
        include_confidence: Whether to include ``overall_confidence`` in output.
        include_provenance: Whether to include ``provenance`` list in output.
        on_missing: Behavior when a projected field is missing from canonical.
    """

    fields: list[FieldProjection] = Field(
        ...,
        min_length=1,
        description="At least one field projection is required.",
    )
    include_confidence: bool = Field(
        default=True,
        description="Include overall_confidence in output.",
    )
    include_provenance: bool = Field(
        default=True,
        description="Include provenance records in output.",
    )
    on_missing: OnMissing = Field(
        default=OnMissing.NULL,
        description="Behavior for missing values: 'null', 'omit', or 'error'.",
    )

    @model_validator(mode="after")
    def _validate_no_duplicate_paths(self) -> ProjectionConfig:
        """Ensure no two field projections have the same output path."""
        paths = [f.path for f in self.fields]
        duplicates = [p for p in paths if paths.count(p) > 1]
        if duplicates:
            raise ValueError(f"Duplicate output paths in projection config: {set(duplicates)}")
        return self
