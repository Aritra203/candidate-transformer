"""Quick verification script for the projection layer."""
import json
from pathlib import Path
from src.parsers.csv_parser import CsvParser
from src.parsers.pdf_parser import PdfParser
from src.pipeline.normalizer import normalize_candidate
from src.pipeline.merger import merge_candidates
from src.pipeline.confidence import compute_confidence
from src.pipeline.projection import project
from src.models.config import ProjectionConfig

# Build the canonical profile
all_c = CsvParser().parse(Path("sample_data/candidate.csv")) + PdfParser().parse(Path("sample_data/resume.pdf"))
for c in all_c:
    normalize_candidate(c)
profile = compute_confidence(merge_candidates(all_c)[0])

# Test 1: Default config
print("=== DEFAULT PROJECTION ===")
default_cfg = ProjectionConfig(**json.loads(Path("config/default.json").read_text()))
default_out = project(profile, default_cfg)
print(f"Fields: {list(default_out.keys())}")
print(f"full_name: {default_out.get('full_name')}")
print(f"emails: {default_out.get('emails')}")
print(f"overall_confidence: {default_out.get('overall_confidence')}")
prov = default_out.get("provenance", [])
print(f"provenance records: {len(prov)}")

# Test 2: Custom config
print()
print("=== CUSTOM PROJECTION ===")
custom_cfg = ProjectionConfig(**json.loads(Path("config/custom.json").read_text()))
custom_out = project(profile, custom_cfg)
print(f"Fields: {list(custom_out.keys())}")
for k, v in custom_out.items():
    if isinstance(v, list) and len(v) > 5:
        print(f"  {k}: {v[:5]}...")
    else:
        print(f"  {k}: {v}")
