---
name: numeric_assist
language: en
schema_version: workspace-skill-manifest.v1
description: Numeric cross comparison / history trend / impact analysis helper
triggers:
  - cross compare
  - peer compare
  - history trend
  - impact analysis
  - which tables affected
require_tools:
  - game_query_tables
  - game_describe_field
  - game_workbench_preview
---

# Numeric Assist

Activate this skill when the planner asks to compare a row with peers, look up
history of a value, or understand the downstream impact of a numeric change.

## Workflow

1. `game_query_tables` to fetch schema + ai_summary; confirm PK and target field.
2. Cross compare: read peer rows (same group/quality/level), tabulate.
3. History: query SVN log for the field's past N commits.
4. Impact: walk downstream dependency_graph two levels, list affected tables.

## Output

- Markdown tables for comparisons.
- Tree-style indented list for impact graph.
- Any suggested edits must be returned as a `changes: [...]` JSON block matching
  the workbench `/suggest` schema.

## Caveats

- Skill never edits tables directly; it only produces analysis + suggestions.
- If SVN history is unavailable, say so explicitly.
