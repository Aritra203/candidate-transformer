"""Tests for date normalization."""

from __future__ import annotations

from src.normalizers.date import is_ongoing, normalize_date


def test_normalize_date_valid() -> None:
    # Standard format conversion tests
    assert normalize_date("Jan 2024") == "2024-01"
    assert normalize_date("2024/02") == "2024-02"
    assert normalize_date("03-2024") == "2024-03"
    assert normalize_date("2024") == "2024-01"  # Defaults to January


def test_normalize_date_ongoing() -> None:
    # Ongoing sentinels return None for normal date parsing
    assert normalize_date("Present") is None
    assert normalize_date("current") is None
    assert is_ongoing("Present") is True
    assert is_ongoing("Jan 2024") is False


def test_normalize_date_invalid() -> None:
    assert normalize_date("garbage") is None
    assert normalize_date("") is None
