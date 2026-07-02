"""Base class for all agents — checkpoint, retry, validation, token tracking."""

from __future__ import annotations
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable

from shadow_protocol.lib.llm import llm_call, get_usage, QuotaExceededError
from shadow_protocol.lib.file_utils import read_json, read_text, write_json, write_text
from shadow_protocol.lib.checkpoint import mark_stage_complete, is_stage_complete, get_completed_stages
from shadow_protocol.lib.schema_validator import validate_output


class AgentError(Exception):
    """Machine-readable agent error."""
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"[{code}] {message}")


class AgentBase:
    """Every agent extends this.

    Provides:
      - load_prompt(name) -> str
      - load_bible() -> dict[str, dict]
      - call_llm(system, user, schema_path=None, **kw) -> dict
      - validate_output(data, schema_rel_path) -> list[str]
      - save_checkpoint(stage_name)
      - run_with_retry(func, label)
    """

    name: str = "base"

    def __init__(self, episode_dir: str, config: dict[str, Any]):
        self.episode_dir = Path(episode_dir)
        self.root_dir = Path(config.get("root", "."))
        self.config = config

    # ── Prompt loading ──────────────────────────────────────────

    def load_prompt(self, name: str) -> str:
        path = self.root_dir / "prompts" / f"{name}.md"
        if not path.exists():
            raise AgentError("PROMPT_NOT_FOUND", f"{path} not found")
        return read_text(path)

    # ── Bible loading ────────────────────────────────────────────

    def load_bible(self) -> dict[str, dict]:
        bible_dir = self.root_dir / "bible"
        result = {}
        for f in sorted(bible_dir.glob("*.json")):
            result[f.stem] = read_json(f)
        return result

    # ── Token audit ─────────────────────────────────────────────

    def _record_audit(
        self,
        stage: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        context_files: list[str] | None = None,
        prompt_size_bytes: int = 0,
        duration_seconds: float = 0.0,
    ) -> None:
        from shadow_protocol.lib.token_audit import TokenAudit

        case_id = self.episode_dir.name
        metrics_dir = self.episode_dir.parent.parent / "projects" / case_id / "metrics"
        audit = TokenAudit(case_id, metrics_dir)
        audit.record(
            stage=stage,
            agent=self.name,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            context_files=context_files,
            prompt_size_bytes=prompt_size_bytes,
            duration_seconds=duration_seconds,
        )

    # ── LLM call with optional schema validation ─────────────────

    def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_rel_path: str | None = None,
        response_format: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stage: str | None = None,
    ) -> dict[str, Any] | tuple[str, Any]:
        """Call LLM.

        When response_format='json', parses the response as JSON, optionally
        validates against a schema, and returns the parsed dict.

        When response_format=None, returns (text, usage) for non-JSON output
        such as Markdown script sections.
        """
        import time as _time
        _start = _time.time()
        text, usage = llm_call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            stage=stage or self.name,
        )
        _duration = _time.time() - _start

        # Record to token audit from the last history entry
        if usage.history:
            last = usage.history[-1]
            self._record_audit(
                stage=stage or self.name,
                provider=last.get("model", "unknown").split(":")[0] if ":" in last.get("model", "") else os.getenv("LLM_PROVIDER", "gemini"),
                model=last.get("model", "unknown"),
                input_tokens=last.get("prompt", 0),
                output_tokens=last.get("completion", 0),
                prompt_size_bytes=len(system_prompt) + len(user_prompt),
                duration_seconds=_duration,
            )

        if response_format != "json":
            return text, usage

        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

        parsed = json.loads(text)

        if schema_rel_path:
            schema_path = self.root_dir / "templates" / "schemas" / schema_rel_path
            errors = validate_output(parsed, schema_path)
            if errors:
                raise AgentError(
                    "SCHEMA_VALIDATION_FAILED",
                    f"{schema_rel_path}: {'; '.join(errors)}",
                )

        return parsed

    # ── Output helpers ───────────────────────────────────────────

    def write_json(self, rel_path: str, data: Any) -> None:
        write_json(self.episode_dir / rel_path, data)

    def write_text(self, rel_path: str, content: str) -> None:
        write_text(self.episode_dir / rel_path, content)

    def read_json(self, rel_path: str) -> dict:
        return read_json(self.episode_dir / rel_path)

    def read_text(self, rel_path: str) -> str:
        return read_text(self.episode_dir / rel_path)

    # ── Checkpoints ──────────────────────────────────────────────

    def save_checkpoint(self, stage: str, extra: dict | None = None) -> None:
        usage = get_usage()
        meta = {
            "tokens": usage.total_tokens,
            "cost": round(usage.cost_usd, 6),
            "calls": usage.calls,
            **(extra or {}),
        }
        mark_stage_complete(self.episode_dir, stage, meta)
        print(f"  CHECKPOINT: {stage} — {usage.log_line()}")

    @property
    def completed_stages(self) -> list[str]:
        return get_completed_stages(self.episode_dir)

    def is_done(self, stage: str) -> bool:
        return is_stage_complete(self.episode_dir, stage)

    # ── Quota status ──────────────────────────────────────────────

    def save_quota_status(self, provider: str, error_message: str, failed_label: str) -> None:
        from datetime import datetime, timezone
        case_id = self.episode_dir.name
        status = {
            "provider": provider,
            "error": "daily_quota_exceeded",
            "failed_stage": self.name,
            "failed_section": failed_label,
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "resume_command": f"create-video {case_id}",
        }
        path = self.episode_dir / "quota_status.json"
        write_json(path, status)
        print(f"\nDaily {provider} quota exhausted.", file=sys.stderr)
        print(f"Resume tomorrow with:\n", file=sys.stderr)
        print(f"  {status['resume_command']}\n", file=sys.stderr)

    # ── Retry ────────────────────────────────────────────────────

    def run_with_retry(self, func: Callable, label: str = "operation", max_retries: int = 3) -> Any:
        last_exc = None
        for attempt in range(1, max_retries + 1):
            try:
                return func()
            except QuotaExceededError as e:
                self.save_quota_status(e.provider or "unknown", str(e), label)
                raise AgentError("QUOTA_EXCEEDED", f"{label}: {e}") from e
            except Exception as e:
                last_exc = e
                print(f"  {label} attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    delay = 2 ** (attempt - 1) * 2
                    print(f"  retrying in {delay}s...")
                    time.sleep(delay)
        raise AgentError("MAX_RETRIES_EXCEEDED", f"{label}: {last_exc}") from last_exc

    # ── Contract ─────────────────────────────────────────────────

    def run(self) -> int:
        raise NotImplementedError

    def fail(self, code: str, message: str) -> int:
        print(f"AGENT_ERROR: code={code} message={message}", file=sys.stderr)
        return 1
