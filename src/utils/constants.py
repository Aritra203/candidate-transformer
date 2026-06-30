"""Constants used across the candidate transformer pipeline.

All magic values live here. Nothing is scattered across modules.
"""

from __future__ import annotations

from enum import StrEnum, unique
from typing import Final

# ---------------------------------------------------------------------------
# Source types
# ---------------------------------------------------------------------------


@unique
class SourceType(StrEnum):
    """Supported input source types."""

    CSV = "csv"
    PDF = "pdf"
    # Future: JSON = "json", DOCX = "docx", GITHUB = "github", LINKEDIN = "linkedin"


# ---------------------------------------------------------------------------
# Source priority (higher = more authoritative)
# ---------------------------------------------------------------------------

SOURCE_PRIORITY: Final[dict[SourceType, int]] = {
    SourceType.PDF: 100,  # Resume — self-reported, most authoritative
    SourceType.CSV: 80,  # Recruiter CSV — may lag or contain typos
}

# ---------------------------------------------------------------------------
# Confidence: base scores by source type
# ---------------------------------------------------------------------------

SOURCE_BASE_CONFIDENCE: Final[dict[SourceType, float]] = {
    SourceType.PDF: 0.92,
    SourceType.CSV: 0.84,
}

# ---------------------------------------------------------------------------
# Confidence: method modifiers (multiplicative)
# ---------------------------------------------------------------------------

METHOD_CONFIDENCE_MODIFIER: Final[dict[str, float]] = {
    "structured_field": 1.00,  # Direct column in CSV
    "regex": 0.95,  # Regex extraction from text
    "section_heuristic": 0.90,  # Section-header based extraction
    "fuzzy_match": 0.85,  # Fuzzy string matching
}

# ---------------------------------------------------------------------------
# Confidence: field importance weights for overall score
# ---------------------------------------------------------------------------

FIELD_IMPORTANCE_WEIGHTS: Final[dict[str, float]] = {
    "full_name": 3.0,
    "emails": 2.0,
    "phones": 2.0,
    "skills": 2.0,
    "experience": 2.0,
    "education": 1.0,
    "location": 1.0,
    "headline": 1.0,
    "years_experience": 1.0,
    "links": 0.5,
}

# ---------------------------------------------------------------------------
# Default phone region (ISO 3166 alpha-2)
# ---------------------------------------------------------------------------

DEFAULT_PHONE_REGION: Final[str] = "US"

# ---------------------------------------------------------------------------
# File extensions → source types
# ---------------------------------------------------------------------------

EXTENSION_TO_SOURCE: Final[dict[str, SourceType]] = {
    ".csv": SourceType.CSV,
    ".pdf": SourceType.PDF,
}

# ---------------------------------------------------------------------------
# Skill canonicalization map
# ---------------------------------------------------------------------------

# Keys are lowercase aliases; values are canonical names.
# This is intentionally a hardcoded dict for v1 — loading from an external
# JSON file is a trivial future extension (the architecture already supports it).
SKILL_ALIAS_MAP: Final[dict[str, str]] = {
    # JavaScript ecosystem
    "javascript": "JavaScript",
    "js": "JavaScript",
    "ecmascript": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "react js": "React",
    "angular": "Angular",
    "angularjs": "Angular",
    "angular.js": "Angular",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "express": "Express.js",
    "expressjs": "Express.js",
    "express.js": "Express.js",
    "next": "Next.js",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    # Python ecosystem
    "python": "Python",
    "python3": "Python",
    "py": "Python",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "pandas": "pandas",
    "numpy": "NumPy",
    "scipy": "SciPy",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",
    # JVM
    "java": "Java",
    "kotlin": "Kotlin",
    "spring": "Spring",
    "spring boot": "Spring Boot",
    "springboot": "Spring Boot",
    # Systems
    "c": "C",
    "c++": "C++",
    "cpp": "C++",
    "rust": "Rust",
    "go": "Go",
    "golang": "Go",
    # Data & cloud
    "sql": "SQL",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "redis": "Redis",
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "GCP",
    "google cloud": "GCP",
    "google cloud platform": "GCP",
    "azure": "Azure",
    "microsoft azure": "Azure",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    # General
    "git": "Git",
    "github": "GitHub",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "rest": "REST",
    "restful": "REST",
    "graphql": "GraphQL",
    "html": "HTML",
    "html5": "HTML",
    "css": "CSS",
    "css3": "CSS",
    "sass": "Sass",
    "scss": "Sass",
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "deep learning": "Deep Learning",
    "dl": "Deep Learning",
    "nlp": "NLP",
    "natural language processing": "NLP",
    "computer vision": "Computer Vision",
    "cv": "Computer Vision",
    "agile": "Agile",
    "scrum": "Scrum",
    "jira": "Jira",
    "linux": "Linux",
    "bash": "Bash",
    "shell": "Shell Scripting",
    "shell scripting": "Shell Scripting",
    "r": "R",
    "ruby": "Ruby",
    "rails": "Ruby on Rails",
    "ruby on rails": "Ruby on Rails",
    "php": "PHP",
    "swift": "Swift",
    "objective-c": "Objective-C",
    "objectivec": "Objective-C",
}

