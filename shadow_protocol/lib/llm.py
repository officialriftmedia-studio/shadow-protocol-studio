"""LLM abstraction layer — multi-provider with token tracking and retry."""

from __future__ import annotations
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class QuotaExceededError(RuntimeError):
    """Raised when the LLM provider returns a quota/rate-limit error."""
    def __init__(self, message: str, provider: str = ""):
        self.provider = provider
        super().__init__(message)


@dataclass
class LLMUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    calls: int = 0
    cost_usd: float = 0.0
    history: list[dict] = field(default_factory=list)

    def add(self, prompt: int, completion: int, cost: float, model: str) -> None:
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.calls += 1
        self.cost_usd += cost
        self.history.append({"model": model, "prompt": prompt, "completion": completion, "cost": cost})

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def log_line(self) -> str:
        return (
            f"LLM: {self.calls} calls, "
            f"{self.total_tokens} tokens "
            f"(prompt={self.prompt_tokens} + completion={self.completion_tokens}), "
            f"${self.cost_usd:.4f}"
        )


_USAGE = LLMUsage()

# Cache for stage_models.json
_STAGE_CONFIG_CACHE: dict[str, Any] | None = None


def get_usage() -> LLMUsage:
    return _USAGE


def reset_usage() -> None:
    _USAGE.__init__()


def _resolve_stage_config(stage: str | None) -> tuple[str, str]:
    """Resolve (provider, model) for a given stage from config/stage_models.json.
    Falls back to env vars LLM_PROVIDER / LLM_MODEL when stage is None or
    not found in config."""
    if stage is None:
        return os.getenv("LLM_PROVIDER", "gemini"), os.getenv("LLM_MODEL", "gemini-2.5-flash")

    global _STAGE_CONFIG_CACHE
    if _STAGE_CONFIG_CACHE is None:
        _STAGE_CONFIG_CACHE = _load_stage_config()

    stage_cfg = _STAGE_CONFIG_CACHE.get("stages", {}).get(stage, {})
    if stage_cfg:
        return stage_cfg.get("provider", "gemini"), stage_cfg.get("model", "gemini-2.5-flash")

    defaults = _STAGE_CONFIG_CACHE.get("defaults", {})
    return defaults.get("provider", "gemini"), defaults.get("model", "gemini-2.5-flash")


def _load_stage_config() -> dict[str, Any]:
    """Load stage_models.json by searching upward from this file or cwd."""
    search_dirs = [Path(__file__).resolve().parent.parent.parent, Path.cwd()]
    for base in search_dirs:
        path = base / "config" / "stage_models.json"
        if path.exists():
            try:
                return json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                return {}
    return {}


# Model pricing per 1K tokens (input / output)
_MODEL_PRICES: dict[str, tuple[float, float]] = {
    "gpt-4o": (0.0025, 0.01),
    "gpt-4o-mini": (0.00015, 0.0006),
    "claude-sonnet-4-20250514": (0.003, 0.015),
    "claude-opus-4-20250514": (0.015, 0.075),
    "gemini-2.5-flash": (0.00015, 0.0006),
    "gemini-2.5-pro": (0.00125, 0.005),
    "gemini-3.1-flash-lite": (0.000075, 0.0003),
    "gemini-2.0-flash": (0.0001, 0.0004),
}


def _is_quota_error(e: Exception) -> bool:
    """Check if an exception indicates a provider quota/rate-limit exhaustion."""
    msg = str(e).lower()
    return any(kw in msg for kw in ["resource_exhausted", "429", "quota exceeded", "rate limit", "insufficient_quota", "insufficient quota"])


