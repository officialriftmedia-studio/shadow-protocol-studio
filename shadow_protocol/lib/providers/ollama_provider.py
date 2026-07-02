"""Ollama provider — local LLM inference via Ollama API.

Supports: qwen3:8b, qwen3:14b, deepseek-r1:14b
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any

import httpx


class OllamaProvider:
    """Ollama-based text generation provider for non-critical stages.

    Reduces Gemini/OpenAI consumption by routing suitable stages
    (production_package, outline, scene_breakdown, image_prompt,
    video_prompt, metadata, thumbnail, voiceover) to local models.
    """

    name = "ollama"

    # Model → context window
    _MODEL_MAX_TOKENS = {
        "qwen3:8b": 32768,
        "qwen3:14b": 32768,
        "deepseek-r1:14b": 16384,
    }

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.base_url = os.environ.get("OLLAMA_HOST") or self.config.get("base_url", "http://localhost:11434")
        self.timeout = self.config.get("timeout", 120)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: str | None = None,
    ) -> tuple[str, int, int]:
        """Call an Ollama model and return (text, prompt_tokens, completion_tokens)."""
        model = model or "qwen3:14b"
        url = f"{self.base_url}/api/chat"

        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": user_prompt})

        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": False,
        }

        if response_format == "json":
            body["format"] = "json"

        resp = httpx.post(url, json=body, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        text = data.get("message", {}).get("content", "")
        if not text:
            text = data.get("response", "")

        prompt_tok = data.get("prompt_eval_count", 0)
        completion_tok = data.get("eval_count", 0)

        return text, prompt_tok, completion_tok

    @classmethod
    def is_available(cls, base_url: str = "http://localhost:11434") -> bool:
        """Check if Ollama is reachable."""
        try:
            resp = httpx.get(f"{base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    @classmethod
    def list_models(cls, base_url: str = "http://localhost:11434") -> list[str]:
        """List models available on the Ollama server."""
        try:
            resp = httpx.get(f"{base_url}/api/tags", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []
