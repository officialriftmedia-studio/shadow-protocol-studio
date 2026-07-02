# PHASE 3 — Pipeline Readiness

**Case:** case_001
**Date:** 2026-07-02

## Stage Dependency Verification

### Remaining stages (effective STAGE_ORDER after scene_breakdown):

| # | Stage | Inputs | Exists? | Outputs | Ready? |
|---|-------|--------|---------|---------|--------|
| 1 | **asset_package** | `scene_breakdown.json` | ✅ | `image_prompts.json`, `video_prompts.json`, `youtube_metadata.json`, `thumbnail_prompt.json` | ⚠️ File has 31 scenes (15 dupes) |
| | | `production_package.json` | ✅ | | |
| 2 | **voiceover** | `script/*.md` | ✅ (7 files) | `voiceover_segments.json` | ✅ |
| | | `scene_breakdown.json` | ✅ | | |
| 3 | **image_generator** | `image_prompts.json` | ❌ (not generated yet) | `assets/images/` | ❌ |
| 4 | **voice_generator** | `voiceover_segments.json` | ❌ (not generated yet) | `assets/voice/` | ❌ |
| 5 | **timeline_builder** | `scene_breakdown.json` | ✅ | `render/timeline.json` | ⚠️ (needs finalized scene_breakdown first) |
| 6 | **render_builder** | `render/timeline.json` | ❌ (not generated yet) | `render/ffmpeg_commands.json` | ❌ |
| 7 | **render_executor** | `render/ffmpeg_commands.json` | ❌ (not generated yet) | `render/final_video.mp4` | ❌ |
| 8 | **publish_package_builder** | render outputs | ❌ | `publish/` | ❌ |
| 9 | **quality_control** | render outputs | ❌ | `publish/quality_report.json` | ❌ |
| 10 | **release_manager** | quality report | ❌ | `publish/publishing_report.md` | ❌ |

### Complete check:

| Dependency | Status |
|------------|--------|
| `production_package.json` | ✅ Ready |
| `outline.json` | ✅ Ready |
| `script/*.md` (7 files) | ✅ Ready |
| `review.json` + `review.md` | ✅ Ready |
| `scene_breakdown.json` | ⚠️ Exists but has 31 scenes (15 duplicates) |
| `image_prompts.json` | ❌ Not generated |
| `video_prompts.json` | ❌ Not generated |
| `youtube_metadata.json` | ❌ Not generated |
| `thumbnail_prompt.json` | ❌ Not generated |
| `voiceover_segments.json` | ❌ Not generated |
| `assets/images/` | ❌ Not generated |
| `assets/voice/` | ❌ Not generated |
| `render/` | ❌ Not generated |

## Estimated Runtime per Stage

Based on dry-run benchmark data and historical logs:

| Stage | Historical Duration | Estimated (production) | Notes |
|-------|-------------------|----------------------|-------|
| asset_package | N/A | ~30s (1 LLM call, Ollama) | 16 scenes |
| voiceover | N/A | ~60s (6 sections, Ollama) | 16 scenes |
| image_generator | N/A | ~120s | 16 images |
| voice_generator | N/A | ~60s | ~16 segments |
| timeline_builder | N/A | ~5s | No LLM |
| render_builder | N/A | ~5s | No LLM |
| render_executor | N/A | ~600s (~10 min) | FFmpeg render |
| **Total** | | **~880s (~15 min)** | |

## Blockers

1. **PRIMARY:** `scene_breakdown.json` has 31 entries (15 duplicates). If processed as-is:
   - `asset_package` will generate 31 image prompts + 31 video prompts (2x needed)
   - Downstream generators will create duplicate assets
   - Render will be ~33 minutes instead of ~17 minutes
   - All for zero creative benefit (duplicate scenes)

2. **SECONDARY:** `quota_status.json` shows Gemini quota exhausted today. Must wait for daily reset or switch to Ollama for remaining stages.

## Verdict

⛔ **Pipeline is NOT ready to proceed.**

Must resolve scene_breakdown duplication before continuing.
