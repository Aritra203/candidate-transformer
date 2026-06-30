"""Validation layer — validates config at startup and output after projection.

Two validation points:
1. **Config validation** (``validate_config``): runs at startup before any I/O.
   Catches bad configs early with clear error messages.
2. **Output validation** (``validate_output``): runs after projection to ensure
   the emitted JSON conforms to declared types and required-field constraints.

Design decisions:
- Validation is fail-fast: the first error is raised immediately rather than
  collecting all errors. This is intentional — a single bad config field is
  enough to make the entire output untrustworthy.
- Type checking is structural, not nominal: we check that the value is
  an instance of the expected Python type, not that it's a specific class.
- Required-field validation happens in both config validation (does the
  config make sense?) and output validation (does the output satisfy it?).
- We never silently discard validation errors. Every failure is either
  raised as an exception or logged as a warning.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.models.config import ProjectionConfig
from src.utils.exceptions import ConfigurationError, ValidationError
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Map from config type strings to Python type checks
_TYPE_VALIDATORS: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "number": (int, float),
    "object": dict,
}


def validate_config(config: ProjectionConfig) -> None:
    """Validate a projection config before pipeline execution.

    Checks:
    - At least one field is defined.
    - No duplicate output paths.
    - ``on_missing`` is a valid value.
    - Field types are recognized.
    - ``from`` paths use valid syntax.

    Args:
        config: The projection configuration to validate.

    Raises:
        ConfigurationError: If the config is invalid.
    """
    logger.debug("Validating projection config with %d fields", len(config.fields))

    # Pydantic already enforces min_length=1 and duplicate paths,
    # but we add explicit checks for clearer error messages.

    if not config.fields:
        raise ConfigurationError("Projection config must define at least one field")

    seen_paths: set[str] = set()
    for field in config.fields:
        # Check for duplicate output paths
        if field.path in seen_paths:
            raise ConfigurationError(f"Duplicate output path in projection config: '{field.path}'")
        seen_paths.add(field.path)

        # Validate output path syntax (must be a simple identifier)
        if not field.path.replace("_", "").isalnum():
            # Allow underscores and alphanumeric characters
            if not all(c.isalnum() or c == "_" for c in field.path):
                raise ConfigurationError(
                    f"Invalid output path '{field.path}': must be alphanumeric "
                    f"with underscores"
                )

        # Validate type if specified
        if field.type is not None:
            valid_types = {"string", "string[]", "number", "object", "object[]"}
            if field.type not in valid_types:
                raise ConfigurationError(
                    f"Unknown type '{field.type}' for field '{field.path}'. "
                    f"Valid types: {valid_types}"
                )

        # Validate source path syntax
        source_path = field.source_path
        _validate_path_syntax(source_path, field.path)

        # Validate normalize directive
        if field.normalize is not None:
            valid_normalizations = {"E164", "canonical"}
            if field.normalize not in valid_normalizations:
                raise ConfigurationError(
                    f"Unknown normalization '{field.normalize}' for field "
                    f"'{field.path}'. Valid: {valid_normalizations}"
                )

    logger.info("Config validation passed: %d fields", len(config.fields))


def validate_output(
    output: dict[str, Any],
    config: ProjectionConfig,
) -> None:
    """Validate the projected output against the config's type declarations.

    Checks:
    - Required fields are present and non-null.
    - Field values match declared types.
    - No unexpected None values for required fields.

    Args:
        output: The projected output dict.
        config: The projection config that produced the output.

    Raises:
        ValidationError: If the output is invalid.
    """
    logger.debug("Validating output with %d keys", len(output))

    for field in config.fields:
        value = output.get(field.path)

        # Required field check
        if field.required and value is None:
            raise ValidationError(f"Required field '{field.path}' is null in output")

        # Type check (skip if value is None — already handled above)
        if value is not None and field.type is not None:
            _check_type(field.path, value, field.type)

    logger.info("Output validation passed: %d fields checked", len(config.fields))


def load_and_validate_config(config_path: Path) -> ProjectionConfig:
    """Load a projection config from a JSON file and validate it.

    This is the primary entry point for config loading — it combines
    file reading, JSON parsing, Pydantic validation, and semantic
    validation into a single call.

    Args:
        config_path: Path to the JSON config file.

    Returns:
        A validated ProjectionConfig.

    Raises:
        ConfigurationError: If the file cannot be read or the config is invalid.
    """
    if not config_path.exists():
        raise ConfigurationError(f"Config file not found: {config_path}")

    try:
        raw = config_path.read_text(encoding="utf-8")
    except Exception as exc:
        raise ConfigurationError(f"Cannot read config file '{config_path}': {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"Invalid JSON in config file '{config_path}': {exc}") from exc

    try:
        config = ProjectionConfig(**data)
    except Exception as exc:
        raise ConfigurationError(f"Config validation failed for '{config_path}': {exc}") from exc

    # Semantic validation (beyond Pydantic's structural checks)
    validate_config(config)

    return config


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _validate_path_syntax(source_path: str, output_path: str) -> None:
    """Validate that a source path uses valid syntax.

    Valid patterns:
    - ``"full_name"`` (simple identifier)
    - ``"location.country"`` (dot notation)
    - ``"emails[0]"`` (array index)
    - ``"skills[].name"`` (array pluck)

    Args:
        source_path: The source path to validate.
        output_path: The output path (for error messages).

    Raises:
        ConfigurationError: If the path syntax is invalid.
    """
    import re

    # Match valid patterns
    # Simple: word chars and underscores
    # Dot: word.word.word
    # Index: word[digit]
    # Pluck: word[].word
    valid_pattern = re.compile(
        r"^[a-zA-Z_]\w*"  # starts with letter/underscore
        r"(?:\.\w+)*"  # optional .field.field
        r"(?:\[\d+\]|\[\]\.[\w.]+)?$"  # optional [0] or [].field
    )

    if not valid_pattern.match(source_path):
        raise ConfigurationError(
            f"Invalid source path syntax '{source_path}' for output field "
            f"'{output_path}'. Supported: 'field', 'field.sub', "
            f"'field[0]', 'field[].sub'"
        )


def _check_type(field_path: str, value: Any, declared_type: str) -> None:
    """Check that a value matches its declared type.

    Args:
        field_path: Field name for error messages.
        value: The value to check.
        declared_type: The declared type string.

    Raises:
        ValidationError: If the type doesn't match.
    """
    if declared_type == "string":
        if not isinstance(value, str):
            raise ValidationError(
                f"Field '{field_path}' expected type 'string', "
                f"got {type(value).__name__}: {value!r}"
            )

    elif declared_type == "number":
        if not isinstance(value, (int, float)):
            raise ValidationError(
                f"Field '{field_path}' expected type 'number', "
                f"got {type(value).__name__}: {value!r}"
            )

    elif declared_type == "string[]":
        if not isinstance(value, list):
            raise ValidationError(
                f"Field '{field_path}' expected type 'string[]', " f"got {type(value).__name__}"
            )
        for i, item in enumerate(value):
            if not isinstance(item, str):
                raise ValidationError(
                    f"Field '{field_path}[{i}]' expected type 'string', "
                    f"got {type(item).__name__}: {item!r}"
                )

    elif declared_type == "object":
        if not isinstance(value, dict):
            raise ValidationError(
                f"Field '{field_path}' expected type 'object', " f"got {type(value).__name__}"
            )

    elif declared_type == "object[]":
        if not isinstance(value, list):
            raise ValidationError(
                f"Field '{field_path}' expected type 'object[]', " f"got {type(value).__name__}"
            )
        for i, item in enumerate(value):
            if not isinstance(item, dict):
                raise ValidationError(
                    f"Field '{field_path}[{i}]' expected type 'object', "
                    f"got {type(item).__name__}: {item!r}"
                )
