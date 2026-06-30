"""Tests for error handling, including missing files, invalid phones, and malformed CSVs."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.parsers.csv_parser import CsvParser
from src.pipeline.detect import detect_source_type
from src.utils.exceptions import FileReadError, MalformedCSVError, SourceDetectionError


def test_missing_files() -> None:
    # CSV parser missing file
    parser = CsvParser()
    with pytest.raises(FileReadError):
        parser.parse(Path("sample_data/nonexistent.csv"))


def test_source_detection_unsupported() -> None:
    # Unsupported extension
    with pytest.raises(SourceDetectionError):
        detect_source_type(Path("sample_data/resume.txt"))


def test_malformed_csv(tmp_path: Path) -> None:
    # Create CSV with unrecognized columns
    malformed_csv = tmp_path / "malformed.csv"
    malformed_csv.write_text("random_header_1,random_header_2\nval1,val2\n", encoding="utf-8")

    parser = CsvParser()
    with pytest.raises(MalformedCSVError) as exc:
        parser.parse(malformed_csv)
    assert "has no recognizable columns" in str(exc.value)
