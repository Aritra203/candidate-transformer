"""Tests for skill canonicalization and deduplication."""

from __future__ import annotations

from src.normalizers.skill import canonicalize_skill, canonicalize_skills


def test_canonicalize_skill() -> None:
    assert canonicalize_skill("ReactJS") == "React"
    assert canonicalize_skill("react.js") == "React"
    assert canonicalize_skill("NodeJS") == "Node.js"
    assert canonicalize_skill("typescript") == "TypeScript"
    assert canonicalize_skill("javascript") == "JavaScript"
    # Unknown skill casing preserved
    assert canonicalize_skill("UnknownSkill") == "UnknownSkill"


def test_canonicalize_skills_list() -> None:
    raw = ["ReactJS", "React", "react.js", "Python", "python", "NodeJS", "Node.js"]
    # Should deduplicate variants to canonical names
    assert canonicalize_skills(raw) == ["React", "Python", "Node.js"]
