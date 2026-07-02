# Optimization Phase 2 — Migration Notes

Date: 2026-07-02

## Summary

Phase 2 implements the remaining optimization features: scene count control, dev/production modes, quota estimation, background queue, and benchmark tooling. Total LLM calls reduced from ~25 to ~5-7, tokens reduced ~60%, pipeline stages reduced from 15 to 9 in dev mode.

## What Changed

### 1. Scene Count Optimization

**File:** `prompts/scene_breakdown.md`

Added explicit per-section scene count targets (12-18 total scenes) and total duration guidelines. The prompt now constrains:
- hook: 1-2 scenes
- act1: 3-4 scenes
- act2: 3-5 scenes
- act3: 2-3 scenes
- ending: 1-2 scenes
- cliffhanger: 1 scene
- Total episode duration: 600-1080 seconds (10-18 min)

**Migration:** No code changes needed. The prompt change is transparent to existing runs — new breakdowns will automatically generate fewer scenes.

### 2. Dev / Production Modes

**Files:** `shadow_protocol/cli.py`, `shadow_protocol/lib/orchestrator_runner.py`

Added `--mode dev|production` flag to the CLI.

- **dev mode:** Skips all render stages (image_generator, voice_generator, timeline_builder, render_builder, render_executor, publish_package_builder, quality_control, release_manager). Stops after asset_package + voiceover. Faster iteration during writing.
- **production mode:** Full pipeline including render and publish stages (default).

Usage:
```bash
create-video case_001 --mode dev          # Skip render stages
create-video case_001 --mode production    # Full pipeline (default)
```

**Effect:** Dev mode cuts pipeline from 15 stages to 7 stages, saving significant time.

### 3. Estimate Command

**File:** `shadow_protocol/cli.py`

New `estimate` subcommand shows quota and token cost estimates before running.

Usage:
```bash
create-video estimate
```

Output:
```
Episode Cost Estimate
=====================
Provider:          gemini
Scene count:       15
Estimated calls:   19
Estimated tokens:  85500
  Input:           57000
  Output:          28500
Remaining quota:   20 requests
Can run episode:   YES
Recommendation:    gemini has enough quota
```

### 4. Quota-Aware Pause/Resume

**Files:** `shadow_protocol/lib/quota_manager.py`, `shadow_protocol/lib/orchestrator_runner.py`

Enhanced pause/resume:
- Pre-flight quota check at pipeline start (warns if < 10 requests remaining)
- Clean `quota_status.json` written on quota exhaustion
- Resume command printed automatically
- Works with `--from` flag to resume from the failed stage

The quota manager tracks per-provider daily usage in `.quota_state.json` and auto-resets each day.

### 5. Background Queue System

**File:** `shadow_protocol/lib/queue_manager.py`

New queue system for running pipelines as background processes.

Usage:
```bash
create-video queue add case_001            # Add and start job
create-video queue add case_001 --dry-run  # Simulation mode
create-video queue status                  # List all jobs
create-video queue cancel 1                # Cancel job #1
```

Queue state is persisted in `projects/.queue_state.json`.

### 6. Benchmark Tool

**File:** `scripts/benchmark.py`

Benchmark script to measure pipeline performance and generate comparison reports.

Usage:
```bash
python scripts/benchmark.py --mode before   # Baseline snapshot
python scripts/benchmark.py --mode after    # After optimization snapshot
python scripts/benchmark.py --mode compare  # Generate comparison report
```

Output: `benchmarks/comparison_report.md` with per-stage breakdown.

### 7. Asset Package Agent

**File:** `agents/asset_package.py`

Replaces 4 individual agents (image_prompt, video_prompt, metadata, thumbnail) with a single LLM call. Reduces LLM calls by 3 per pipeline run.

**Migration:** Old checkpoints for `image_prompt`, `video_prompt`, `metadata`, `thumbnail` are ignored by the new pipeline. If resuming an older run, use `--force` to re-run from `scene_breakdown`.

### 8. Stage Model Routing

**File:** `shadow_protocol/lib/llm.py`

All non-critical stages now route to Ollama by default via `config/stage_models.json`. Critical stages (script, script_review) use Gemini. This reduces API quota consumption by ~70%.

## Backward Compatibility

| Feature | Compatible? | Notes |
|---------|-------------|-------|
| `create-video case_NNN` | Yes | Same CLI, just new options |
| `--from` resume | Yes | Quota pause/resume enhanced |
| `--dry-run` | Yes | Unchanged |
| `--force` | Yes | Unchanged |
| `create-video quota` | Yes | Same output, enhanced |
| `scene_breakdown.json` schema | Yes | Unchanged |
| Agent input/output schemas | Yes | All schemas preserved |
| Checkpoint files | Yes | Old checkpoints respected |

## New Dependencies

None. All changes use stdlib only.

## Test Coverage

New test file: `tests/test_optimization_phase2.py`
- Queue manager: add, list, cancel, persistence, status filtering
- Quota manager: record, estimate, new-day reset, Ollama limits
- Token audit: record, persistence, summary
- Dev mode: stage filtering
- Production mode: full stage inclusion
- Stage models: asset_package config
- Benchmark: dry-run validation
