"""Tests for phone normalization.

Verifies valid formatting (E164) and invalid phone handling.
"""

from __future__ import annotations

from src.normalizers.phone import normalize_phone, normalize_phones


def test_normalize_phone_valid() -> None:
    # US local format
    assert normalize_phone("(415) 555-1234") == "+14155551234"
    # International formats
    assert normalize_phone("+44 20 7946 0958") == "+442079460958"
    assert normalize_phone("+91 98765 43210") == "+919876543210"
    # Already normalized
    assert normalize_phone("+14155551234") == "+14155551234"


def test_normalize_phone_invalid() -> None:
    # Too short / long / words
    assert normalize_phone("123") is None
    assert normalize_phone("not a number") is None
    assert normalize_phone("1234567890123456") is None  # Too long


def test_normalize_phones_list() -> None:
    raw = ["(415) 555-1234", "invalid", "+1 415 555 1234"]
    # Should clean, filter invalid, and deduplicate
    assert normalize_phones(raw) == ["+14155551234"]
