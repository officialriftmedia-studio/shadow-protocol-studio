# Workflows — Shadow Protocol Studio

## Default Pipeline

```bash
create-video case_001
```

Executes all 14 stages in order:

```
memory_resolver → story_idea → production_package → outline → script →
script_review → scene_breakdown → [image_prompt, video_prompt, voiceover, thumbnail, metadata] →
validation → memory_update
```

## Recovery Pipeline

If any agent fails, the recovery workflow kicks in:
- 3 retries with exponential backoff (5s, 10s, 20s)
- After 3 failures: generates `error_report.json` + `error_report.md`
- Pipeline halts for human intervention

```bash
create-video case_001  # auto-uses recovery after first failure
```

## Regeneration / Resume

Resume from a specific stage:

```bash
create-video case_001 --from scene_breakdown
```

This skips all stages before `scene_breakdown` and resumes from there. The regeneration workflow checks that required input files exist before proceeding.

## Batch Processing

Process multiple episodes:

```bash
create-video --batch case_001,case_002,case_003
```

Runs episodes sequentially. After all episodes complete, runs cross-episode continuity validation.

## Simulation Mode

```bash
create-video --dry-run case_001
```

Prints what would happen without calling any LLM. Useful for debugging.
