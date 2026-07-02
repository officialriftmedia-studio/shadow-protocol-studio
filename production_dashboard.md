# Production Dashboard

> Real-time health and performance tracking for the Shadow Protocol Studio pipeline.
> Auto-generated from `benchmark_results/aggregate.json` after each benchmark run.

---

## Pipeline Health

| Indicator | Status | Current Value | Threshold | Trend |
|-----------|--------|---------------|-----------|-------|
| **Pipeline Success Rate** | 🟢 | — | > 90% | — |
| **Avg Duration per Episode** | ⏳ | — | < 30 min | — |
| **Avg Cost per Episode** | 💰 | — | < $1.00 | — |
| **Avg Tokens per Episode** | 📝 | — | < 100k | — |
| **Render Failure Rate** | 🎬 | — | < 5% | — |
| **Stage Failure Rate** | ⚠️ | — | < 2% | — |
| **FFmpeg Render Time (avg)** | ⏱️ | — | < 10 min | — |
| **Disk Usage (projects/)** | 💾 | — | < 5 GB | — |

---

## Quick Stats (All Episodes)

| Metric | Value | Per-Episode Avg |
|--------|-------|-----------------|
| **Total Episodes** | `N` | — |
| **Total Pipeline Time** | — | — |
| **Total Cost** | — | — |
| **Total Tokens** | — | — |
| **Total LLM Calls** | — | — |
| **Total Render Time** | — | — |

---

## Cost by Workflow

```
WF1: Script Generation    ████████████████░░░░░░░░░░░░  XX.X%
WF2: Production Assets    ██████████░░░░░░░░░░░░░░░░░░  XX.X%
WF3: Media Generation     ██████░░░░░░░░░░░░░░░░░░░░░░  XX.X%
WF4: Video Assembly       ████░░░░░░░░░░░░░░░░░░░░░░░░  XX.X%
WF5: Publishing           ██░░░░░░░░░░░░░░░░░░░░░░░░░░  XX.X%
```

| Workflow | Cost | % of Total | Duration |
|----------|------|-----------|----------|
| WF1: Script Generation | — | — | — |
| WF2: Production Assets | — | — | — |
| WF3: Media Generation | — | — | — |
| WF4: Video Assembly | — | — | — |
| WF5: Publishing | — | — | — |

---

## Cost by Episode

| Episode | Cost | Tokens | Duration | Success |
|---------|------|--------|----------|---------|
| `case_001` | — | — | — | 🟢 |
| `case_002` | — | — | — | 🟢 |
| `case_003` | — | — | — | 🟢 |
| `case_004` | — | — | — | 🟢 |
| `case_005` | — | — | — | 🟢 |
| `case_006` | — | — | — | 🟢 |
| `case_007` | — | — | — | 🟢 |
| `case_008` | — | — | — | 🟢 |
| `case_009` | — | — | — | 🟢 |
| `case_010` | — | — | — | 🟢 |

**Cost Range:** $X.XXXX — $Y.YYYY

---

## Stage Performance

### Fastest Stages (avg duration)
| # | Stage | Mean | p95 |
|---|-------|------|-----|
| 1 | — | — | — |
| 2 | — | — | — |
| 3 | — | — | — |

### Slowest Stages (avg duration)
| # | Stage | Mean | p95 |
|---|-------|------|-----|
| 1 | — | — | — |
| 2 | — | — | — |
| 3 | — | — | — |

### Most Expensive Stages (avg cost)
| # | Stage | Mean Cost | % of Total |
|---|-------|-----------|-----------|
| 1 | — | — | — |
| 2 | — | — | — |
| 3 | — | — | — |

### Highest Variance Stages (std dev)
| # | Stage | Std Dev | CV |
|---|-------|---------|-----|
| 1 | — | — | — |
| 2 | — | — | — |
| 3 | — | — | — |

---

## Render Performance

| Metric | Value |
|--------|-------|
| **Total Render Time (all episodes)** | — |
| **Avg Render Time per Episode** | — |
| **Slowest Render** | — |
| **Fastest Render** | — |
| **Avg Scenes per Episode** | — |
| **Avg Render Time per Scene** | — |
| **Total FFmpeg Commands Executed** | — |
| **FFmpeg Failure Rate** | — |

### Render Time by Episode
| Episode | Scenes | Render Duration | Per-Scene Avg | Slowest Motion |
|---------|--------|----------------|---------------|----------------|
| `case_001` | — | — | — | — |
| `case_002` | — | — | — | — |

---

## Token Usage

### Token Distribution by Workflow
```
WF1: Script Generation    ████████████████████████████  XX.X%
WF2: Production Assets    ██████████████░░░░░░░░░░░░░░  XX.X%
WF3: Media Generation     ░░░░░░░░░░░░░░░░░░░░░░░░░░░░  XX.X%
WF4: Video Assembly       ░░░░░░░░░░░░░░░░░░░░░░░░░░░░  XX.X%
WF5: Publishing           ░░░░░░░░░░░░░░░░░░░░░░░░░░░░  XX.X%
```

| Stage | Mean Tokens | Mean Cost |
|-------|-------------|-----------|
| `production_package` | — | — |
| `outline` | — | — |
| `script` | — | — |
| `script_review` | — | — |
| `scene_breakdown` | — | — |
| `image_prompt` | — | — |
| `video_prompt` | — | — |
| `voiceover` | — | — |
| `metadata` | — | — |
| `thumbnail` | — | — |
| `image_generator` | — | — |
| `voice_generator` | — | — |
| `timeline_builder` | — | — |
| `render_builder` | — | — |
| `render_executor` | — | — |
| `publish_package_builder` | — | — |
| `quality_control` | — | — |
| `release_manager` | — | — |

---

## Failure Tracking

| Episode | Stage | Error Code | Severity | Resolved |
|---------|-------|-----------|----------|----------|
| — | — | — | — | — |

### Failure Rate by Stage
| Stage | Episodes | Failures | Rate |
|-------|----------|----------|------|
| — | — | — | — |

---

## Trend Tracking (Over Multiple Benchmark Runs)

| Run # | Date | Avg Cost | Avg Duration | Success Rate | Notes |
|-------|------|----------|-------------|-------------|-------|
| 1 | — | — | — | — | Baseline |
| 2 | — | — | — | — | — |
| 3 | — | — | — | — | — |

---

## Cost Projection

| Volume Scenario | Cost per Episode | Total Cost | Time |
|----------------|-----------------|------------|------|
| **10 Episodes** (1 season) | — | — | — |
| **50 Episodes** (5 seasons) | — | — | — |
| **100 Episodes** (ongoing) | — | — | — |

---

## Alerts & Anomalies

| Timestamp | Type | Message | Action |
|-----------|------|---------|--------|
| — | — | — | — |

---

## Data Sources

| Artifact | Path | Updates |
|----------|------|---------|
| Aggregate metrics | `benchmark_results/aggregate.json` | After each benchmark run |
| Per-stage stats | `benchmark_results/per_stage.json` | After each benchmark run |
| Per-episode data | `benchmark_results/per_episode.json` | After each run |
| Duration CSV | `benchmark_results/durations.csv` | After each run |
| Environment info | `benchmark_results/environment.json` | At benchmark start |
| Full benchmark report | `benchmark_results/benchmark_report.md` | After each run |

---

## Usage

```bash
# Generate dashboard data
python benchmark_scripts/collect_metrics.py

# Update this dashboard
python benchmark_scripts/benchmark_report.py
```

> **Note**: Replace `—` placeholders with actual values after running benchmark.
> This file is meant to be kept in version control and updated after each benchmark run.
