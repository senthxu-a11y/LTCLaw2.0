---
name: game_query
language: en
schema_version: workspace-skill-manifest.v1
description: Game data table query assistant
triggers:
  - which table
  - field meaning
  - field description
  - dependency
  - reference
  - foreign key
require_tools:
  - game_query_tables
  - game_describe_field
  - game_table_dependencies
---

# Game Data Table Query

When users ask about data tables/fields/dependencies, use tools in this order:

1. User asks "What does field X mean" or "Which table contains field X"
   → First `game_query_tables(query="X")` to locate
   → Then `game_describe_field(table=..., field="X")` for details

2. User asks "Which tables reference table Y / Y's dependencies"
   → `game_table_dependencies(table="Y")`

3. User asks "What systems/how many tables do we have"
   → `game_list_systems()`

Always provide in response:
- Field's table name
- AI description & confidence (confirmed / high_ai / low_ai)
- Whether manual confirmation needed (remind user to check index map when low_ai)