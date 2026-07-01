"""LLM abstraction layer — single call interface for all providers."""

from __future__ import annotations
import os
from typing import Any


def llm_call(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    response_format: str | None = None,
) -> str:
    """Unified LLM call. Routes to the configured provider.

    Args:
        system_prompt: System-level instructions
        user_prompt: User message content
        model: Model override (default from config)
        temperature: Sampling temperature
        max_tokens: Maximum output tokens
        response_format: "json" or None

    Returns:
        Model response text

    Raises:
        RuntimeError: If the LLM call fails after retries
    """
    provider = os.getenv("LLM_PROVIDER", "openai")
    model = model or os.getenv("LLM_MODEL", "gpt-4o")

    if provider == "openai":
        return _call_openai(system_prompt, user_prompt, model, temperature, max_tokens, response_format)
    elif provider == "anthropic":
        return _call_anthropic(system_prompt, user_prompt, model, temperature, max_tokens, response_format)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def _call_openai(
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    response_format: str | None,
) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    kwargs = {
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
    return resp.choices[0].message.content or ""


def _call_anthropic(
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    response_format: str | None,
) -> str:
    import httpx

    api_key = os.getenv("ANTHROPIC_API_KEY")
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
    return data["content"][0]["text"]
