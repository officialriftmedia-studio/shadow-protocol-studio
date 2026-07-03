# Pipeline Summary
**Case:** `case_001`
**Status:** ❌ Failed
**Duration:** 547.1s
**Total LLM calls:** 7
**Total tokens:** 26488
**Total cost:** $0.003372

---
## Stage Breakdown

| Stage | Status | Duration | LLM Calls | Prompt Tokens | Completion Tokens | Total Tokens | Cost |
|-------|--------|----------|-----------|---------------|-------------------|--------------|------|
| `asset_package` | ✅ Success | 19.0s | 1 | 9443 | - | 9443 | $0.001326 |
| `voiceover` | ✅ Success | 59.6s | 6 | 17045 | - | 17045 | $0.002046 |
| `image_generator` | ✅ Success | 324.6s | - | - | - | - | - |
| `voice_generator` | ✅ Success | 15.4s | - | - | - | - | - |
| `timeline_builder` | ✅ Success | 0.2s | - | - | - | - | - |
| `render_builder` | ✅ Success | 0.2s | - | - | - | - | - |
| `render_executor` | ✅ Success | 127.6s | - | - | - | - | - |
| `publish_package_builder` | ✅ Success | 0.3s | - | - | - | - | - |
| `quality_control` | ❌ Failed | 0.3s | - | - | - | - | - |

| **Total** | | **547.1s** | 7 | | | 26488 | $0.003372 |

---
## Token Usage by Stage

- **asset_package**: 9443 tokens `██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░`
- **voiceover**: 17045 tokens `█████████████████████████░░░░░░░░░░░░░░░`

---
## Cost Breakdown

- **asset_package**: $0.001326
- **voiceover**: $0.002046

**Total:** $0.003372

---
## Stage Details

### asset_package
- **Status:** ✅ Success
- **Duration:** 19.0s
- **LLM calls:** 1
- **Tokens:** 9443 (prompt=9443 + completion=0)
- **Cost:** $0.001326
- **Output files:**
  - `image_prompts.json`
  - `video_prompts.json`
  - `youtube_metadata.json`
  - `thumbnail_prompt.json`
  - `thumbnail_prompt.txt`

### voiceover
- **Status:** ✅ Success
- **Duration:** 59.6s
- **LLM calls:** 6
- **Tokens:** 17045 (prompt=17045 + completion=0)
- **Cost:** $0.002046
- **Output files:**
  - `voiceover_segments.json`

### image_generator
- **Status:** ✅ Success
- **Duration:** 324.6s
- **LLM calls:** 0
- **Tokens:** 0 (prompt=0 + completion=0)
- **Cost:** $0.000000
- **Output files:**
  - `assets/images/img_0001.jpg`
  - `assets/images/img_0002.jpg`
  - `assets/images/img_0003.jpg`
  - `assets/images/img_0004.jpg`
  - `assets/images/img_0005.jpg`
  - `assets/images/img_0006.jpg`
  - `assets/images/img_0007.jpg`
  - `assets/images/img_0008.jpg`
  - `assets/images/img_0009.jpg`
  - `assets/images/img_0010.jpg`
  - `assets/images/img_0011.jpg`
  - `assets/images/img_0012.jpg`
  - `assets/images/img_0013.jpg`
  - `assets/images/img_0014.jpg`
  - `assets/images/img_0015.jpg`
  - `assets/images/img_0031.jpg`
  - `assets/manifests/asset_manifest.json`

### voice_generator
- **Status:** ✅ Success
- **Duration:** 15.4s
- **LLM calls:** 0
- **Tokens:** 0 (prompt=0 + completion=0)
- **Cost:** $0.000000
- **Output files:**
  - `assets/voice/voice_scene0001_seg0000.wav`
  - `assets/voice/voice_scene0001_seg0001.wav`
  - `assets/voice/voice_scene0002_seg0000.wav`
  - `assets/voice/voice_scene0003_seg0000.wav`
  - `assets/voice/voice_scene0003_seg0001.wav`
  - `assets/voice/voice_scene0004_seg0000.wav`
  - `assets/voice/voice_scene0004_seg0001.wav`
  - `assets/voice/voice_scene0005_seg0000.wav`
  - `assets/voice/voice_scene0005_seg0001.wav`
  - `assets/voice/voice_scene0005_seg0002.wav`
  - `assets/voice/voice_scene0006_seg0000.wav`
  - `assets/voice/voice_scene0006_seg0001.wav`
  - `assets/voice/voice_scene0006_seg0002.wav`
  - `assets/voice/voice_scene0007_seg0000.wav`
  - `assets/voice/voice_scene0007_seg0001.wav`
  - `assets/voice/voice_scene0008_seg0000.wav`
  - `assets/voice/voice_scene0008_seg0001.wav`
  - `assets/voice/voice_scene0009_seg0000.wav`
  - `assets/voice/voice_scene0009_seg0001.wav`
  - `assets/voice/voice_scene0010_seg0000.wav`
  - `assets/voice/voice_scene0010_seg0001.wav`
  - `assets/voice/voice_scene0011_seg0000.wav`
  - `assets/voice/voice_scene0011_seg0001.wav`
  - `assets/voice/voice_scene0012_seg0000.wav`
  - `assets/voice/voice_scene0012_seg0001.wav`
  - `assets/voice/voice_scene0013_seg0000.wav`
  - `assets/voice/voice_scene0013_seg0001.wav`
  - `assets/voice/voice_scene0013_seg0002.wav`
  - `assets/voice/voice_scene0015_seg0000.wav`
  - `assets/voice/voice_scene0015_seg0001.wav`
  - `assets/voice/voice_scene0015_seg0002.wav`
  - `assets/voice/voice_scene0015_seg0003.wav`
  - `assets/voice/voice_scene0031_seg0000.wav`
  - `assets/voice/voice_scene0031_seg0001.wav`
  - `assets/voice/voice_scene0031_seg0002.wav`
  - `assets/manifests/asset_manifest.json`

### timeline_builder
- **Status:** ✅ Success
- **Duration:** 0.2s
- **LLM calls:** 0
- **Tokens:** 0 (prompt=0 + completion=0)
- **Cost:** $0.000000
- **Output files:**
  - `render/timeline.json`
  - `render/chapters.txt`

### render_builder
- **Status:** ✅ Success
- **Duration:** 0.2s
- **LLM calls:** 0
- **Tokens:** 0 (prompt=0 + completion=0)
- **Cost:** $0.000000
- **Output files:**
  - `render/ffmpeg_commands.json`

### render_executor
- **Status:** ✅ Success
- **Duration:** 127.6s
- **LLM calls:** 0
- **Tokens:** 0 (prompt=0 + completion=0)
- **Cost:** $0.000000
- **Output files:**
  - `render/final_video.mp4`
  - `render/render_manifest.json`

### publish_package_builder
- **Status:** ✅ Success
- **Duration:** 0.3s
- **LLM calls:** 0
- **Tokens:** 0 (prompt=0 + completion=0)
- **Cost:** $0.000000
- **Output files:**
  - `publish/publish_manifest.json`
  - `publish/upload_package/chapters.txt`
  - `publish/upload_package/description.txt`
  - `publish/upload_package/final_video.mp4`
  - `publish/upload_package/metadata.json`
  - `publish/upload_package/tags.txt`
  - `publish/upload_package/title.txt`

### quality_control
- **Status:** ❌ Failed
- **Duration:** 0.3s
- **LLM calls:** 0
- **Tokens:** 0 (prompt=0 + completion=0)
- **Cost:** $0.000000
- **Error:** Agent exited with code 1