def llm_call(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    response_format: str | None = None,
    max_retries: int = 3,
    stage: str | None = None,
) -> tuple[str, LLMUsage]:
    """Unified LLM call with retry, token tracking, cost estimation, and
    per-stage model routing.

    Args:
        stage: Agent stage name — used to look up provider/model from
               config/stage_models.json. Falls back to env vars when None.

    Returns (response_text, updated_usage).

    Quota/rate-limit errors are NOT retried — QuotaExceededError is raised
    immediately so the caller can save state and exit gracefully.
    """
    # Resolve provider/model from stage config (with env var fallback)
    stage_provider, stage_model = _resolve_stage_config(stage)
    provider = stage_provider
    model = model or stage_model

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            if provider == "gemini":
                text, prompt_tok, completion_tok = _call_gemini(
                    system_prompt, user_prompt, model, temperature, max_tokens, response_format
                )
            elif provider == "openai":
                text, prompt_tok, completion_tok = _call_openai(
                    system_prompt, user_prompt, model, temperature, max_tokens, response_format
                )
            elif provider == "anthropic":
                text, prompt_tok, completion_tok = _call_anthropic(
                    system_prompt, user_prompt, model, temperature, max_tokens, response_format
                )
            elif provider == "ollama":
                text, prompt_tok, completion_tok = _call_ollama(
                    system_prompt, user_prompt, model, temperature, max_tokens, response_format
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")

            cost = _estimate_cost(model, prompt_tok, completion_tok)
            _USAGE.add(prompt_tok, completion_tok, cost, model)
            return text, _USAGE

        except Exception as e:
            if _is_quota_error(e):
                raise QuotaExceededError(str(e), provider=provider) from e
            last_error = e
            if attempt < max_retries:
                delay = 2 ** (attempt - 1) * 2
                print(f"  LLM attempt {attempt} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise RuntimeError(f"LLM call failed after {max_retries} retries: {last_error}") from last_error

    raise RuntimeError(f"Unexpected: exit after retry loop. Last error: {last_error}")


def _call_ollama(
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    response_format: str | None,
) -> tuple[str, int, int]:
    from shadow_protocol.lib.providers.ollama_provider import OllamaProvider

    provider = OllamaProvider()
    return provider.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_format,
    )


def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    prices = _MODEL_PRICES.get(model)
    if prices is None:
        return 0.0
    input_price, output_price = prices
    return (prompt_tokens / 1000 * input_price) + (completion_tokens / 1000 * output_price)


def _call_gemini(
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    response_format: str | None,
) -> tuple[str, int, int]:
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY"))
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY not set")

    client = genai.Client(api_key=api_key)
    contents = [system_prompt, user_prompt]

    kwargs: dict[str, Any] = {
        "model": model,
        "contents": "\n\n".join(contents),
        "config": types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
    }

    if response_format == "json":
        kwargs["config"].response_mime_type = "application/json"

    resp = client.models.generate_content(**kwargs)

    text = resp.text or ""
    prompt_tok = 0
    completion_tok = 0
    if hasattr(resp, "usage_metadata") and resp.usage_metadata:
        prompt_tok = (resp.usage_metadata.prompt_token_count or 0)
        completion_tok = (resp.usage_metadata.candidates_token_count or 0)

    return text, prompt_tok, completion_tok


def _call_openai(
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    response_format: str | None,
) -> tuple[str, int, int]:
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    client = OpenAI(api_key=api_key)
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format == "json":
        kwargs["response_format"] = {"type": "json_object"}

    resp = client.chat.completions.create(**kwargs)
    text = resp.choices[0].message.content or ""
    prompt_tok = resp.usage.prompt_tokens if resp.usage else 0
    completion_tok = resp.usage.completion_tokens if resp.usage else 0
    return text, prompt_tok, completion_tok


def _call_anthropic(
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    response_format: str | None,
) -> tuple[str, int, int]:
    import httpx

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body: dict[str, Any] = {
        "model": model,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format == "json":
        body["response_format"] = {"type": "json_object"}

    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=body,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    text = data["content"][0]["text"]
    prompt_tok = 0
    completion_tok = 0
    if "usage" in data:
        prompt_tok = data["usage"].get("input_tokens", 0)
        completion_tok = data["usage"].get("output_tokens", 0)
    return text, prompt_tok, completion_tok
