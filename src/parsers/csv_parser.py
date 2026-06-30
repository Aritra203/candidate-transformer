"""CSV parser using Polars.

Reads recruiter CSV exports and converts each row into a ``ParsedCandidate``.
Handles column name variations via the alias map in ``constants.py``.

Design decisions:
- Uses Polars over pandas for type safety, speed, and no implicit type coercion.
- Column names are lowercased and matched against ``CSV_COLUMN_ALIASES``.
- Empty strings and whitespace-only values are treated as None (never garbage).
- Skills columns are split by comma.
- Every extracted field records provenance with method="structured_field".
- Malformed rows are logged and skipped — they never crash the pipeline.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from src.models.candidate import ParsedCandidate
from src.utils.constants import (
    CSV_COLUMN_ALIASES,
    SOURCE_BASE_CONFIDENCE,
    SourceType,
)
from src.utils.exceptions import FileReadError, MalformedCSVError
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Confidence for structured CSV fields = base × method modifier (1.00)
_CSV_CONFIDENCE = SOURCE_BASE_CONFIDENCE[SourceType.CSV] * 1.00


def _clean_value(value: object) -> str | None:
    """Convert a cell value to a cleaned string, or None if empty.

    Args:
        value: Raw cell value from Polars.

    Returns:
        Stripped string, or None if the value is null/empty/whitespace.
    """
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


class CsvParser:
    """Parses recruiter CSV exports into ``ParsedCandidate`` instances.

    Each row in the CSV produces one ``ParsedCandidate``. Column names are
    normalized via ``CSV_COLUMN_ALIASES`` to handle common variations
    (e.g. "Email Address" → "email", "Phone Number" → "phone").
    """

    def parse(self, file_path: Path) -> list[ParsedCandidate]:
        """Parse a CSV file and return one ParsedCandidate per row.

        Args:
            file_path: Path to the CSV file.

        Returns:
            List of parsed candidates. Empty list if file has no data rows.

        Raises:
            FileReadError: If the file cannot be read.
            MalformedCSVError: If the CSV has no usable columns.
        """
        if not file_path.exists():
            raise FileReadError(f"CSV file not found: {file_path}")

        try:
            df = pl.read_csv(file_path, infer_schema_length=0, truncate_ragged_lines=True)
        except Exception as exc:
            raise FileReadError(f"Failed to read CSV '{file_path}': {exc}") from exc

        if df.is_empty():
            logger.warning("CSV file '%s' contains no data rows", file_path)
            return []

        # Normalize column names and map to canonical fields
        column_map = self._build_column_map(df.columns)
        if not column_map:
            raise MalformedCSVError(
                f"CSV '{file_path}' has no recognizable columns. " f"Found: {df.columns}"
            )

        logger.info(
            "Parsing CSV '%s': %d rows, %d mapped columns",
            file_path.name,
            len(df),
            len(column_map),
        )

        source_name = file_path.name
        candidates: list[ParsedCandidate] = []

        for row_idx in range(len(df)):
            try:
                candidate = self._parse_row(df, row_idx, column_map, source_name)
                candidates.append(candidate)
            except Exception:
                logger.warning(
                    "Skipping malformed row %d in '%s'",
                    row_idx + 1,
                    file_path.name,
                    exc_info=True,
                )

        logger.info(
            "CSV '%s': extracted %d candidates from %d rows",
            file_path.name,
            len(candidates),
            len(df),
        )
        return candidates

    def _build_column_map(self, columns: list[str]) -> dict[str, str]:
        """Map raw CSV column names to canonical field names.

        Args:
            columns: Raw column names from the CSV header.

        Returns:
            Dict mapping raw column name → canonical field name.
        """
        column_map: dict[str, str] = {}
        for col in columns:
            normalized = col.strip().lower()
            if normalized in CSV_COLUMN_ALIASES:
                canonical = CSV_COLUMN_ALIASES[normalized]
                column_map[col] = canonical
                logger.debug("Mapped column '%s' → '%s'", col, canonical)
            else:
                logger.debug("Unrecognized column '%s' — skipping", col)
        return column_map

    def _parse_row(
        self,
        df: pl.DataFrame,
        row_idx: int,
        column_map: dict[str, str],
        source_name: str,
    ) -> ParsedCandidate:
        """Extract a single ParsedCandidate from one CSV row.

        Args:
            df: The Polars DataFrame.
            row_idx: Zero-based row index.
            column_map: Mapping of raw column names → canonical field names.
            source_name: Source file name for provenance.

        Returns:
            A populated ParsedCandidate.
        """
        # Build a dict of canonical_field → cleaned_value for this row
        row_data: dict[str, str | None] = {}
        for raw_col, canonical_field in column_map.items():
            value = df[raw_col][row_idx]
            row_data[canonical_field] = _clean_value(value)

        candidate = ParsedCandidate(
            source_type=SourceType.CSV,
            source_file=source_name,
        )

        # --- Identity ---
        if row_data.get("full_name"):
            candidate.full_name = row_data["full_name"]
            candidate.add_provenance("full_name", "structured_field", _CSV_CONFIDENCE)

        email = row_data.get("email")
        if email:
            candidate.emails = [email]
            candidate.add_provenance("emails", "structured_field", _CSV_CONFIDENCE)

        phone = row_data.get("phone")
        if phone:
            candidate.phones = [phone]
            candidate.add_provenance("phones", "structured_field", _CSV_CONFIDENCE)

        # --- Location ---
        if row_data.get("city"):
            candidate.city = row_data["city"]
            candidate.add_provenance("location.city", "structured_field", _CSV_CONFIDENCE)

        if row_data.get("region"):
            candidate.region = row_data["region"]
            candidate.add_provenance("location.region", "structured_field", _CSV_CONFIDENCE)

        if row_data.get("country"):
            candidate.country = row_data["country"]
            candidate.add_provenance("location.country", "structured_field", _CSV_CONFIDENCE)

        # Handle combined "location" column (e.g. "San Francisco, CA")
        if row_data.get("location") and not row_data.get("city"):
            parts = [p.strip() for p in row_data["location"].split(",")]  # type: ignore[union-attr]
            if len(parts) >= 1:
                candidate.city = parts[0]
                candidate.add_provenance("location.city", "structured_field", _CSV_CONFIDENCE)
            if len(parts) >= 2:
                candidate.region = parts[1]
                candidate.add_provenance("location.region", "structured_field", _CSV_CONFIDENCE)
            if len(parts) >= 3:
                candidate.country = parts[2]
                candidate.add_provenance("location.country", "structured_field", _CSV_CONFIDENCE)

        # --- Links ---
        if row_data.get("linkedin"):
            candidate.linkedin = row_data["linkedin"]
            candidate.add_provenance("links.linkedin", "structured_field", _CSV_CONFIDENCE)

        if row_data.get("github"):
            candidate.github = row_data["github"]
            candidate.add_provenance("links.github", "structured_field", _CSV_CONFIDENCE)

        if row_data.get("portfolio"):
            candidate.portfolio = row_data["portfolio"]
            candidate.add_provenance("links.portfolio", "structured_field", _CSV_CONFIDENCE)

        # --- Professional ---
        if row_data.get("headline"):
            candidate.headline = row_data["headline"]
            candidate.add_provenance("headline", "structured_field", _CSV_CONFIDENCE)

        if row_data.get("current_company"):
            candidate.current_company = row_data["current_company"]
            candidate.add_provenance("current_company", "structured_field", _CSV_CONFIDENCE)

        if row_data.get("years_experience"):
            try:
                candidate.years_experience = float(row_data["years_experience"])  # type: ignore[arg-type]
                candidate.add_provenance("years_experience", "structured_field", _CSV_CONFIDENCE)
            except (ValueError, TypeError):
                logger.warning(
                    "Cannot parse years_experience '%s' in row %d",
                    row_data["years_experience"],
                    row_idx + 1,
                )

        # --- Skills (comma-separated) ---
        if row_data.get("skills"):
            raw_skills = [s.strip() for s in row_data["skills"].split(",") if s.strip()]  # type: ignore[union-attr]
            if raw_skills:
                candidate.skills = raw_skills
                candidate.add_provenance("skills", "structured_field", _CSV_CONFIDENCE)

        return candidate
