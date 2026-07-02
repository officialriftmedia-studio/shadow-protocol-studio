# PHASE 5 — Production Recommendation

**Case:** case_001
**Date:** 2026-07-02

---

## Option Analysis

### OPTION A: Continue pipeline as-is with 31 scenes

| Factor | Assessment |
|--------|------------|
| Feasible | Technically yes |
| Asset waste | **High** — 15 duplicate image/video prompts, duplicate render |
| Render time | ~33 min (2x necessary) |
| Quality impact | **Negative** — duplicate scenes would render same content twice |
| Verdict | ❌ **NOT recommended** |

### OPTION B: Regenerate scene breakdown from scratch

| Factor | Assessment |
|--------|------------|
| Effort | High — requires new LLM calls, may hit Gemini quota |
| Risk | New breakdown may differ from currently reviewed script |
| Quality impact | Unknown — could be better or worse than current unique scenes |
| Verdict | ❌ **NOT recommended** (current unique scenes are good quality) |

### OPTION C: Switch remaining stages to Ollama

| Factor | Assessment |
|--------|------------|
| Effort | Zero — already configured in `config/stage_models.json` |
| Risk | Requires Ollama running locally with `qwen3:14b` model pulled |
| Cost savings | $0.00 for remaining stages |
| Verdict | ✅ **RECOMMENDED** (already configured, just needs verification) |

### OPTION D: Prune duplicates + continue

| Factor | Assessment |
|--------|------------|
| Effort | **Low** — remove 15 duplicate entries from JSON array |
| Risk | None — unique scenes are high quality and match reviewed script |
| Asset waste | **Eliminated** — only 16 unique scenes processed |
| Render time | ~17 min (target range) |
| Verdict | ✅ **RECOMMENDED** |

---

## RECOMMENDATION: OPTION D + OPTION C

Execute both:

**Step 1 — Prune duplicates from scene_breakdown.json**
Remove scenes 16–30 from the JSON array. Keep scenes 1–15 and scene 31.
This reduces 31 → 16 unique scenes, all within the 12–18 optimization target.

**Step 2 — Verify Ollama is running**
```bash
curl http://localhost:11434/api/tags
```
Expected: `qwen3:14b` listed. If not: `ollama pull qwen3:14b`

**Step 3 — Resume pipeline**
```bash
create-video case_001 --from scene_breakdown --mode production
```
Projected stages: `asset_package` → `voiceover` → `image_generator` → `voice_generator` → `timeline_builder` → `render_builder` → `render_executor`

**Step 4 — If quota exceeded on Gemini stages**
`script` and `script_review` are already complete. All remaining stages route to Ollama. No Gemini quota issues expected.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Ollama not running | Low | High (Gemini fallback needed) | Pre-check with `curl` |
| qwen3:14b not pulled | Low | Medium (pull is fast) | `ollama pull qwen3:14b` |
| Duplicate pruning errors | Low | Medium (wrong scenes removed) | Manual verification before commit |
| Gemini quota on prune re-run | None | N/A | Pruning is manual, not regeneration |
