# H2 Map-gated RAG Validation

## Goal

Confirm that formal RAG is strictly gated by Current Release and Formal Map refs.

## Source Focus

- `src/ltclaw_gy_x/game/knowledge_rag_context.py`
- `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py`
- `src/ltclaw_gy_x/game/knowledge_rag_answer.py`
- Release artifact readers and citation builders

## Checklist

- [ ] RAG loads Current Release first.
- [ ] RAG loads the release map snapshot.
- [ ] RAG routes query to allowed refs before artifact reads.
- [ ] `allowed_refs` come only from active Formal Map refs.
- [ ] `ignored` refs are excluded.
- [ ] `deprecated` refs are excluded.
- [ ] `knowledge_map.deprecated` refs are excluded.
- [ ] Explicit `focus_refs` are hard constraints.
- [ ] Empty or wholly invalid explicit `focus_refs` fail closed.
- [ ] Partial valid `focus_refs` only allow the valid active subset.
- [ ] `table:*` refs map only to table schema artifacts.
- [ ] `doc:*` refs map only to doc knowledge artifacts.
- [ ] `script:*` refs map only to script evidence artifacts.
- [ ] Candidate evidence is not formal RAG evidence.
- [ ] Raw source files are not formal RAG evidence.
- [ ] Pending drafts are not formal RAG evidence.
- [ ] Session drafts are not formal RAG evidence.
- [ ] RAG does not scan all artifacts first and filter later.
- [ ] RAG stops reading artifact rows once routed refs are satisfied.
- [ ] Citations preserve `citation_id`, `release_id`, `artifact_path`, `source_path`, `row`, `field`, `title`, `source_hash`, and `ref`.
- [ ] `no_current_release`, `insufficient_context`, and no-evidence cases do not fall back to KB/retrieval.

## Tests To Prefer

- Ignored/deprecated refs never appear in chunks or citations.
- Invalid focus refs produce `no_active_focus_refs`.
- Mixed focus refs only read active refs.
- Candidate evidence does not enter formal context.
- Citation fields support Workbench deep-link needs.

## Pass Standard

RAG answers can cite only Current Release artifacts selected through the Formal Map route.
