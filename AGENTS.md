# Agents — Shadow Protocol Studio

Every agent follows the same contract:

| Aspect | Rule |
|--------|------|
| **Responsibility** | One concern per agent |
| **Input** | Read from file paths passed as CLI args (not stdin) |
| **Output** | Write structured files (JSON / Markdown) |
| **Context** | Read only the files it needs — never the full project |
| **Reusability** | No episode-specific logic — read all context from files |
| **Failure** | Exit non-zero with a machine-readable error message |

## Agent Index

| # | Agent | File | Produces |
|---|-------|------|----------|
| 1 | **Orchestrator** | `agents/orchestrator.py` | Pipeline execution log |
| 2 | **Memory Resolver** | `agents/memory_resolver.py` | Resolved references JSON |
| 3 | **Story Idea** | `agents/story_idea.py` | `story_idea.md` |
| 4 | **Production Package** | `agents/production_package.py` | `production_package.json` |
| 5 | **Outline** | `agents/outline.py` | `outline.json` |
| 6 | **Script** | `agents/script.py` | `script_section_N.md` |
| 7 | **Script Review** | `agents/script_review.py` | `review.md` |
| 8 | **Scene Breakdown** | `agents/scene_breakdown.py` | `scene_breakdown.json` |
| 9 | **Image Prompt** | `agents/image_prompt.py` | `image_prompts.json` |
| 10 | **Video Prompt** | `agents/video_prompt.py` | `video_prompts.json` |
| 11 | **Voiceover** | `agents/voiceover.py` | `voiceover_segments.json` |
| 12 | **Thumbnail** | `agents/thumbnail.py` | `thumbnail_prompt.txt` |
| 13 | **Metadata** | `agents/metadata.py` | `youtube_metadata.json` |
| 14 | **Memory Update** | `agents/memory_update.py` | Updated `bible/*.json` |
| 15 | **Validation** | `agents/validation.py` | `validation_report.json` |

## Agent Contract

```python
# Every agent implements:
def run(input_dir: str, output_dir: str, config: dict) -> int:
    # Returns 0 on success, non-zero on failure
    ...
```
