# PHASE 4 — Gemini Quota Impact

**Case:** case_001
**Date:** 2026-07-02

## Current Environment

| Setting | Value |
|---------|-------|
| Provider | `gemini` |
| Model | `gemini-2.5-flash` |
| Tier | Free (20 req/day) |

## Historical Usage (from .checkpoint.json)

| Stage | Calls | Tokens |
|-------|-------|--------|
| production_package | 1 | 2,398 |
| outline | 1 | 3,055 |
| script_review | 3 | 27,669 |
| scene_breakdown | 5 | 19,131 |
| image_prompt (failed) | 0 | 0 |
| **Total used** | **10** | **46,253** |

(Note: The `script` stage was skipped due to file existence, so it made 0 Gemini calls.)

## Remaining Downstream Requirements (Unique Scenes)

With `config/stage_models.json` routing:

| Stage | Provider | Model | Calls | Notes |
|-------|----------|-------|-------|-------|
| **asset_package** | **ollama** | qwen3:14b | **0 Gemini** | Routed to local |
| **voiceover** | **ollama** | qwen3:14b | **0 Gemini** | Routed to local |
| image_generator | N/A | N/A | 0 | Midjourney/Imagen (no LLM) |
| voice_generator | N/A | N/A | 0 | ElevenLabs/GTTS (no LLM) |

**Zero additional Gemini calls needed** if Ollama is available and working.

## If Ollama is NOT available (Gemini fallback for everything):

With 16 unique scenes:

| Stage | Estimated Calls | Estimated Tokens |
|-------|----------------|-----------------|
| asset_package | 1 | ~8,000 |
| voiceover | 6 (sections) | ~12,000 |
| **Total remaining** | **7** | **~20,000** |

| Metric | Value |
|--------|-------|
| Calls needed | 7 |
| Calls remaining (free tier) | 10 (20 - 10 used) |
| Can run today? | ❌ (quota already exhausted — image_prompt hit 429) |
| Can run tomorrow? | ✅ (10 remaining > 7 needed) |
| Days on free tier | ~2 days (today's quota + tomorrow's quota) |

## Cost Analysis (Gemini 2.5-flash: $0.00015/1K input, $0.0006/1K output)

| Scenario | Cost |
|----------|------|
| Already spent | ~$0.0101 |
| Remaining (Gemini fallback) | ~$0.005–0.010 |
| **Total (Gemini)** | **~$0.015–0.020** |
| Remaining (Ollama) | **$0.00** |
| **Total (Ollama routing)** | **~$0.0101** |

## Recommendation

**Use Ollama for remaining stages.** `asset_package` and `voiceover` are already configured to route to `ollama/qwen3:14b` in `config/stage_models.json`. If Ollama is running locally, zero Gemini calls are needed to complete case_001.

Verify Ollama is running:
```bash
curl http://localhost:11434/api/tags
```
