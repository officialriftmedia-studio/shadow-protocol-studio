# Pipeline Summary
**Case:** `case_001`
**Status:** ❌ Failed
**Duration:** 84.1s
**Total LLM calls:** 8
**Total tokens:** 46800
**Total cost:** $0.010118

---
## Stage Breakdown

| Stage | Status | Duration | LLM Calls | Prompt Tokens | Completion Tokens | Total Tokens | Cost |
|-------|--------|----------|-----------|---------------|-------------------|--------------|------|
| `script` | ✅ Success | 0.2s | - | - | - | - | - |
| `script_review` | ✅ Success | 0.1s | 3 | 27669 | - | 27669 | $0.004990 |
| `scene_breakdown` | ✅ Success | 80.9s | 5 | 19131 | - | 19131 | $0.005128 |
| `image_prompt` | ❌ Failed | 2.9s | - | - | - | - | - |

| **Total** | | **84.1s** | 8 | | | 46800 | $0.010118 |

---
## Token Usage by Stage

- **script_review**: 27669 tokens `███████████████████████░░░░░░░░░░░░░░░░░`
- **scene_breakdown**: 19131 tokens `████████████████░░░░░░░░░░░░░░░░░░░░░░░░`

---
## Cost Breakdown

- **script_review**: $0.004990
- **scene_breakdown**: $0.005128

**Total:** $0.010118

---
## Stage Details

### script
- **Status:** ✅ Success
- **Duration:** 0.2s
- **LLM calls:** 0
- **Tokens:** 0 (prompt=0 + completion=0)
- **Cost:** $0.000000
- **Output files:**
  - `script/act1.md`
  - `script/act2.md`
  - `script/act3.md`
  - `script/cliffhanger.md`
  - `script/ending.md`
  - `script/hook.md`
  - `script/script.md`

### script_review
- **Status:** ✅ Success
- **Duration:** 0.1s
- **LLM calls:** 3
- **Tokens:** 27669 (prompt=27669 + completion=0)
- **Cost:** $0.004990
- **Output files:**
  - `review.json`
  - `review.md`

### scene_breakdown
- **Status:** ✅ Success
- **Duration:** 80.9s
- **LLM calls:** 5
- **Tokens:** 19131 (prompt=19131 + completion=0)
- **Cost:** $0.005128
- **Output files:**
  - `scene_breakdown.json`

### image_prompt
- **Status:** ❌ Failed
- **Duration:** 2.9s
- **LLM calls:** 0
- **Tokens:** 0 (prompt=0 + completion=0)
- **Cost:** $0.000000
- **Error:** Agent exited with code 1
