# PHASE 2 — Scene Count Analysis

**Case:** case_001
**Date:** 2026-07-02

## Current Scene Distribution

| Section | Scene Numbers | Unique Count | Total Count (with duplicates) |
|---------|--------------|-------------|------|
| hook | 1, 2, 16, 17 | 2 | 4 |
| act1 | 3, 4, 5, 6, 18, 19, 20, 21 | 4 | 8 |
| act2 | 7, 8, 9, 10, 11, 12, 22, 23, 24, 25, 26, 27 | 6 | 12 |
| act3 | 13, 14, 28, 29 | 2 | 4 |
| ending | 15, 30 | 1 | 2 |
| cliffhanger | 31 | 1 | 1 |
| **Total** | **1–31** | **16** | **31** |

## Duplicate Analysis

The scene breakdown contains **15 duplicate scenes** generated from a second pipeline run:

| Section | Original | Duplicate | Overlap |
|---------|----------|-----------|---------|
| hook | scenes 1–2 | scenes 16–17 | ~100% (same titles, same purposes, different camera notes) |
| act1 | scenes 3–6 | scenes 18–21 | ~100% (same titles: "Guardian", "First Glitch", "Erasure", "Identity Not Found") |
| act2 | scenes 7–12 | scenes 22–27 | ~100% (same titles: "Cage", "Architect", "Watching", "Signature", "Phantom", "Stolen Life") |
| act3 | scenes 13–14 | scenes 28–29 | ~80% (same titles: "Futility of Proof", "System's Echo" vs "Unheard Truth", "Echoes") |
| ending | scene 15 | scene 30 | ~100% (both "Solitary Truth") |

**Effective unique scenes: 16** (scenes 1–15 + scene 31 for cliffhanger)

## Duration Analysis

### All 31 scenes (double-counted):

| Section | Total Duration | Avg per scene |
|---------|---------------|---------------|
| hook | 200s | 50s |
| act1 | 490s | 61s |
| act2 | 790s | 66s |
| act3 | 265s | 66s |
| ending | 150s | 75s |
| cliffhanger | 75s | 75s |
| **Total** | **1,970s (32.8 min)** | **64s avg** |

### Unique 16 scenes only:

| Section | Scenes | Total Duration | Per-Scene Target |
|---------|--------|---------------|------------------|
| hook | 2 | 100s | 1–2 |
| act1 | 4 | 260s | 3–4 |
| act2 | 6 | 415s | 3–5 (❌ exceeds) |
| act3 | 2 | 120s | 2–3 |
| ending | 1 | 75s | 1–2 |
| cliffhanger | 1 | 75s | 1 |
| **Total** | **16** | **1,045s (17.4 min)** | **12–18** |

## Key Metrics

| Metric | Value |
|--------|-------|
| Total scenes in file | 31 |
| Unique scenes | 16 |
| Duplicate scenes | 15 |
| Average duration (unique) | 65s |
| Estimated render time (unique) | ~17.4 min |
| Estimated image prompts | 16 (1 per unique scene) |
| Estimated video prompts | 16 (1 per unique scene) |
| Estimated Gemini requests (downstream) | asset_package(1) + voiceover(~6) = ~7 |

## Comparison Against Optimization Target

| Metric | Current (unique) | Target |
|--------|-----------------|--------|
| Total scenes | 16 | 12–18 ✅ |
| hook | 2 | 1–2 ✅ |
| act1 | 4 | 3–4 ✅ |
| act2 | 6 | 3–5 ❌ (1 over) |
| act3 | 2 | 2–3 ✅ |
| ending | 1 | 1–2 ✅ |
| cliffhanger | 1 | 1 ✅ |
| Duration | 17.4 min | 10–18 min ✅ |

## Bottleneck Analysis

1. **Duplicate scenes (scenes 16–31):** These must be removed before proceeding. If the pipeline runs as-is, `asset_package` will generate image/video prompts for all 31 scenes, doubling the asset count and rendering workload for no creative benefit.

2. **act2 has 6 unique scenes** (target: 3–5). Marginal overage — could be tightened but is acceptable.

3. **Production package predicts 10 min / 5 scenes.** The actual breakdown is 17.4 min / 16 scenes. This is a planning discrepancy but the output quality is appropriate for the story.

## Recommendation

### REGENERATE scene breakdown — BUT with a critical modification

The scene_breakdown.json currently has 31 entries. The duplicates exist because the scene_breakdown agent was run twice. **The unique 16 scenes are actually well-structured.**

**Recommended action:**
1. Remove duplicate scenes (16–30) from `scene_breakdown.json`, keeping only scenes 1–15 + 31
2. This yields 16 unique scenes — within the 12–18 target
3. No full regeneration needed since the unique scenes are already good quality

**Risk of keeping all 31:**
- `asset_package` call will prompt for 31 image + 31 video prompts — ~62 total items in one LLM call
- Token usage will be ~2x what it should be
- Downstream generators will create assets for duplicate scenes, wasting time and compute
- Final render will repeat the same story beats

**Risk of regenerating from scratch:**
- Loses the current unique scene quality
- Additional Gemini requests (may hit quota)
- New content may differ from reviewed script

**Recommendation: MANUALLY prune duplicates from scene_breakdown.json**
