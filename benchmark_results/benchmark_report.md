# Benchmark Report

**Generated:** 2026-07-01T20:09:52.478079+00:00
**Episodes:** 10 (1 with metrics, 0 with failures)

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Tokens | 0 |
| Total Cost | $0.000000 |
| Total Duration | 0.0s (0.00h) |
| Total LLM Calls | 0 |
| Avg Tokens/Episode | 0 |
| Avg Cost/Episode | $0.000000 |
| Avg Duration/Episode | 0.0s |
| Max Cost/Episode | $0.000000 |
| Min Cost/Episode | $0.000000 |

### Cost Distribution


**Total:** $0.000000

### Token Distribution


**Total:** 0 tokens

## By Workflow

| Workflow | Tokens | Cost | Duration | LLM Calls |
|----------|--------|------|----------|-----------|
| WF1: Script Generation | 0 | $0.000000 | 0.0s | 0 |
| WF2: Production Assets | 0 | $0.000000 | 0.0s | 0 |

## Stage Statistics

| Stage | WF | Mean Tokens | Mean Cost | Mean Duration | p95 Duration | Failure Rate | Calls |
|-------|----|-------------|-----------|---------------|--------------|--------------|-------|
| `image_prompt` | WF2: Production Assets | 0 | $0.000000 | 0.0s | 0.0s | 0.0% | 0.0 |
| `metadata` | WF2: Production Assets | 0 | $0.000000 | 0.0s | 0.0s | 0.0% | 0.0 |
| `outline` | WF1: Script Generation | 0 | $0.000000 | 0.0s | 0.0s | 0.0% | 0.0 |
| `production_package` | WF1: Script Generation | 0 | $0.000000 | 0.0s | 0.0s | 0.0% | 0.0 |
| `scene_breakdown` | WF2: Production Assets | 0 | $0.000000 | 0.0s | 0.0s | 0.0% | 0.0 |
| `script` | WF1: Script Generation | 0 | $0.000000 | 0.0s | 0.0s | 0.0% | 0.0 |
| `script_review` | WF1: Script Generation | 0 | $0.000000 | 0.0s | 0.0s | 0.0% | 0.0 |
| `thumbnail` | WF2: Production Assets | 0 | $0.000000 | 0.0s | 0.0s | 0.0% | 0.0 |
| `video_prompt` | WF2: Production Assets | 0 | $0.000000 | 0.0s | 0.0s | 0.0% | 0.0 |
| `voiceover` | WF2: Production Assets | 0 | $0.000000 | 0.0s | 0.0s | 0.0% | 0.0 |

## Episode Comparison

| Episode | Tokens | Cost | Duration | Stages | Failures |
|---------|--------|------|----------|--------|----------|
| case_001 | 0 | $0.000000 | 0.0s | 10 | 0 |

## Variance Analysis

Stages with the highest duration variance — potential optimization targets:

| Stage | Mean Duration | Std Dev | CV (%) |
|-------|--------------|---------|--------|
| `image_prompt` | 0.0s | 0.0s | 0.0% |
| `metadata` | 0.0s | 0.0s | 0.0% |
| `outline` | 0.0s | 0.0s | 0.0% |
| `production_package` | 0.0s | 0.0s | 0.0% |
| `scene_breakdown` | 0.0s | 0.0s | 0.0% |

## Failures

_No failures recorded across all episodes._

## Optimization Recommendations

1. **Reduce image_prompt costs** ($0.000000)
   - Consider: prompt compression, shorter outputs, cheaper model variant.
   - Potential savings: ~— of total cost.

2. **Optimize image_prompt duration** (mean 0.0s)
   - Consider: parallel execution, timeout tuning, LLM response streaming.
   - Impact: reduces per-episode pipeline time.

## Raw Data

- `benchmark_results/aggregate.json` — Full metrics
- `benchmark_results/per_episode.json` — Per-episode summaries
- `benchmark_results/per_stage.json` — Per-stage statistics
- `benchmark_results/durations.csv` — Duration CSV for external analysis
- `benchmark_results/environment.json` — Runtime environment metadata
