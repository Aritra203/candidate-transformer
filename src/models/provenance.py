"""Provenance tracking models.

Every value in the final candidate profile must be traceable to a source file,
extraction method, and confidence score. ProvenanceRecord is the atomic unit
of this audit trail.

Design decision: ProvenanceRecord is frozen (immutable) because provenance
is write-once — once a fact about extraction is recorded, it never changes.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProvenanceRecord(BaseModel):
    """Records where a single field value came from.

    Attributes:
        field: Canonical field name (e.g. "emails", "phones", "full_name").
        source: Filename or identifier of the input source (e.g. "resume.pdf").
        method: How the value was extracted (e.g. "structured_field", "regex",
                "section_heuristic", "regex+phonenumbers").
        confidence: Confidence score for this extraction, in [0.0, 1.0].
    """

    model_config = {"frozen": True}

    field: str = Field(
        ...,
        description="Canonical field name this provenance record applies to.",
    )
    source: str = Field(
        ...,
        description="Source filename or identifier (e.g. 'resume.pdf').",
    )
    method: str = Field(
        ...,
        description="Extraction method used (e.g. 'structured_field', 'regex').",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score in [0.0, 1.0].",
    )
