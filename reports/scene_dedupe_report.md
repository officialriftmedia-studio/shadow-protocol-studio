# Scene Deduplication Report

**Case:** case_001
**Date:** 2026-07-02

## Before

| Metric | Value |
|--------|-------|
| Total scenes | 31 |
| Unique scenes | 16 |
| Duplicate scenes | 15 |
| Total duration (all) | 1,970s (32.8 min) |
| Estimated render time (all) | ~33 min |

## Scenes to PRESERVE

| scene_number | Section | Title | Duration |
|-------------|---------|-------|----------|
| 1 | hook | The Phantom Echo | 75s |
| 2 | hook | Rewind to the Precipice | 25s |
| 3 | act1 | The Digital Guardian | 60s |
| 4 | act1 | The First Glitch | 50s |
| 5 | act1 | Spreading Discrepancies | 80s |
| 6 | act1 | Identity Not Found | 70s |
| 7 | act2 | Going Dark | 65s |
| 8 | act2 | The Architecture | 70s |
| 9 | act2 | Phantom Presence | 60s |
| 10 | act2 | The Machine | 65s |
| 11 | act2 | Identity Reassigned | 75s |
| 12 | act2 | A Stolen Life | 80s |
| 13 | act3 | The Unheard Truth | 60s |
| 14 | act3 | Echoes of Reality | 60s |
| 15 | ending | A Solitary Truth | 75s |
| 31 | cliffhanger | The Indifferent Machine | 75s |

## Scenes to REMOVE

| scene_number | Section | Title | Duplicate Of |
|-------------|---------|-------|-------------|
| 16 | hook | Identity Not Found | scene 1 (hook) |
| 17 | hook | Three Days Earlier | scene 2 (hook) |
| 18 | act1 | Guardian of the Digital Order | scene 3 (act1) |
| 19 | act1 | The First Glitch | scene 4 (act1) |
| 20 | act1 | The Digital Erasure Begins | scene 5 (act1) |
| 21 | act1 | Identity Not Found | scene 6 (act1) |
| 22 | act2 | The Digital Cage | scene 7 (act2) |
| 23 | act2 | Architect of Deception | scene 8 (act2) |
| 24 | act2 | Watching Back | scene 9 (act2) |
| 25 | act2 | The Machine's Signature | scene 10 (act2) |
| 26 | act2 | Project Phantom | scene 11 (act2) |
| 27 | act2 | A Stolen Life | scene 12 (act2) |
| 28 | act3 | The Futility of Proof | scene 13 (act3) |
| 29 | act3 | The System's Echo | scene 14 (act3) |
| 30 | ending | Solitary Truth | scene 15 (ending) |

## After

| Metric | Value |
|--------|-------|
| Total scenes | **16** |
| Total duration | **1,045s (17.4 min)** |
| Estimated render time | **~17 min** |
| Image prompts needed | 16 (was 31) |
| Video prompts needed | 16 (was 31) |
| Asset generation savings | **~48%** |

## Verdict

Duplicate removal is safe and necessary. The 16 preserved scenes are high quality, follow the script structure, and fit within the 12–18 optimization target.
