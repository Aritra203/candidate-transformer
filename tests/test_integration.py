"""End-to-end integration tests for candidate transformer pipeline."""

from __future__ import annotations

from pathlib import Path

from src.pipeline.pipeline import CandidateTransformerPipeline
from src.pipeline.validator import load_and_validate_config


def test_pipeline_integration_end_to_end() -> None:
    csv_path = Path("sample_data/candidate.csv")
    pdf_path = Path("sample_data/resume.pdf")
    config_path = Path("config/default.json")

    assert csv_path.exists()
    assert pdf_path.exists()
    assert config_path.exists()

    # Load default configuration
    config = load_and_validate_config(config_path)

    # Execute pipeline orchestrator
    pipeline = CandidateTransformerPipeline()
    results = pipeline.run([csv_path, pdf_path], config)

    # Assert outputs
    assert len(results) == 1
    candidate = results[0]

    # Verify canonical shape & normalizations
    assert candidate["full_name"] == "Priya Sharma"
    # Deduplicated emails list
    assert "priya.sharma@email.com" in candidate["emails"]
    assert "p.sharma@company.org" in candidate["emails"]
    # Phone E.164 normalization
    assert candidate["phones"] == ["+14155551234"]
    # ISO country code normalization
    assert candidate["location"]["country"] == "US"
    assert candidate["location"]["city"] == "San Francisco"
    # Unified skills (ReactJS / react.js -> React)
    skills = [s["name"] for s in candidate["skills"]]
    assert "React" in skills
    assert "Python" in skills
    # Metadata presence
    assert candidate["overall_confidence"] > 0.8
    assert len(candidate["provenance"]) > 0
