# Multi-Source Candidate Data Transformer — Technical Design

## Pipeline

```
Input Files → Detect → Parse → Normalize → Canonical Model → Merge → Confidence → Project → Validate → JSON
```

| Stage | Responsibility | Key Decision |
|---|---|---|
| **Detect** | Classify file by extension + content sniffing | `.csv` → CSV parser, `.pdf` → PDF parser; unknown → skip with warning |
| **Parse** | Extract raw key-value pairs from each source | CSV: Polars row→dict; PDF: pdfplumber text→regex/section extraction |
| **Normalize** | Coerce raw values into canonical formats | Phones→E.164, dates→YYYY-MM, countries→ISO 3166 α-2, skills→canonical map |
| **Merge** | Combine N partial candidates into one record | Deterministic priority: Resume > CSV; union for lists, priority-pick for scalars |
| **Confidence** | Score every field by source reliability + method | Base confidence per source × method modifier; overall = weighted average |
| **Project** | Reshape canonical model per runtime JSON config | Select/rename/remap fields; toggle provenance/confidence; handle missing values |
| **Validate** | Assert output conforms to schema and config constraints | Pydantic model validation; required-field checks; type enforcement |

## Canonical Schema

```
CandidateProfile:
  candidate_id: str                          # SHA-256(name ∥ sorted-emails ∥ sorted-phones)
  full_name: str | None
  emails: list[str]                          # lowercase, validated, deduplicated
  phones: list[str]                          # E.164 format
  location: {city, region, country}          # country = ISO 3166 α-2
  links: {linkedin, github, portfolio, other[]}
  headline: str | None
  years_experience: float | None
  skills: list[{name, confidence, sources}]  # canonical names via alias map
  experience: list[{company, title, start, end, summary}]  # dates = YYYY-MM
  education: list[{institution, degree, field, end_year}]
  provenance: list[{field, source, method, confidence}]
  overall_confidence: float                  # [0.0, 1.0]
```

## Normalization Rules

| Field | Method | Library |
|---|---|---|
| Phone | Parse with `phonenumbers`, format as E.164; default region US | `phonenumbers` |
| Email | Lowercase, strip, validate RFC 5322; reject invalid → null | `email-validator` |
| Date | Parse freeform with `dateutil`, emit `YYYY-MM`; unparseable → null | `python-dateutil` |
| Country | Fuzzy match name/code to ISO 3166 α-2 via `pycountry` | `pycountry` |
| Skill | Alias map (ReactJS→React, NodeJS→Node.js); case-normalize; deduplicate by canonical key | `rapidfuzz` for fuzzy dedup |

## Merge Strategy

**Match key**: `SHA-256(lowercase(name) ∥ sorted(emails))` — if emails overlap or names fuzzy-match (>90 score), candidates merge.

**Priority order** (higher wins for scalar conflicts):

```
resume.pdf  (priority=100)  →  most authoritative self-reported data
candidate.csv (priority=80)  →  recruiter-entered, may lag
```

**Rules by field type**:
- **Scalars** (name, headline): highest-priority source wins; loser recorded in provenance.
- **Lists** (emails, phones, skills): union-merge, deduplicate by canonical form.
- **Nested lists** (experience, education): deduplicate by (company+title+start) or (institution+degree); merge non-null fields from lower-priority source into winner.

Every merge decision records: `{field, winner_source, loser_source, winner_value, loser_value, reason}`.

## Confidence Scoring

**Base confidence by source:**

| Source | Base |
|---|---|
| Resume PDF | 0.92 |
| Recruiter CSV | 0.84 |

**Method modifiers** (multiplicative):

| Method | Modifier |
|---|---|
| Structured field (CSV column) | 1.00 |
| Regex extraction | 0.95 |
| Section-header heuristic | 0.90 |
| Fuzzy match | 0.85 |

**Field confidence** = `source_base × method_modifier`, clamped to [0.0, 1.0].

**Overall confidence** = weighted average across non-null fields, weights proportional to field importance (name=3, email=2, phone=2, skills=2, experience=2, education=1, location=1, headline=1).

## Projection Layer

Runtime JSON config drives output reshaping **without mutating** the canonical model:

```json
{
  "fields": [
    {"path": "full_name", "type": "string", "required": true},
    {"path": "primary_email", "from": "emails[0]", "type": "string"}
  ],
  "include_confidence": true,
  "include_provenance": false,
  "on_missing": "null"          // "null" | "omit" | "error"
}
```

**Resolution**: `from` uses dot-notation with array indexing (`emails[0]`, `location.country`). Config is validated before pipeline runs — unknown paths or type mismatches fail fast.

## Validation

1. **Config validation** — at startup, before any I/O.
2. **Per-source validation** — after parsing, malformed rows logged and skipped.
3. **Canonical model validation** — Pydantic enforces types; fields without provenance are rejected.
4. **Output validation** — projected output re-validated against declared types and required constraints.

## Edge Cases Handled

| Case | Behavior |
|---|---|
| Missing/unreadable file | Log warning, continue with remaining sources |
| Empty CSV / blank PDF | Produce empty candidate with `overall_confidence = 0.0` |
| Conflicting names across sources | Highest-priority source wins; provenance records both |
| Invalid phone/email | Logged, set to null; never emitted as garbage |
| Duplicate skills with different casing | Canonicalized and deduplicated |
| No sources produce a name | `full_name = null`, `candidate_id` uses available emails/phones |
| Projection requests missing field | Respects `on_missing` config: null / omit / raise error |

## Intentionally Out of Scope

- **NLP/ML-based resume parsing**: regex + section-header heuristics are deterministic and explainable; ML adds non-determinism.
- **GitHub/LinkedIn API integration**: architecture supports it (new parser class), but not implemented in v1.
- **DOCX parsing**: same parser interface, not implemented.
- **Concurrent/async pipeline**: single-threaded is sufficient for thousands of candidates; concurrency adds complexity without clear need at this scale.
- **Database persistence**: output is JSON files; a DB layer is a separate concern.
- **Internationalized name parsing**: names are treated as opaque strings, not split into first/last (culturally fraught).
