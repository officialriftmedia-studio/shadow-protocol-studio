# Pipeline Summary
**Case:** `case_001`
**Status:** ❌ Failed
**Duration:** 38.6s
**Total LLM calls:** 1
**Total tokens:** 9693
**Total cost:** $0.001401

---
## Stage Breakdown

| Stage | Status | Duration | LLM Calls | Prompt Tokens | Completion Tokens | Total Tokens | Cost |
|-------|--------|----------|-----------|---------------|-------------------|--------------|------|
| `asset_package` | ✅ Success | 13.7s | 1 | 9693 | - | 9693 | $0.001401 |
| `voiceover` | ❌ Failed | 24.9s | - | - | - | - | - |

| **Total** | | **38.6s** | 1 | | | 9693 | $0.001401 |

---
## Token Usage by Stage

- **asset_package**: 9693 tokens `████████████████████████████████████████`

---
## Cost Breakdown

- **asset_package**: $0.001401

**Total:** $0.001401

---
## Stage Details

### asset_package
- **Status:** ✅ Success
- **Duration:** 13.7s
- **LLM calls:** 1
- **Tokens:** 9693 (prompt=9693 + completion=0)
- **Cost:** $0.001401
- **Output files:**
  - `image_prompts.json`
  - `video_prompts.json`
  - `youtube_metadata.json`
  - `thumbnail_prompt.json`
  - `thumbnail_prompt.txt`

### voiceover
- **Status:** ❌ Failed
- **Duration:** 24.9s
- **LLM calls:** 0
- **Tokens:** 0 (prompt=0 + completion=0)
- **Cost:** $0.000000
- **Error:** Agent exited with code 1
