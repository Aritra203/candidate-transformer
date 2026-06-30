"""Canonical candidate profile and intermediate parsed representation.

Two key models live here:

1. ``ParsedCandidate`` — the intermediate representation every parser produces.
   All fields are Optional because any source may only have partial data.
   Carries a list of ProvenanceRecord entries so downstream stages know
   where each value came from.

2. ``CandidateProfile`` — the canonical output model. Strongly typed, with
   nested sub-models for structured fields (location, links, skills,
   experience, education). This is the single source of truth that the
   projection layer reads from.

Design decisions:
- ``candidate_id`` is a deterministic SHA-256 hash of (lowercase name +
  sorted emails + sorted phones). This means the same candidate always gets
  the same ID regardless of source ordering.
- ``full_name`` is a single opaque string — we deliberately do not split
  into first/last because name parsing is culturally fraught and unreliable.
- Skills carry their own confidence and source list so the projection layer
  can filter or sort by confidence.
"""

from __future__ import annotations

import hashlib
from typing import Any

from pydantic import BaseModel, Field, model_validator

from src.models.provenance import ProvenanceRecord
from src.utils.constants import SourceType

# ---------------------------------------------------------------------------
# Nested sub-models for CandidateProfile
# ---------------------------------------------------------------------------


class Location(BaseModel):
    """Geographic location with ISO-3166 country code."""

    city: str | None = None
    region: str | None = None
    country: str | None = Field(
        default=None,
        description="ISO 3166 alpha-2 country code (e.g. 'US', 'IN').",
    )


class Links(BaseModel):
    """Web presence links."""

    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None
    other: list[str] = Field(default_factory=list)


class Skill(BaseModel):
    """A single skill with confidence and source tracking.

    Attributes:
        name: Canonical skill name (e.g. "React", not "ReactJS").
        confidence: Confidence that this candidate has this skill.
        sources: List of source files that mentioned this skill.
    """

    name: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    sources: list[str] = Field(default_factory=list)


class Experience(BaseModel):
    """A single work experience entry."""

    company: str | None = None
    title: str | None = None
    start: str | None = Field(
        default=None,
        description="Start date in YYYY-MM format.",
    )
    end: str | None = Field(
        default=None,
        description="End date in YYYY-MM format, or None if current role.",
    )
    summary: str | None = None


class Education(BaseModel):
    """A single education entry."""

    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    end_year: str | None = Field(
        default=None,
        description="Graduation year as string (e.g. '2017').",
    )


# ---------------------------------------------------------------------------
# Canonical candidate profile (output)
# ---------------------------------------------------------------------------


class CandidateProfile(BaseModel):
    """The single canonical candidate profile produced by the pipeline.

    This model is immutable after creation (frozen=True). The projection
    layer reads from it but never mutates it.

    Every field is strongly typed. The ``provenance`` list must contain at
    least one entry for every non-null field — this invariant is enforced
    by the validator stage, not here (to allow incremental construction
    during the merge phase).
    """

    model_config = {"frozen": True}

    candidate_id: str = Field(
        ...,
        description="Deterministic SHA-256 hash of (name, emails, phones).",
    )
    full_name: str | None = None
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    location: Location = Field(default_factory=Location)
    links: Links = Field(default_factory=Links)
    headline: str | None = None
    years_experience: float | None = None
    skills: list[Skill] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    provenance: list[ProvenanceRecord] = Field(default_factory=list)
    overall_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Weighted average confidence across all fields.",
    )

    @staticmethod
    def compute_candidate_id(
        name: str | None,
        emails: list[str],
        phones: list[str],
    ) -> str:
        """Compute a deterministic candidate ID.

        The hash is based on:
        - Lowercased, stripped name (or empty string if None)
        - Sorted, lowercased emails
        - Sorted phones

        This ensures the same candidate always gets the same ID regardless
        of source ordering or casing.

        Args:
            name: Full name (may be None).
            emails: List of email addresses.
            phones: List of phone numbers (ideally E.164).

        Returns:
            A hex-encoded SHA-256 hash string.
        """
        normalized_name = (name or "").strip().lower()
        sorted_emails = sorted(e.lower().strip() for e in emails)
        sorted_phones = sorted(phones)

        components = [
            normalized_name,
            "|".join(sorted_emails),
            "|".join(sorted_phones),
        ]
        raw = "||".join(components)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Intermediate parsed representation (input to normalizer/merger)
# ---------------------------------------------------------------------------


class ParsedCandidate(BaseModel):
    """Intermediate representation produced by each parser.

    All fields are Optional — any source may have only partial data.
    The ``source_type`` and ``source_file`` identify where this data
    came from, and ``provenance`` records extraction details per field.

    This model is mutable (not frozen) because the normalizer modifies
    field values in-place before handing off to the merger.
    """

    source_type: SourceType
    source_file: str

    # Identity
    full_name: str | None = None
    emails: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)

    # Location
    city: str | None = None
    region: str | None = None
    country: str | None = None

    # Links
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None
    other_links: list[str] = Field(default_factory=list)

    # Professional
    headline: str | None = None
    current_company: str | None = None
    years_experience: float | None = None
    skills: list[str] = Field(default_factory=list)

    # History
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)

    # Summary text (from PDF)
    summary: str | None = None

    # Provenance tracking — populated during parsing
    provenance: list[ProvenanceRecord] = Field(default_factory=list)

    def add_provenance(
        self,
        field: str,
        method: str,
        confidence: float,
    ) -> None:
        """Record provenance for a field extraction.

        Args:
            field: Canonical field name.
            method: Extraction method identifier.
            confidence: Confidence score in [0.0, 1.0].
        """
        self.provenance.append(
            ProvenanceRecord(
                field=field,
                source=self.source_file,
                method=method,
                confidence=confidence,
            )
        )

    @model_validator(mode="before")
    @classmethod
    def _coerce_years_experience(cls, data: Any) -> Any:
        """Attempt to coerce years_experience to float.

        Recruiter CSVs often have this as a string like '6' or '6.5'.
        We handle the conversion here at the model boundary rather than
        scattering it across parsers.
        """
        if isinstance(data, dict):
            yoe = data.get("years_experience")
            if isinstance(yoe, str):
                try:
                    data["years_experience"] = float(yoe)
                except (ValueError, TypeError):
                    data["years_experience"] = None
        return data
