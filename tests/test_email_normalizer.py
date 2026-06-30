"""Tests for email validation and normalization."""

from __future__ import annotations

from src.normalizers.email import normalize_email, normalize_emails


def test_normalize_email_valid() -> None:
    assert normalize_email("  User@Example.COM  ") == "user@example.com"
    assert normalize_email("first.last+label@domain.co.uk") == "first.last+label@domain.co.uk"


def test_normalize_email_invalid() -> None:
    assert normalize_email("not-an-email") is None
    assert normalize_email("user@") is None
    assert normalize_email("@domain.com") is None


def test_normalize_emails_list() -> None:
    raw = ["  User@Example.COM  ", "invalid", "user@example.com"]
    # Should normalize, filter, and deduplicate
    assert normalize_emails(raw) == ["user@example.com"]
