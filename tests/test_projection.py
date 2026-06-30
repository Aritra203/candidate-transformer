"""Tests for the output projection layer."""

from __future__ import annotations

from src.models.candidate import CandidateProfile, Location, Skill
from src.models.config import ProjectionConfig
from src.pipeline.projection import project


def test_projection_basic() -> None:
    profile = CandidateProfile(
        candidate_id="id123",
        full_name="Priya Sharma",
        emails=["priya@email.com"],
        location=Location(city="SF", country="US"),
        skills=[Skill(name="React", confidence=0.9, sources=["resume.pdf"])],
        overall_confidence=0.87,
    )

    config = ProjectionConfig(
        fields=[
            {"path": "name", "from": "full_name", "type": "string"},
            {"path": "primary_email", "from": "emails[0]", "type": "string"},
            {"path": "country_code", "from": "location.country", "type": "string"},
            {"path": "skill_names", "from": "skills[].name", "type": "string[]"},
        ],
        include_confidence=True,
        include_provenance=False,
        on_missing="null",
    )

    projected = project(profile, config)

    assert projected["name"] == "Priya Sharma"
    assert projected["primary_email"] == "priya@email.com"
    assert projected["country_code"] == "US"
    assert projected["skill_names"] == ["React"]
    assert projected["overall_confidence"] == 0.87
    assert "provenance" not in projected
