# Tutorial — Shadow Protocol Studio

## Prerequisites

- Python 3.11+
- API keys for your LLM provider (OpenAI or Anthropic)
- pip

## Installation

```bash
git clone <repo-url> shadow-protocol-studio
cd shadow-protocol-studio
chmod +x scripts/setup.sh scripts/create-video
./scripts/setup.sh
```

Edit `.env` with your API keys:

```env
OPENAI_API_KEY=sk-...
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
```

## Your First Episode

```bash
create-video case_001
```

This runs the full pipeline:
1. Resolves universe memory
2. Generates a story idea
3. Creates a production package
4. Produces an outline
5. Writes the script section-by-section
6. Reviews the script
7. Breaks scenes down
8. Generates image prompts
9. Generates video prompts
10. Generates voiceover segments
11. Designs a thumbnail
12. Creates YouTube metadata
13. Validates all outputs
14. Updates universe memory

## Resume a Failed Run

```bash
create-video case_001 --from scene_breakdown
```

## Dry Run

```bash
create-video case_001 --dry-run
```

## Batch Episodes

```bash
create-video --batch case_001,case_002,case_003
```

## Next Steps

- Read `docs/ARCHITECTURE.md` to understand the system design
- Read `AGENTS.md` for the full agent contract
- Edit `bible/themes.json` to customize the universe
- Edit `prompts/*.md` to customize agent behavior
