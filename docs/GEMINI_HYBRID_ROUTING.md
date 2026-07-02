# Gemini Hybrid Routing

## Overview

Shadow Protocol Studio uses a **hybrid routing strategy** to distribute LLM calls across different Gemini models based on task type. This reduces dependence on the Gemini 2.5 Flash free-tier quota (20 RPD) by routing extraction/utility tasks to Gemini 3.1 Flash Lite (500 RPD).

## Routing Rules

| Stage Type | Stages | Model | RPD Quota |
|-----------|--------|-------|-----------|
| Creative writing | `production_package`, `outline`, `script` | `gemini-2.5-flash` | 20 |
| Extraction / Formatting | `script_review`, `scene_breakdown`, `asset_package`, `metadata`, `thumbnail` | `gemini-3.1-flash-lite` | 500 |
| Voiceover | `voiceover` | `qwen3:14b` (Ollama, local) | Unlimited |
| Disabled | `image_generator`, `voice_generator` | provider: `none` | N/A |

## Configuration

### `config/stage_models.json`

Defines per-stage provider/model overrides. The pipeline reads this file at runtime to determine which model to invoke for each stage.

```json
{
  "defaults": {
    "provider": "gemini",
    "model": "gemini-2.5-flash"
  },
  "stages": {
    "production_package": { "provider": "gemini", "model": "gemini-2.5-flash" },
    "script_review":     { "provider": "gemini", "model": "gemini-3.1-flash-lite" },
    "voiceover":         { "provider": "ollama", "model": "qwen3:14b" },
    "image_generator":   { "provider": "none" }
  }
}
```

### `config/quota_limits.json`

Per-model RPD/RPM/TPM limits used by `QuotaManager` for tracking and estimation.

### `config/models.json`

Full model registry with pricing blocks and capability metadata.

## Quota Tracking

`QuotaManager` tracks usage **per model** (not per provider). Each model's call count and token usage are stored independently in `.quota_state.json`.

### Key operations

- `record_call(model, input_tokens)` — increment usage for a model
- `get_usage(model)` — get remaining quota for a model
- `estimate_episode(scene_count)` — estimate per-model usage for a full episode

## CLI Commands

### Estimate

```bash
create-video estimate
```

Shows per-model breakdown of estimated calls, remaining quota, and whether a full episode can run.

### Benchmark Models

```bash
create-video benchmark-models case_001
```

Runs the pipeline in dry-run mode and reports per-model quota status after execution.

### Quota Status

```bash
create-video quota
```

Displays quota exhaustion events and resumable episodes.

## Migration Guide

### From single-model to hybrid routing

1. Update `config/stage_models.json` to assign models per stage (see above)
2. Ensure `config/quota_limits.json` has entries for all models in use
3. Update `config/models.json` if adding new models
4. Verify routing with `create-video estimate`
5. Run a dry-run to confirm no stage errors: `create-video benchmark-models case_dry_run`

### Adding a new stage

1. Add entry to `config/stage_models.json` under `stages`
2. Add estimated call count to `QuotaManager.estimate_episode()` in `quota_manager.py`
3. Add pricing to `_MODEL_PRICES` in `llm.py` (if a new model)
4. Add quota limits to `config/quota_limits.json`

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Script routed to flash-lite | `stage_models.json` misconfigured | Check `script` entry points to `gemini-2.5-flash` |
| Quota estimate shows wrong model | `_get_stage_model_map()` not reading config | Verify `config/stage_models.json` exists and is valid JSON |
| QuotaExceededError on flash-lite | RPD exhausted (500/day) | Wait for daily reset or reduce scene count |
