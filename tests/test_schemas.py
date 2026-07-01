"""Tests for JSON Schema validation."""

from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from shadow_protocol.lib.schema_validator import validate_output


SCHEMA_DIR = Path("templates/schemas")


def test_all_schemas_are_valid_json():
    """Every schema file must be parseable JSON."""
    for f in SCHEMA_DIR.rglob("*.json"):
        with open(f) as fh:
            data = json.load(fh)
        assert "$schema" in data, f"{f} missing $schema"


def test_bible_characters_schema():
    """bible/characters.json must validate against its schema."""
    from shadow_protocol.lib.schema_validator import validate_output_file

    schema_path = SCHEMA_DIR / "bible" / "characters.json"
    data_path = Path("bible/characters.json")
    if data_path.exists():
        errors = validate_output_file(data_path, schema_path)
        assert errors == [], f"Validation errors: {errors}"
