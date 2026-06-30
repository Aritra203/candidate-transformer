"""Generate a sample resume PDF for testing.

Uses pdfplumber-compatible text layout. We use reportlab (or fall back to
a minimal PDF generator) to create a realistic resume that exercises the
PDF parser's section detection, regex extraction, and edge-case handling.
"""

import sys
from pathlib import Path


def _generate_minimal_pdf(output_path: Path) -> None:
    """Generate a minimal valid PDF with resume content using raw PDF operators.

    This avoids requiring reportlab as a dependency — we write the PDF
    structure by hand. The text is laid out as a single-page document that
    pdfplumber can reliably extract.
    """
    lines = [
        "PRIYA SHARMA",
        "",
        "priya.sharma@email.com | (415) 555-1234 | San Francisco, CA",
        "LinkedIn: https://linkedin.com/in/priyasharma",
        "GitHub: https://github.com/priyasharma",
        "Portfolio: https://priyasharma.dev",
        "",
        "PROFESSIONAL SUMMARY",
        "Senior Software Engineer with 6+ years of experience building",
        "scalable distributed systems and data pipelines. Passionate about",
        "clean architecture and developer experience.",
        "",
        "SKILLS",
        "Python, JavaScript, TypeScript, React, Node.js, PostgreSQL, MongoDB,",
        "AWS, Docker, Kubernetes, CI/CD, REST, GraphQL, Git, Agile, Scrum",
        "",
        "EXPERIENCE",
        "",
        "Senior Software Engineer | Stripe | Jan 2021 - Present",
        "- Designed and built real-time payment processing pipeline handling",
        "  50K transactions per second",
        "- Led migration from monolith to microservices architecture",
        "- Mentored team of 4 junior engineers",
        "",
        "Software Engineer | Datadog | Mar 2019 - Dec 2020",
        "- Built customer-facing dashboards using React and TypeScript",
        "- Implemented distributed tracing backend in Go and Python",
        "- Reduced p99 latency by 40% through query optimization",
        "",
        "Junior Developer | Acme Corp | Jun 2017 - Feb 2019",
        "- Developed RESTful APIs using Django and Flask",
        "- Maintained CI/CD pipelines with Jenkins and Docker",
        "",
        "EDUCATION",
        "",
        "Master of Science in Computer Science",
        "Stanford University | 2017",
        "",
        "Bachelor of Technology in Information Technology",
        "IIT Bombay | 2015",
    ]

    # Build PDF content stream
    text_content = "BT\n/F1 11 Tf\n"
    y = 780
    for line in lines:
        # Escape PDF special characters
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        text_content += f"1 0 0 1 50 {y} Tm\n({escaped}) Tj\n"
        y -= 16
        if y < 40:
            break
    text_content += "ET"

    content_bytes = text_content.encode("latin-1")
    content_length = len(content_bytes)

    # Assemble PDF objects
    pdf_parts: list[str] = []
    offsets: list[int] = []

    pdf_parts.append("%PDF-1.4\n")

    # Object 1: Catalog
    offsets.append(len("".join(pdf_parts).encode("latin-1")))
    pdf_parts.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

    # Object 2: Pages
    offsets.append(len("".join(pdf_parts).encode("latin-1")))
    pdf_parts.append("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")

    # Object 3: Page
    offsets.append(len("".join(pdf_parts).encode("latin-1")))
    pdf_parts.append(
        "3 0 obj\n<< /Type /Page /Parent 2 0 R "
        "/MediaBox [0 0 612 792] "
        "/Contents 4 0 R "
        "/Resources << /Font << /F1 5 0 R >> >> >>\n"
        "endobj\n"
    )

    # Object 4: Content stream
    offsets.append(len("".join(pdf_parts).encode("latin-1")))
    pdf_parts.append(
        f"4 0 obj\n<< /Length {content_length} >>\nstream\n"
    )

    # Write the header portion
    header = "".join(pdf_parts).encode("latin-1")

    # After stream content
    trailer_parts: list[str] = []
    trailer_parts.append("\nendstream\nendobj\n")

    # Object 5: Font
    offset_5 = len(header) + content_length + len(trailer_parts[0].encode("latin-1"))
    trailer_parts.append(
        "5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    )

    # Xref table
    xref_offset = offset_5 + len(
        "5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n".encode(
            "latin-1"
        )
    )

    # Build xref
    all_offsets = offsets + [offset_5]
    xref = "xref\n0 6\n"
    xref += "0000000000 65535 f \n"
    for off in all_offsets:
        xref += f"{off:010d} 00000 n \n"

    trailer_parts.append(xref)
    trailer_parts.append(
        f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"
    )

    trailer = "".join(trailer_parts).encode("latin-1")

    # Write PDF
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(header)
        f.write(content_bytes)
        f.write(trailer)

    print(f"Generated sample resume: {output_path}")


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("sample_data/resume.pdf")
    _generate_minimal_pdf(out)
