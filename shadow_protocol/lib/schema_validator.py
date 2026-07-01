"""JSON Schema validation for agent outputs."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from jsonschema import validate, ValidationError


def validate_output(
    instance: dict[str, Any],
    schema_path: str | Path,
) -> list[str]:
    """Validate a dict against a JSON Schema file.

    Args:
        instance: The data to validate
        schema_path: Path to the JSON Schema file

    Returns:
        List of error messages. Empty list means valid.
    """
    with open(schema_path, "r") as f:
        schema = json.load(f)

    errors: list[str] = []
    try:
        validate(instance=instance, schema=schema)
    except ValidationError as e:
        # Walk the full error tree
        for err in sorted(e.context, key=lambda x: x.path) if hasattr(e, "context") else [e]:
            path = " -> ".join(str(p) for p in err.absolute_path) or "root"
            errors.append(f"{path}: {err.message}")
    return errors


def validate_output_file(
    data_path: str | Path,
    schema_path: str | Path,
) -> list[str]:
    """Load a JSON file and validate it against a schema."""
    with open(data_path, "r") as f:
        instance = json.load(f)
    return validate_output(instance, schema_path)
