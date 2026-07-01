"""Base class for all agents implementing the common contract."""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Any


class AgentError(Exception):
    """Machine-readable agent error."""
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"[{code}] {message}")


class AgentBase:
    """Every agent extends this and implements run()."""

    name: str = "base"

    def __init__(self, input_dir: str, output_dir: str, config: dict[str, Any]):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.config = config

    def run(self) -> int:
        raise NotImplementedError

    def fail(self, code: str, message: str) -> int:
        print(f"AGENT_ERROR: code={code} message={message}", file=sys.stderr)
        return 1
