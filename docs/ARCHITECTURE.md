# Architecture — Shadow Protocol Studio

## Overview

Shadow Protocol Studio is an AI-native YouTube production automation system. It transforms a single episode identifier into a complete production package through a pipeline of specialized agents.

## Design Philosophy

1. **File-based state** — All agent state lives on disk as JSON/Markdown files. No databases. No shared memory.
2. **Single responsibility** — Each agent does exactly one thing. Agents never overlap in concern.
3. **Minimal context** — Agents read only the files they need. No agent loads the full project.
4. **Idempotent outputs** — Re-running an agent with the same inputs produces the same outputs.
5. **Token efficiency** — Everything is designed to minimize LLM token consumption.

## System Diagram

```
                   ┌──────────────┐
                   │   CLI: create-video   │
                   └──────┬───────┘
                          │
                   ┌──────▼───────┐
                   │ Orchestrator │
                   │  (DAG Exec)  │
                   └──────┬───────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
    ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
    │ Memory    │  │ Story     │  │ Production│
    │ Resolver  │──► Idea      │──► Package   │──► ...
    └───────────┘  └───────────┘  └───────────┘

    All agents read from ──►  bible/  (canonical memory)
    All agents write to  ──►  projects/case_NNN/
    All agents validated ──►  templates/schemas/
    All agents prompted ──►  prompts/
```

## Data Flow

Every agent follows this contract:

1. Read input files from `input_dir/`
2. Read configuration from `config/`
3. Read system prompt from `prompts/{agent_name}.md`
4. Call LLM with prompt + input
5. Validate output against JSON Schema
6. Write output files to `output_dir/`
7. Exit 0 (success) or non-zero (failure)

## Key Files

| File | Purpose |
|------|---------|
| `shadow_protocol/lib/llm.py` | Unified LLM interface (OpenAI, Anthropic) |
| `shadow_protocol/lib/file_utils.py` | File I/O with env-var resolution |
| `shadow_protocol/lib/schema_validator.py` | JSON Schema validation |
| `shadow_protocol/lib/orchestrator_runner.py` | Pipeline DAG executor |
| `config/default.json` | Global config with ${ENV_VAR} substitution |
| `config/models.json` | Provider/model registry with costs |
| `config/paths.json` | Stage-to-file-path mappings |
