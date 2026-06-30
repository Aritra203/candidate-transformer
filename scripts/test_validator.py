"""Quick verification of the validator."""
from pathlib import Path
from src.pipeline.validator import load_and_validate_config, validate_output
from src.utils.exceptions import ConfigurationError, ValidationError

# Test 1: Valid default config
print("=== Valid default config ===")
try:
    cfg = load_and_validate_config(Path("config/default.json"))
    print(f"  OK: {len(cfg.fields)} fields validated")
except ConfigurationError as e:
    print(f"  FAIL: {e}")

# Test 2: Valid custom config
print("=== Valid custom config ===")
try:
    cfg = load_and_validate_config(Path("config/custom.json"))
    print(f"  OK: {len(cfg.fields)} fields validated")
except ConfigurationError as e:
    print(f"  FAIL: {e}")

# Test 3: Missing config file
print("=== Missing config file ===")
try:
    load_and_validate_config(Path("config/nonexistent.json"))
    print("  FAIL: should have raised")
except ConfigurationError as e:
    print(f"  OK (expected error): {e}")

# Test 4: Output validation - required field missing
print("=== Output validation: required field null ===")
from src.models.config import ProjectionConfig, FieldProjection
cfg = ProjectionConfig(
    fields=[FieldProjection(path="full_name", type="string", required=True)],
    include_confidence=False,
    include_provenance=False,
)
try:
    validate_output({"full_name": None}, cfg)
    print("  FAIL: should have raised")
except ValidationError as e:
    print(f"  OK (expected error): {e}")

# Test 5: Output validation - type mismatch
print("=== Output validation: type mismatch ===")
try:
    validate_output({"full_name": 42}, cfg)
    print("  FAIL: should have raised")
except ValidationError as e:
    print(f"  OK (expected error): {e}")

# Test 6: Output validation - valid
print("=== Output validation: valid ===")
try:
    validate_output({"full_name": "Priya Sharma"}, cfg)
    print("  OK: validation passed")
except ValidationError as e:
    print(f"  FAIL: {e}")
