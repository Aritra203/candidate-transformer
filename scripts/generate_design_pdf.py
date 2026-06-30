"""Generate the beautiful 1-page design document PDF using ReportLab."""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles to squeeze on one page elegantly
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1A365D'),
        spaceAfter=6
    )
    
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#2B6CB0'),
        spaceBefore=6,
        spaceAfter=4,
        borderPadding=2,
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#2D3748')
    )
    
    code_style = ParagraphStyle(
        'CodeStyleCustom',
        parent=styles['Code'],
        fontSize=7,
        leading=8,
        textColor=colors.HexColor('#D69E2E')
    )
    
    table_text_style = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor('#2D3748')
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=7.5,
        leading=9,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )

    story = []
    
    # Title
    story.append(Paragraph("Multi-Source Candidate Data Transformer — Technical Design", title_style))
    story.append(Paragraph("<b>Architect:</b> Staff Software Engineer | <b>Target:</b> Eightfold AI Engineering Committee", body_style))
    story.append(Spacer(1, 8))
    
    # 1. Pipeline Description
    story.append(Paragraph("1. System Architecture & Pipeline", h2_style))
    pipeline_text = (
        "The system processes multiple heterogeneous raw sources (e.g., CSV, PDF resumes) "
        "through a sequence of single-responsibility stages: <br/>"
        "<b>Detect:</b> Suffix mapping to identify format. | "
        "<b>Parse:</b> Row/text extraction (Polars & pdfplumber). | "
        "<b>Normalize:</b> Field cleansing (E.164, YYYY-MM, ISO 3166). | "
        "<b>Merge:</b> Deduplication & conflict resolution via priority. | "
        "<b>Confidence:</b> Multi-source boost & weighted scoring. | "
        "<b>Project:</b> Config-driven output filtering (dot & index paths). | "
        "<b>Validate:</b> Output type validation."
    )
    story.append(Paragraph(pipeline_text, body_style))
    
    # 2. Canonical Output Schema
    story.append(Paragraph("2. Canonical Candidate Model", h2_style))
    schema_text = (
        "<b>CandidateProfile (Immutable / Frozen)</b><br/>"
        "&nbsp;&nbsp;• <b>candidate_id</b>: Deterministic SHA-256 hash of: <code>lower(name) || sorted(emails) || sorted(phones)</code><br/>"
        "&nbsp;&nbsp;• <b>full_name</b>: Opaque string (no first/last splits to avoid cultural assumptions).<br/>"
        "&nbsp;&nbsp;• <b>emails / phones</b>: Deduplicated arrays. Phones normalized strictly to E.164. <br/>"
        "&nbsp;&nbsp;• <b>location / links</b>: Structured sub-objects with country normalized to ISO-3166 Alpha-2.<br/>"
        "&nbsp;&nbsp;• <b>skills</b>: aggregated <code>Skill</code> sub-models containing source lists and local confidence metrics.<br/>"
        "&nbsp;&nbsp;• <b>experience / education</b>: deduplicated nested history lists tracking titles, dates (YYYY-MM), and credentials."
    )
    story.append(Paragraph(schema_text, body_style))
    
    # 3. Normalization Rules Table
    story.append(Paragraph("3. Field Normalization Specifications", h2_style))
    norm_data = [
        [Paragraph("Field", table_header_style), Paragraph("Normalization Standard", table_header_style), Paragraph("Graceful Degradation Behavior", table_header_style)],
        [Paragraph("Phones", table_text_style), Paragraph("Parse via <code>phonenumbers</code> -> E.164 (e.g. +14155551234)", table_text_style), Paragraph("Unparseable / invalid numbers are omitted (become null)", table_text_style)],
        [Paragraph("Emails", table_text_style), Paragraph("RFC 5322 validation (lowercase, trimmed)", table_text_style), Paragraph("Invalid syntaxes are logged & omitted (never emit garbage)", table_text_style)],
        [Paragraph("Dates", table_text_style), Paragraph("YYYY-MM (fuzzy parser fallback). 'Present' -> null end date.", table_text_style), Paragraph("Unparseable dates become null; single year defaults to YYYY-01", table_text_style)],
        [Paragraph("Countries", table_text_style), Paragraph("ISO 3166-1 Alpha-2 mapping via <code>pycountry</code>", table_text_style), Paragraph("Unresolved country strings are set to null", table_text_style)],
        [Paragraph("Skills", table_text_style), Paragraph("Alias map check + fuzzy matching list dedup (score > 90)", table_text_style), Paragraph("Acronyms kept in uppercase; others formatted in Title Case", table_text_style)]
    ]
    t = Table(norm_data, colWidths=[60, 240, 240])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2B6CB0')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#F7FAFC'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(t)
    
    # 4. Merge & Confidence Strategy
    story.append(Paragraph("4. Deterministic Merge & Confidence Engine", h2_style))
    merge_text = (
        "<b>Deduplication:</b> Matches candidates via email overlap or case-insensitive fuzzy name matching. "
        "<b>Priority:</b> In case of field conflicts, values are selected from the highest-priority source: "
        "<code>Resume PDF (100) > Recruiter CSV (80)</code>. Provenance tracks winning and losing values.<br/>"
        "<b>Gap-Filling:</b> For nested lists (experience & education), records match on composite keys (company+title). "
        "Missing fields in the winner are merged from lower-priority duplicates.<br/>"
        "<b>Confidence:</b> Calculated as <code>base_confidence (Source) * method_modifier (Method)</code>. "
        "Corroborating agreements boost confidence by <code>+0.03</code> per source (cap 1.0). "
        "Overall confidence is the weighted average of active non-null fields."
    )
    story.append(Paragraph(merge_text, body_style))
    
    # 5. Configurable Projection Layer & Edge Cases
    story.append(Paragraph("5. Projection Layer & Robustness Rules", h2_style))
    projection_text = (
        "<b>Projection:</b> Supports dot-notation, list indexing (<code>emails[0]</code>), and array field plucking "
        "(<code>skills[].name</code>). Configured missing values are handled via <code>null</code>, <code>omit</code>, "
        "or raising a <code>ProjectionError</code>.<br/>"
        "<b>Edge Cases Handled:</b> Missing source files, corrupted PDF files, empty tables, duplicate/conflicting name spellings. "
        "The system degrades gracefully, logging issues and processing valid records. Unknown values default to null, never invented."
    )
    story.append(Paragraph(projection_text, body_style))
    
    doc.build(story)
    print(f"Generated design document PDF: {output_path}")

if __name__ == "__main__":
    out_dir = Path(__file__).parent.parent
    
    # Generate for workspace system user name
    out_pdf_victus = out_dir / "Aritra_Victus_aritra_victus_Eightfold.pdf"
    generate_pdf(out_pdf_victus)
    
    # Generate for candidate parsed resume name
    out_pdf_konar = out_dir / "Aritra_Konar_konararitra72@gmail.com_Eightfold.pdf"
    generate_pdf(out_pdf_konar)
