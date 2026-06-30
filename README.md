# Multi-Source Candidate Data Transformer

A production-quality data engineering pipeline that ingests candidate profiles from heterogeneous structured and unstructured sources (Recruiter CSVs & Resume PDFs), cleanses and normalizes field values, merges duplicates using deterministic rules, tracks provenance metadata, scores extraction confidence, and projects the final output using a configurable layout.

This repository now contains a modern, enterprise-quality web application dashboard built in Next.js 16 (App Router) + TypeScript + Tailwind CSS + Lucide React, communicating with a python FastAPI backend server.

---

## Folder Structure

```
candidate-transformer/
├── app/                                    # Next.js App Router (Layout & Pages)
├── components/                             # Reusable React components (Sidebar, JsonViewer, etc.)
├── hooks/                                  # React hooks & Context (usePipeline state management)
├── services/                               # Client API service layer (apiService)
├── types/                                  # TypeScript definitions
├── src/                                    # Python Pipeline Package source code
├── config/                                 # Runtime output projection configs (default.json, custom.json)
├── output/                                 # Transformed JSON profiles destination
├── sample_data/                            # Tabular recruiter data and PDF resume sample
├── server.py                               # FastAPI backend API server proxy wrapper
├── main.py                                 # Python CLI proxy entry point
├── package.json                            # Next.js npm dependencies
├── requirements.txt                        # Python pipeline dependencies
└── pyproject.toml                          # Python linters and configs
```

---

## Getting Started

Follow these steps to set up and run both the backend API server and the frontend dashboard.

### 1. Backend Server Setup

Ensure you are using Python 3.12 or 3.13.

```bash
# Install python requirements (includes fastapi, uvicorn, python-multipart, polars, rapidfuzz, pdfplumber, etc.)
pip install -r requirements.txt

# Start the FastAPI API server
python server.py
```
The backend API server will start running at `http://127.0.0.1:8000`.

### 2. Frontend Dashboard Setup

Ensure you have Node.js v18+ (tested on Node.js v24).

```bash
# Install npm dependencies
npm install

# Start the Next.js development server
npm run dev
```
The frontend dashboard will start running at `http://localhost:3000`.

Open your browser to `http://localhost:3000` to interact with the enterprise recruitment dashboard!

---

## Web Application Features

The UI is designed to feel like an internal recruiting platform (matching aesthetics of Vercel Dashboard, Stripe, and Linear) and is organized across 7 panels:

1. **Dashboard**: Unified overview of the pipeline status, uploaded file states, config projection indicators, and quick links to run the transformation or view merged candidate cards.
2. **Upload**: Drag-and-drop file uploaders for Recruiter CSVs, Resume PDFs, and custom JSON configuration maps with size parsing and live validation warnings.
3. **Configuration**: A dual-pane settings editor. Use the GUI builder on the left to map paths, add/remove fields, adjust missing-value policies, and toggle confidence/provenance, or edit raw JSON on the right. Validate in real time via the backend validate-config API.
4. **Pipeline**: Visual stepper showing each ingestion node (`Detection` → `Parser` → `Normalizer` → `Merger` → `Confidence` → `Projection` → `Validation`).
5. **Output Profile**: Highlights canonical candidates in an ATS-style candidate card alongside a searchable, collapsible JSON tree viewer and a sortable provenance audit table.
6. **Execution Logs**: Terminal console printing real-time messages emitted by the Python modules (INFO, SUCCESS, WARNING, ERROR) with GREP log search filters.
7. **About Project**: Engineering documentation detailing deterministic candidate IDs, conflict authority resolution, and normalizers.

---

## Running the Pipeline (CLI Command Line)

To run the transformer using the CLI terminal instead of the browser interface:

```bash
# Run with verbose logging using default projection config
python main.py \
  --csv sample_data/candidate.csv \
  --resume sample_data/resume.pdf \
  --config config/default.json \
  --output output/result.json \
  --verbose

# Run with custom projection config mapping sub-fields
python main.py \
  --csv sample_data/candidate.csv \
  --resume sample_data/resume.pdf \
  --config config/custom.json \
  --output output/custom_result.json
```

---

## Testing (Python CLI Core)

Run all 21 test suites verifying correctness and degradation behavior:

```bash
# Run test suite
python -m pytest tests/ -v

# Run strict type checking (Mypy)
python -m mypy src/ --strict

# Run formatting check
python -m black --check src/ tests/

# Run linting check
python -m ruff check src/ tests/
```

---

## Core Pipeline Normalization Rules

| Field | Method | Library |
|---|---|---|
| **Phone** | Parse with `phonenumbers`, format as E.164; default US | `phonenumbers` |
| **Email** | Lowercase, strip, validate RFC 5322; reject invalid | `email-validator` |
| **Date** | Parse freeform with `dateutil`, format as YYYY-MM | `python-dateutil` |
| **Country** | Fuzzy match name/code to ISO 3166 α-2 | `pycountry` |
| **Skill** | Case-normalization + RapidFuzz dedup at 90% threshold | `rapidfuzz` |

---

## Technical Architecture & Decisions

1. **Deterministic Unique IDs**: Generates a deterministic SHA-256 hash using the candidate's canonical name, sorted emails, and sorted phone numbers. This ensures identical records combine into the same candidate identifier regardless of input format or sequence.
2. **Authority Priority Scoring**: Conflicting field values resolve deterministically by source reliability: `Resume PDF (100) > Recruiter CSV (80)`. Provenance trails are kept for every resolved field.
3. **Pydantic Validation Guardrails**: Config validations run before ingestion execution, and final outputs are re-validated against projected schema models.
