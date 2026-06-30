"""Tests for config validation and loader."""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from src.models.config import ProjectionConfig
from src.pipeline.validator import validate_config
from src.utils.exceptions import ConfigurationError


def test_config_validation_valid() -> None:
    config = ProjectionConfig(
        fields=[
            {"path": "name", "from": "full_name", "type": "string"},
            {"path": "email", "from": "emails[0]", "type": "string"},
        ],
        include_confidence=True,
        include_provenance=True,
    )
    # Should run without error
    validate_config(config)


def test_config_validation_duplicate_paths() -> None:
    # Duplicate path check
    with pytest.raises(PydanticValidationError):
        ProjectionConfig(
            fields=[
                {"path": "name", "from": "full_name", "type": "string"},
                {"path": "name", "from": "first_name", "type": "string"},
            ]
        )


def test_config_validation_invalid_path_syntax() -> None:
    config = ProjectionConfig(
        fields=[
            {"path": "name", "from": "invalid[path]syntax", "type": "string"},
        ]
    )
    with pytest.raises(ConfigurationError) as exc:
        validate_config(config)
    assert "Invalid source path syntax" in str(exc.value)
