# Shadow Protocol Studio

AI-native automated YouTube production studio for the **Shadow Protocol** universe — a serialized cinematic psychological thriller presented as investigative documentaries.

## Quick Start

```bash
pip install -e .
cp .env.example .env
# Edit .env with your API keys
create-video case_001
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the complete system design.

## Directory Structure

| Directory | Purpose |
|-----------|---------|
| `bible/` | Canonical universe memory (characters, orgs, locations, timeline, mysteries) |
| `agents/` | Standalone agent scripts — one responsibility each |
| `prompts/` | System prompts for every agent |
| `workflows/` | DAG definitions for pipeline orchestration |
| `projects/` | Per-episode production packages |
| `memory/` | Agent session memory and cross-episode state |
| `templates/` | JSON Schemas and output templates |
| `config/` | Global configuration (models, paths) |
| `shadow_protocol/` | Shared Python library (LLM calls, validation, file utils) |
| `scripts/` | Shell entrypoints and setup utilities |
| `tests/` | Unit and integration tests |

## Commands

```bash
create-video <case_id>          # Full pipeline
create-video --dry-run <case>   # Simulate without LLM calls
create-video --from <step>      # Resume from a specific step
create-video --batch a,b,c      # Process multiple episodes
```

## License

MIT
