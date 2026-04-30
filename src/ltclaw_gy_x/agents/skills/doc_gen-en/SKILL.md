---
name: doc_gen
language: en
schema_version: workspace-skill-manifest.v1
description: Generate design / requirement / change-note Markdown docs
triggers:
  - write a design doc
  - generate requirement doc
  - draft change note
  - produce a markdown doc
require_tools:
  - write_file
  - game_query_tables
---

# Doc Generation

Convert conversational requirements / changes into a Markdown document ready to
commit.

## Default template

```markdown
---
title: <topic>
type: design_doc | change_note | requirement
author: <agent name>
created: <YYYY-MM-DD>
related_tables: [Equipment, Skill]
---

# <topic>

## 1. Background
...
## 2. Goals
- ...
## 3. Plan
### 3.1 Numeric changes
| Table | Row | Field | Old | New | Reason |
### 3.2 Doc changes
- ...
## 4. Risks & rollback
...
## 5. References
...
```

## Workflow

1. Distill requirements from chat history; tabulate any numeric change.
2. Use `game_query_tables` to fetch schema for tables referenced.
3. `write_file` to `docs/<slug>.md`.
4. Return doc path; front-end will push a `draft_doc` workbench card.

## Constraints

- Frontmatter required.
- Risks & rollback section is mandatory.
- Mention every changed field by name at least once for downstream indexing.
