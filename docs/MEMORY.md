# Memory Layer — Shadow Protocol Studio

## Purpose

The memory layer ensures continuity across episodes. It lives in `bible/` as versioned JSON files that track all canonical universe state.

## Files

| File | Tracks |
|------|--------|
| `characters.json` | Every character: name, role, status (alive/dead/missing), appears_in episodes, motivation, affiliation |
| `organizations.json` | Every organization: type, members, appears_in episodes |
| `locations.json` | Every location: type (urban/rural/facility/digital), appears_in episodes |
| `timeline.json` | Every canonical event: date, description, related entities, episode |
| `unresolved_mysteries.json` | Open questions: status (open/partially_resolved/resolved), introduced_in, resolved_in |
| `themes.json` | Core thematic registry (static, seeded in Phase 0) |

## How Memory Works

1. **Read** — Memory Resolver agent reads all bible/ files before the pipeline starts
2. **Resolve** — It produces a `resolved_references.json` that lists which entities are relevant to the current episode and any continuity constraints
3. **Write** — After the episode is produced, Memory Update agent appends new entities and events to bible/ files
4. **Version** — Every bible file has a `meta.version` field; updates increment it

## Rules

- Never delete from bible/ — always append
- Mark resolved mysteries with `resolved_in: case_NNN`, don't remove them
- When a character dies, set `status: dead` but keep their entry
- Each entity has an `appears_in` array tracking which episodes reference them
