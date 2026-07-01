"""File system utilities for reading/writing agent artifacts."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any


def read_json(path: str | Path) -> dict[str, Any]:
    """Read and parse a JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def write_json(path: str | Path, data: Any, indent: int = 2) -> None:
    """Write data as pretty-printed JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
        f.write("\n")


def read_text(path: str | Path) -> str:
    """Read a text file."""
    with open(path, "r") as f:
        return f.read()


def write_text(path: str | Path, content: str) -> None:
    """Write a text file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a JSON config, resolving ${ENV_VAR} references."""
    data = read_json(path)
    return _resolve_env_refs(data)


def _resolve_env_refs(obj: Any) -> Any:
    """Recursively resolve ${VAR} patterns in strings."""
    import os
    import re

    if isinstance(obj, str):
        pattern = re.compile(r"\$\{([^}]+)\}")
        return pattern.sub(lambda m: os.getenv(m.group(1), m.group(0)), obj)
    elif isinstance(obj, dict):
        return {k: _resolve_env_refs(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_resolve_env_refs(v) for v in obj]
    return obj
