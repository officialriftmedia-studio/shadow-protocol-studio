# Production Validation Plan

## Objectives

1. **Generate 10 complete episodes** through the full pipeline (Workflows #1–#5).
2. **Benchmark token usage** per stage and per episode to establish baselines.
3. **Benchmark cost** per episode and identify cost drivers.
4. **Benchmark render times** (FFmpeg) to gauge video assembly throughput.
5. **Identify failure points** — stages with the highest failure rate, longest duration, or most variance.
6. **Produce optimization recommendations** with data-driven evidence.

## Episode Generation Plan

### Episode Concepts (10 diverse episodes)

| # | ID | Title | Protagonist | Central Question | Unique Angle |
|---|-----|-------|-------------|-----------------|--------------|
| 1 | `case_001` | The Ghost in the Machine | Elena Vasquez (Cybersecurity) | Who erased my identity and replaced it with a dead woman's? | Existing blueprint — baseline benchmark |
| 2 | `case_002` | The Dead Letter Office | Marcus Cole (Postal Inspector) | Why are classified letters arriving with postmarks from before the sender died? | Physical mail as data vector |
| 3 | `case_003` | The Sleepers Protocol | Dr. Aisha Sharma (Neurologist) | Why do 47 coma patients across 12 cities share the same impossible dream? | Medical / neural angle |
| 4 | `case_004` | The Carbon Copy | David Park (Forensic Accountant) | Why do 5 competing companies have identical off-book ledgers written by the same dead accountant? | Financial conspiracy |
| 5 | `case_005` | The Hollow Men | Father Gabriel Torres (Priest) | Why does the confessional's voice-recognition system keep flagging sins that haven't been committed yet? | Faith / surveillance intersection |
| 6 | `case_006` | The Vanishing Point | Nina Okafor (Archivist) | Why do historical photographs keep shifting — and who is editing the past in real-time? | Media manipulation / deepfake history |
| 7 | `case_007` | The Echo Chamber | Leo Chen (Acoustic Engineer) | Who is hiding messages in the background noise of every government building in the capital? | Audio steganography |
| 8 | `case_008` | The Fence | Sarah Kessler (Border Patrol) | Why does the biometric database show 2 million more crossings than any human recorded? | Border / immigration system |
| 9 | `case_009` | The Zero Day | Jamal Brooks (High School Teacher) | Why did a 16-year-old student predict a natural disaster with 100% accuracy using only public data? | Crowd-sourced intelligence / prodigy |
| 10 | `case_010` | The Long Game | Dr. Helena Ross (Historian) | Why do 200-year-old Masonic lodge records perfectly predict modern stock market crashes? | Historical pattern / time-spanning conspiracy |

### Diversity Criteria

- **Gender balance**: 5 female, 4 male, 1 non-binary protagonists
- **Profession variety**: Tech, medical, finance, religious, archival, engineering, law enforcement, education, historical
- **Antagonist systems**: Cyber, physical, neural, financial, institutional, temporal, acoustic, bureaucratic, predictive, historical
- **Tone variation**: Paranoid, clinical, atmospheric, urgent, meditative, forensic, conspiratorial, intimate, epic, philosophical

## Benchmark Methodology

### Token Benchmarking

```
For each stage in every episode:
  - Record prompt_tokens and completion_tokens from metrics/*.json
  - Aggregate: total_tokens = sum(prompt_tokens + completion_tokens)
  - Compute: min, max, mean, median, p95, stddev across 10 episodes
```

### Cost Benchmarking

```
Cost_per_stage = tokens * model_rates (from config/models.json)
  - Input cost  = prompt_tokens / 1000 * cost_per_1k_input(gpt-4o)
  - Output cost = completion_tokens / 1000 * cost_per_1k_output(gpt-4o)
  
Cost_per_episode = sum(cost_per_stage for all stages)
Cost_per_workflow = {WF1: script stages, WF2: scene/asset stages, WF3: gen stages, WF4: render stages, WF5: publish stages}
```

### Render Time Benchmarking

```
For render_executor stage:
  - Total render duration_seconds (from metrics)
  - Per-scene render time = duration_seconds / scene_count
  - FFmpeg command wall-clock time per scene
  - Compare: slow_zoom_in vs static vs pan camera motions
  - Compare: fade vs crossfade vs cut transitions
```

### Environment Recording

Each benchmark run must record:

| Variable | Source |
|----------|--------|
| Python version | `python --version` |
| OS | `uname -a` |
| CPU cores | `nproc` |
| RAM | `free -g` |
| Disk type | `lsblk -d -o name,rota` |
| FFmpeg version | `ffmpeg -version` |
| Timestamp | ISO 8601 |
| Git commit hash | `git rev-parse HEAD` |
| LLM provider | config: `LLM_PROVIDER` |
| LLM model | config: `LLM_MODEL` |

## Execution Protocol

### Phase 1: Dry-Run Validation

```bash
# Verify all episodes can be discovered and the pipeline accepts each case
for i in $(seq -w 1 10); do
  create-video "case_0${i}" --dry-run
done
```

**Pass criteria**: All 10 dry-runs exit with code 0.

### Phase 2: Serial Execution

```bash
# Execute each episode in isolation, collect metrics
for i in $(seq -w 1 10); do
  create-video "case_0${i}"
  # Copy metrics to benchmark archive
  cp -r "projects/case_0${i}/metrics" "benchmark_results/case_0${i}/"
done
```

**Pass criteria**: Episodes 1–8 exit 0. Episodes 9–10 may fail on edge conditions.

### Phase 3: Parallel Stress Test

```bash
# Run 3 episodes concurrently to test resource contention
create-video case_001 & create-video case_002 & create-video case_003 & wait
```

**Pass criteria**: No FFmpeg or LLM provider race conditions. Total time < sum of individual times.

### Phase 4: Resume & Recovery

```bash
# Start an episode, kill it mid-pipeline, resume
create-video case_002 &
PID=$!
sleep 30
kill $PID
create-video case_002 --from render_builder
```

**Pass criteria**: Pipeline resumes at the correct stage, produces identical output to a clean run.

### Phase 5: Force Re-Run

```bash
# Verify --force produces identical metrics (within tolerance)
create-video case_001 --force
```

**Pass criteria**: Metrics from re-run match first run within 5% tolerance.

## Data Collection Schema

### Per-Episode Metrics File

Each episode produces `metrics/{stage}.json` per stage with:

```json
{
  "stage": "production_package",
  "status": "success",
  "duration_seconds": 12.34,
  "prompt_tokens": 1500,
  "completion_tokens": 850,
  "total_tokens": 2350,
  "llm_calls": 1,
  "cost_usd": 0.0345,
  "output_files": ["production_package.json"]
}
```

### Benchmark Aggregation

A `benchmark_results/aggregate.json` is computed after all 10 runs:

```json
{
  "meta": {
    "timestamp": "2026-07-01T00:00:00Z",
    "git_commit": "abc123",
    "llm_model": "gpt-4o",
    "total_episodes": 10
  },
  "summary": {
    "total_cost_usd": 5.2345,
    "total_tokens": 850000,
    "total_pipeline_seconds": 15420,
    "total_render_seconds": 8900,
    "success_rate": 0.9
  },
  "per_stage": {
    "production_package": {
      "mean_tokens": 2150,
      "mean_cost": 0.031,
      "p95_duration": 45.2,
      "failure_rate": 0.0
    }
  },
  "per_episode": {
    "case_001": {
      "total_cost": 0.4231,
      "total_tokens": 78200,
      "duration": 1230
    }
  }
}
```

## Failure Point Identification

### Categories

| Category | Detection Method | Example |
|----------|-----------------|---------|
| **LLM Provider Errors** | Non-zero exit from agent, log contains API error | Rate limit, timeout, model overload |
| **Schema Validation Failures** | Agent logs contain `SCHEMA_VALIDATION_FAILED` | LLM returns malformed JSON |
| **Asset Not Found** | Render or publish stage fails with missing asset | Image generator created wrong filename |
| **FFmpeg Failures** | `render_executor` returns non-zero, `render_manifest.json` has `failed_scenes > 0` | Invalid filter string, codec not found |
| **Checkpoint Corruption** | Pipeline skips stages incorrectly | `.checkpoint.json` has inconsistent state |
| **Cost Anomaly** | Stage cost > 3 standard deviations from mean | Unexpectedly high token usage |

### Scoring

```
Failure Severity:
  Critical = Pipeline stops, requires manual intervention
  Major    = Pipeline continues, output degraded
  Minor    = Warning, output unaffected
```

### Tracking

A `failure_log.csv` in `benchmark_results/`:

```csv
timestamp,episode,stage,error_code,message,severity
2026-07-01T00:01:23Z,case_004,outline,SCHEMA_VALIDATION_FAILED,Missing required field 'acts',major
```

## Optimization Recommendations Framework

Each recommendation follows this template:

```markdown
### REC-001: Description

**Evidence**: Metric X shows Y% overhead compared to baseline.
**Impact**: Reduces Z by W%.
**Effort**: Low / Medium / High
**Risk**: Low / Medium / High
**Implementation**: Brief description of the change.
```

### Areas of Investigation

1. **LLM prompt optimization** — Reduce token counts per stage
2. **Parallel agent execution** — Run independent stages concurrently
3. **FFmpeg filter optimization** — Faster camera motion rendering
4. **Checkpoint granularity** — Resume at scene-level rather than stage-level
5. **Provider caching** — Increase cache hit rate for image/voice generation
6. **Model selection** — Use cheaper models for specific stages
7. **Concurrent scene rendering** — Render scenes in parallel (already ThreadPoolExecutor 4)

## Deliverables

| Artifact | Location | Format |
|----------|----------|--------|
| 10 episode directories | `projects/case_001` … `projects/case_010` | Directory with all pipeline outputs |
| Aggregate benchmark report | `benchmark_results/aggregate.json` | JSON with per-stage and per-episode stats |
| Dashboard | `production_dashboard.md` | Markdown dashboard |
| Episode scorecards | `benchmark_results/scorecards/case_NNN.md` | Per-episode markdown |
| Failure log | `benchmark_results/failure_log.csv` | CSV |
| Optimization report | `benchmark_results/optimization_report.md` | Markdown with ranked recommendations |

## Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Dry-run validation | 15 min | Blueprint JSONs created |
| Phase 2: Serial execution | 4–8 hours | LLM provider availability |
| Phase 3: Stress test | 1 hour | Phase 2 complete |
| Phase 4: Resume testing | 30 min | Phase 2 complete |
| Phase 5: Force re-run | 1 hour | Phase 2 complete |
| Analysis & reporting | 2 hours | All phases complete |
| **Total** | **~12 hours** | |

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM rate limiting | Medium | High | Use `--dry-run` for LLM-independent testing; stagger episode launches |
| Disk space exhaustion | Low | High | Monitor `projects/` with `du -sh`; set `MAX_PROJECTS_MB` alert |
| FFmpeg OOM on large renders | Medium | Medium | Render with `--max-scenes 4` in stress test |
| Checkpoint state corruption | Low | Critical | Backup `.checkpoint.json` before each run |
| Benchmark variance from model non-determinism | High | Low | Run each episode 3 times, report mean ± stddev |

## Glossary

| Term | Definition |
|------|------------|
| **Stage** | One step in the pipeline (e.g., `outline`, `render_builder`) |
| **Workflow** | Group of related stages (WF1: Script, WF2: Assets, WF3: Media, WF4: Video, WF5: Publish) |
| **Metrics** | Per-stage JSON files recording tokens, cost, duration |
| **Blueprint** | Episode concept JSON — the starting input |
| **Checkpoint** | `.checkpoint.json` — tracks completed stages for resume |
| **p95** | 95th percentile — the value below which 95% of observations fall |
