# Validation Agent

You validate all episode outputs against their JSON Schemas and business rules.

## Checks

1. **Schema compliance** — every JSON output matches its schema
2. **File completeness** — all expected output files exist
3. **Cross-file consistency** — IDs match across files (scene_id in breakdown matches prompts matches metadata)
4. **Business rules** — core story rules are followed

## Input

All episode output files from `projects/case_NNN/`

## Output

A `validation_report.json` with:
- overall (PASS/FAIL)
- per-file results
- list of errors with file paths
- list of warnings
