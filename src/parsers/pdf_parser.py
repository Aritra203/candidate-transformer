"""PDF resume parser using pdfplumber.

Extracts candidate information from resume PDFs using a combination of
regex patterns and section-header heuristics. This is a deterministic,
rule-based parser — no ML/NLP involved.

Design decisions:
- Name extraction: first non-empty line that isn't an email/phone/URL.
  This is a heuristic that works for most standard resume formats.
- Section detection: lines matching section keywords (EXPERIENCE, EDUCATION,
  etc.) are treated as section boundaries. Content between boundaries
  belongs to that section.
- Emails, phones, and URLs are extracted globally (not section-bound)
  because they may appear anywhere in the document.
- Experience entries are detected by lines matching "Title | Company | Date"
  patterns, with bullet points collected as summaries.
- Education entries look for institution names followed by degree/year info.
- All extraction records provenance with method="regex" or "section_heuristic".

Limitations (intentional):
- Two-column layouts may interleave text — pdfplumber extracts left-to-right.
- Decorative elements (icons, images) are ignored.
- Non-English resumes are not explicitly handled.
"""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from src.models.candidate import Education, Experience, ParsedCandidate
from src.utils.constants import (
    METHOD_CONFIDENCE_MODIFIER,
    PDF_SECTION_KEYWORDS,
    SOURCE_BASE_CONFIDENCE,
    SourceType,
)
from src.utils.exceptions import FileReadError
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Confidence calculations
_PDF_BASE = SOURCE_BASE_CONFIDENCE[SourceType.PDF]
_REGEX_CONFIDENCE = _PDF_BASE * METHOD_CONFIDENCE_MODIFIER["regex"]
_SECTION_CONFIDENCE = _PDF_BASE * METHOD_CONFIDENCE_MODIFIER["section_heuristic"]

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Email: standard RFC-5322-ish pattern (intentionally permissive — validation
# happens in the normalizer, not here).
_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
)

# Phone: matches common US/international formats.
# Examples: +1 (415) 555-1234, (415) 555-1234, 415-555-1234, +14155551234
_PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s.-]?)?"  # Optional country code
    r"(?:\(?\d{2,4}\)?[\s.-]?)?"  # Optional area code
    r"\d{3,4}"  # First group
    r"[\s.-]?"  # Separator
    r"\d{3,4}"  # Second group
    r"(?:[\s.-]?\d{1,4})?",  # Optional extension
)

# URL patterns
_LINKEDIN_RE = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+/?",
    re.IGNORECASE,
)
_GITHUB_RE = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/[\w\-]+/?",
    re.IGNORECASE,
)
_URL_RE = re.compile(
    r"https?://[^\s,;|]+",
    re.IGNORECASE,
)

# Experience line pattern: "Title | Company | Date Range" or similar
_EXPERIENCE_LINE_RE = re.compile(
    r"^(.+?)\s*[|•·–—]\s*(.+?)\s*[|•·–—]\s*(.+)$",
)

# Date range pattern: "Jan 2021 - Present", "03/2019 - 12/2020", etc.
_DATE_RANGE_RE = re.compile(
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}"
    r"|(?:\d{1,2}[/\-]\d{4})"
    r"|(?:\d{4}[/\-]\d{1,2})"
    r"|(?:\d{4}))"
    r"\s*[-–—to]+\s*"
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}"
    r"|(?:\d{1,2}[/\-]\d{4})"
    r"|(?:\d{4}[/\-]\d{1,2})"
    r"|(?:\d{4})"
    r"|[Pp]resent|[Cc]urrent|[Nn]ow)",
    re.IGNORECASE,
)

# Year pattern for education
_YEAR_RE = re.compile(r"\b((?:19|20)\d{2})\b")

# Lines that are clearly not a person's name
_NOT_NAME_RE = re.compile(
    r"(?:@|https?://|www\.|\.com|\.org|\.edu|resume|curriculum|vitae|page \d)",
    re.IGNORECASE,
)