# ---------------------------------------------------------------------------
# CSV column name mappings (lowercase alias → canonical field)
# ---------------------------------------------------------------------------

# Recruiter CSVs arrive with inconsistent column names. This map normalizes
# common variations to canonical field paths used by the parser.
CSV_COLUMN_ALIASES: Final[dict[str, str]] = {
    # Name
    "name": "full_name",
    "full_name": "full_name",
    "full name": "full_name",
    "candidate_name": "full_name",
    "candidate name": "full_name",
    # Email
    "email": "email",
    "email_address": "email",
    "email address": "email",
    "e-mail": "email",
    # Phone
    "phone": "phone",
    "phone_number": "phone",
    "phone number": "phone",
    "mobile": "phone",
    "telephone": "phone",
    "tel": "phone",
    # Location
    "city": "city",
    "state": "region",
    "region": "region",
    "province": "region",
    "country": "country",
    "location": "location",  # May need splitting
    # Title / headline
    "title": "headline",
    "current_title": "headline",
    "current title": "headline",
    "headline": "headline",
    "job_title": "headline",
    "job title": "headline",
    "position": "headline",
    # Company
    "company": "current_company",
    "current_company": "current_company",
    "current company": "current_company",
    "employer": "current_company",
    # Experience
    "years_experience": "years_experience",
    "years experience": "years_experience",
    "years_of_experience": "years_experience",
    "experience_years": "years_experience",
    "yoe": "years_experience",
    # Skills
    "skills": "skills",
    "skill": "skills",
    "technologies": "skills",
    "tech_stack": "skills",
    "tech stack": "skills",
    # Links
    "linkedin": "linkedin",
    "linkedin_url": "linkedin",
    "linkedin url": "linkedin",
    "github": "github",
    "github_url": "github",
    "github url": "github",
    "portfolio": "portfolio",
    "website": "portfolio",
    "portfolio_url": "portfolio",
}

# ---------------------------------------------------------------------------
# PDF section header keywords
# ---------------------------------------------------------------------------

PDF_SECTION_KEYWORDS: Final[dict[str, list[str]]] = {
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "work history",
        "career history",
    ],
    "education": [
        "education",
        "academic background",
        "academic history",
        "qualifications",
    ],
    "skills": [
        "skills",
        "technical skills",
        "technologies",
        "core competencies",
        "competencies",
        "tech stack",
        "proficiencies",
    ],
    "contact": [
        "contact",
        "contact information",
        "personal information",
        "personal details",
    ],
    "summary": [
        "summary",
        "professional summary",
        "objective",
        "career objective",
        "about",
        "profile",
        "about me",
    ],
}

# ---------------------------------------------------------------------------
# Missing value behaviors
# ---------------------------------------------------------------------------


@unique
class OnMissing(StrEnum):
    """Behavior when a projected field is missing from the canonical model."""

    NULL = "null"
    OMIT = "omit"
    ERROR = "error"
