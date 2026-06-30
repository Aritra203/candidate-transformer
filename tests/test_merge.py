"""Tests for merge engine and conflict resolution."""

from __future__ import annotations

from src.merge.resolver import resolve
from src.models.candidate import Experience, ParsedCandidate
from src.utils.constants import SourceType


def test_merge_priority_conflict() -> None:
    # PDF (priority 100) should win over CSV (priority 80) for scalar fields
    c_csv = ParsedCandidate(
        source_type=SourceType.CSV,
        source_file="recruiter.csv",
        full_name="Priya Sharma (CSV)",
        headline="Software Engineer",
    )
    c_csv.add_provenance("full_name", "structured_field", 0.84)
    c_csv.add_provenance("headline", "structured_field", 0.84)

    c_pdf = ParsedCandidate(
        source_type=SourceType.PDF,
        source_file="resume.pdf",
        full_name="Priya Sharma",
        headline="Senior Software Engineer",
    )
    c_pdf.add_provenance("full_name", "section_heuristic", 0.828)
    c_pdf.add_provenance("headline", "section_heuristic", 0.828)

    merged = resolve([c_csv, c_pdf])

    # PDF values should win
    assert merged.full_name == "Priya Sharma"
    assert merged.headline == "Senior Software Engineer"


def test_merge_nested_list_gap_fill() -> None:
    # Lower priority sources should fill in missing experience fields in duplicates
    c_csv = ParsedCandidate(
        source_type=SourceType.CSV,
        source_file="recruiter.csv",
        experience=[Experience(company="Stripe", title="Senior Engineer", summary="CSV Summary")],
    )
    c_csv.add_provenance("experience", "structured_field", 0.84)

    c_pdf = ParsedCandidate(
        source_type=SourceType.PDF,
        source_file="resume.pdf",
        experience=[Experience(company="Stripe", title="Senior Engineer", start="2021-01")],
    )
    c_pdf.add_provenance("experience", "section_heuristic", 0.828)

    merged = resolve([c_csv, c_pdf])

    # Should merge company, title, start, and fill summary from CSV
    assert len(merged.experience) == 1
    exp = merged.experience[0]
    assert exp.company == "Stripe"
    assert exp.title == "Senior Engineer"
    assert exp.start == "2021-01"
    assert exp.summary == "CSV Summary"