class PdfParser:
    """Parses resume PDFs into a single ``ParsedCandidate``.

    Extraction strategy:
    1. Extract full text from all pages.
    2. Extract emails, phones, and URLs globally via regex.
    3. Identify section boundaries via keyword matching.
    4. Parse each section with section-specific logic.
    5. Extract name from the first non-trivial line.
    """

    def parse(self, file_path: Path) -> list[ParsedCandidate]:
        """Parse a PDF resume file.

        Args:
            file_path: Path to the PDF file.

        Returns:
            A list containing exactly one ParsedCandidate, or empty list
            if the PDF contains no extractable text.

        Raises:
            FileReadError: If the file cannot be read.
        """
        if not file_path.exists():
            raise FileReadError(f"PDF file not found: {file_path}")

        try:
            text = self._extract_text(file_path)
        except Exception as exc:
            raise FileReadError(f"Failed to read PDF '{file_path}': {exc}") from exc

        if not text or not text.strip():
            logger.warning("PDF '%s' contains no extractable text", file_path.name)
            return []

        source_name = file_path.name
        candidate = ParsedCandidate(
            source_type=SourceType.PDF,
            source_file=source_name,
        )

        lines = [line.strip() for line in text.split("\n")]
        lines = [line for line in lines if line]  # Remove empty lines

        # --- Global extractions (not section-bound) ---
        self._extract_emails(candidate, text)
        self._extract_phones(candidate, text)
        self._extract_links(candidate, text)
        self._extract_name(candidate, lines)

        # --- Section-based extractions ---
        sections = self._identify_sections(lines)
        self._parse_skills_section(candidate, sections.get("skills", []))
        self._parse_experience_section(candidate, sections.get("experience", []))
        self._parse_education_section(candidate, sections.get("education", []))
        self._parse_summary_section(candidate, sections.get("summary", []))

        # --- Infer location from contact line ---
        self._extract_location(candidate, lines)

        logger.info(
            "PDF '%s': extracted name=%s, emails=%d, phones=%d, skills=%d, "
            "experience=%d, education=%d",
            file_path.name,
            candidate.full_name or "(none)",
            len(candidate.emails),
            len(candidate.phones),
            len(candidate.skills),
            len(candidate.experience),
            len(candidate.education),
        )

        return [candidate]

    def _extract_text(self, file_path: Path) -> str:
        """Extract text from all pages of a PDF.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Concatenated text from all pages.
        """
        pages_text: list[str] = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
        return "\n".join(pages_text)

    def _extract_emails(self, candidate: ParsedCandidate, text: str) -> None:
        """Extract email addresses from the full text."""
        emails = list(set(_EMAIL_RE.findall(text)))
        if emails:
            candidate.emails = emails
            candidate.add_provenance("emails", "regex", _REGEX_CONFIDENCE)
            logger.debug("Found %d email(s): %s", len(emails), emails)

    def _extract_phones(self, candidate: ParsedCandidate, text: str) -> None:
        """Extract phone numbers from the full text.

        Filters out matches that are too short (likely years or zip codes)
        or too long (likely not phone numbers).
        """
        raw_matches = _PHONE_RE.findall(text)
        phones: list[str] = []
        for match in raw_matches:
            # Strip non-digit characters to check length
            digits = re.sub(r"\D", "", match)
            # Valid phone numbers have 7-15 digits (ITU-T E.164)
            if 7 <= len(digits) <= 15:
                phones.append(match.strip())

        if phones:
            # Deduplicate while preserving order
            seen: set[str] = set()
            unique_phones: list[str] = []
            for p in phones:
                digits = re.sub(r"\D", "", p)
                if digits not in seen:
                    seen.add(digits)
                    unique_phones.append(p)

            candidate.phones = unique_phones
            candidate.add_provenance("phones", "regex+phonenumbers", _REGEX_CONFIDENCE)
            logger.debug("Found %d phone(s): %s", len(unique_phones), unique_phones)

    def _extract_links(self, candidate: ParsedCandidate, text: str) -> None:
        """Extract LinkedIn, GitHub, portfolio, and other URLs."""
        linkedin_matches = _LINKEDIN_RE.findall(text)
        if linkedin_matches:
            candidate.linkedin = linkedin_matches[0]
            candidate.add_provenance("links.linkedin", "regex", _REGEX_CONFIDENCE)

        github_matches = _GITHUB_RE.findall(text)
        if github_matches:
            candidate.github = github_matches[0]
            candidate.add_provenance("links.github", "regex", _REGEX_CONFIDENCE)

        # Find other URLs that aren't LinkedIn or GitHub
        all_urls = _URL_RE.findall(text)
        other_urls: list[str] = []
        for url in all_urls:
            url_lower = url.lower()
            if "linkedin.com" not in url_lower and "github.com" not in url_lower:
                other_urls.append(url)

        if other_urls:
            # First non-social URL is likely the portfolio
            candidate.portfolio = other_urls[0]
            candidate.add_provenance("links.portfolio", "regex", _REGEX_CONFIDENCE)
            if len(other_urls) > 1:
                candidate.other_links = other_urls[1:]

    def _extract_name(self, candidate: ParsedCandidate, lines: list[str]) -> None:
        """Extract the candidate's name from the first non-trivial line.

        Heuristic: the name is typically the first line of a resume that
        isn't an email, phone, URL, or section header. We also check that
        it looks like a name (2-5 words, no special characters).
        """
        for line in lines[:5]:  # Only check first 5 lines
            # Skip lines that are clearly not names
            if _NOT_NAME_RE.search(line):
                continue
            if _EMAIL_RE.search(line):
                continue
            if _PHONE_RE.search(line) and len(re.sub(r"\D", "", line)) > 5:
                continue

            # Check if line looks like a section header
            is_header = False
            for keywords in PDF_SECTION_KEYWORDS.values():
                if line.lower().strip() in keywords:
                    is_header = True
                    break
            if is_header:
                continue

            # A name should be 1-5 words, primarily alphabetic
            words = line.split()
            if 1 <= len(words) <= 5:
                # Check that most characters are letters or spaces
                alpha_ratio = sum(c.isalpha() or c.isspace() for c in line) / max(len(line), 1)
                if alpha_ratio > 0.7:
                    candidate.full_name = line.strip()
                    candidate.add_provenance("full_name", "section_heuristic", _SECTION_CONFIDENCE)
                    logger.debug("Extracted name: '%s'", candidate.full_name)
                    return

    def _extract_location(self, candidate: ParsedCandidate, lines: list[str]) -> None:
        """Try to extract location from contact-area lines.

        Heuristic: look for lines in the first 5 lines that contain a
        city/state pattern (e.g. "San Francisco, CA" or "New York, NY 10001").
        """
        # Common US state abbreviations for detection
        state_re = re.compile(r",\s*([A-Z]{2})\b")
        for line in lines[:6]:
            # Skip lines that are just name, email, or URL
            if line == candidate.full_name:
                continue
            match = state_re.search(line)
            if match:
                # Split on the pipe/bullet that separates contact items
                for segment in re.split(r"[|•·]", line):
                    segment = segment.strip()
                    state_match = state_re.search(segment)
                    if state_match:
                        parts = segment.split(",")
                        if len(parts) >= 1:
                            city = parts[0].strip()
                            # Filter out emails and phone fragments
                            if "@" not in city and not city.isdigit():
                                candidate.city = city
                                candidate.add_provenance(
                                    "location.city", "regex", _REGEX_CONFIDENCE
                                )
                        if len(parts) >= 2:
                            region = parts[1].strip().split()[0]  # "CA 94105" → "CA"
                            candidate.region = region
                            candidate.add_provenance("location.region", "regex", _REGEX_CONFIDENCE)
                        return

    def _identify_sections(self, lines: list[str]) -> dict[str, list[str]]:
        """Split the resume into named sections based on header keywords.

        Args:
            lines: Non-empty lines from the PDF.

        Returns:
            Dict mapping section name → list of content lines under that section.
        """
        sections: dict[str, list[str]] = {}
        current_section: str | None = None
        current_lines: list[str] = []

        for line in lines:
            detected_section = self._detect_section_header(line)
            if detected_section:
                # Save previous section
                if current_section is not None:
                    sections[current_section] = current_lines
                current_section = detected_section
                current_lines = []
            elif current_section is not None:
                current_lines.append(line)

        # Save last section
        if current_section is not None:
            sections[current_section] = current_lines

        logger.debug("Identified sections: %s", list(sections.keys()))
        return sections

    def _detect_section_header(self, line: str) -> str | None:
        """Check if a line is a section header.

        Args:
            line: A single line of text.

        Returns:
            Section name if this is a header, None otherwise.
        """
        cleaned = line.strip().lower()
        # Remove common decorators (dashes, colons, etc.)
        cleaned = re.sub(r"[:\-–—_=]+$", "", cleaned).strip()
        cleaned = re.sub(r"^[:\-–—_=]+", "", cleaned).strip()

        for section_name, keywords in PDF_SECTION_KEYWORDS.items():
            if cleaned in keywords:
                return section_name
        return None

    def _parse_skills_section(self, candidate: ParsedCandidate, lines: list[str]) -> None:
        """Parse the SKILLS section into a list of skill strings."""
        if not lines:
            return

        # Join all lines and split by common delimiters
        text = " ".join(lines)
        # Split by comma, pipe, bullet, semicolon, or newline
        raw_skills = re.split(r"[,|•·;]+", text)
        skills = [s.strip() for s in raw_skills if s.strip()]

        # Filter out lines that look like headers or noise
        skills = [s for s in skills if len(s) > 1 and len(s) < 50]

        if skills:
            candidate.skills = skills
            candidate.add_provenance("skills", "section_heuristic", _SECTION_CONFIDENCE)
            logger.debug("Extracted %d skills", len(skills))

    def _parse_experience_section(self, candidate: ParsedCandidate, lines: list[str]) -> None:
        """Parse the EXPERIENCE section into structured entries.

        Looks for patterns like:
        - "Title | Company | Date Range"
        - "Title at Company"
        - "Company — Title"
        Followed by bullet-point descriptions.
        """
        if not lines:
            return

        experiences: list[Experience] = []
        current_exp: dict[str, str | None] = {}
        current_bullets: list[str] = []

        for line in lines:
            # Try "Title | Company | Date" pattern
            exp_match = _EXPERIENCE_LINE_RE.match(line)
            date_match = _DATE_RANGE_RE.search(line)

            if exp_match or date_match:
                # Save previous experience
                if current_exp:
                    if current_bullets:
                        current_exp["summary"] = " ".join(current_bullets)
                    experiences.append(Experience(**current_exp))
                    current_bullets = []

                current_exp = {}

                if exp_match:
                    current_exp["title"] = exp_match.group(1).strip()
                    current_exp["company"] = exp_match.group(2).strip()
                    date_text = exp_match.group(3).strip()
                    date_range = _DATE_RANGE_RE.search(date_text)
                    if date_range:
                        current_exp["start"] = date_range.group(1).strip()
                        end_val = date_range.group(2).strip()
                        current_exp["end"] = (
                            None if end_val.lower() in ("present", "current", "now") else end_val
                        )
                elif date_match:
                    # Line has dates but different format — try to split
                    pre_date = line[: date_match.start()].strip().rstrip("-–—|•·")
                    parts = re.split(r"[|•·–—]", pre_date)
                    if len(parts) >= 2:
                        current_exp["title"] = parts[0].strip()
                        current_exp["company"] = parts[1].strip()
                    elif len(parts) == 1 and parts[0].strip():
                        current_exp["title"] = parts[0].strip()

                    current_exp["start"] = date_match.group(1).strip()
                    end_val = date_match.group(2).strip()
                    current_exp["end"] = (
                        None if end_val.lower() in ("present", "current", "now") else end_val
                    )

            elif line.startswith(("-", "•", "·", "–", "→", "▪", "►")):
                # Bullet point — belongs to current experience
                bullet_text = line.lstrip("-•·–→▪► ").strip()
                if bullet_text:
                    current_bullets.append(bullet_text)

        # Save last experience
        if current_exp:
            if current_bullets:
                current_exp["summary"] = " ".join(current_bullets)
            experiences.append(Experience(**current_exp))

        if experiences:
            candidate.experience = experiences
            candidate.add_provenance("experience", "section_heuristic", _SECTION_CONFIDENCE)
            logger.debug("Extracted %d experience entries", len(experiences))

    def _parse_education_section(self, candidate: ParsedCandidate, lines: list[str]) -> None:
        """Parse the EDUCATION section into structured entries.

        Looks for patterns like:
        - "Degree in Field"
        - "Institution | Year"
        - "B.S. Computer Science, University of X, 2020"
        """
        if not lines:
            return

        educations: list[Education] = []
        i = 0
        while i < len(lines):
            line = lines[i]

            # Look for degree keywords
            degree_keywords = [
                "bachelor",
                "master",
                "phd",
                "ph.d",
                "doctorate",
                "associate",
                "b.s.",
                "b.a.",
                "m.s.",
                "m.a.",
                "m.b.a.",
                "b.tech",
                "m.tech",
                "b.sc",
                "m.sc",
                "b.e.",
                "m.e.",
            ]
            is_degree_line = any(kw in line.lower() for kw in degree_keywords)

            if is_degree_line:
                edu: dict[str, str | None] = {}
                edu["degree"] = line.strip()

                # Extract year from this line
                year_match = _YEAR_RE.search(line)
                if year_match:
                    edu["end_year"] = year_match.group(1)
                    # Remove year from degree string to clean it up
                    edu["degree"] = _YEAR_RE.sub("", line).strip().rstrip("|,- ")

                # Check next line for institution or year
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    next_year = _YEAR_RE.search(next_line)

                    if next_year and not any(kw in next_line.lower() for kw in degree_keywords):
                        # Next line is institution + year
                        edu["institution"] = _YEAR_RE.sub("", next_line).strip().rstrip("|,- ")
                        if not edu.get("end_year"):
                            edu["end_year"] = next_year.group(1)
                        i += 1
                    elif not any(kw in next_line.lower() for kw in degree_keywords):
                        # Next line might be institution without year
                        if len(next_line.split()) <= 10:
                            edu["institution"] = next_line.strip().rstrip("|,- ")
                            i += 1

                educations.append(Education(**edu))

            i += 1

        if educations:
            candidate.education = educations
            candidate.add_provenance("education", "section_heuristic", _SECTION_CONFIDENCE)
            logger.debug("Extracted %d education entries", len(educations))

    def _parse_summary_section(self, candidate: ParsedCandidate, lines: list[str]) -> None:
        """Parse the SUMMARY/OBJECTIVE section."""
        if not lines:
            return

        summary = " ".join(lines)
        if summary.strip():
            candidate.summary = summary.strip()
            candidate.add_provenance("summary", "section_heuristic", _SECTION_CONFIDENCE)

            # Try to extract years of experience from summary
            yoe_match = re.search(
                r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)?",
                summary,
                re.IGNORECASE,
            )
            if yoe_match and candidate.years_experience is None:
                try:
                    candidate.years_experience = float(yoe_match.group(1))
                    candidate.add_provenance("years_experience", "regex", _REGEX_CONFIDENCE)
                except ValueError:
                    pass
