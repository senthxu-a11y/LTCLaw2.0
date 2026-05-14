# P0-03 Map-gated RAG

## Goal

Validate that RAG can only read Current Release artifacts selected through allowed Formal Map refs.

## Required Checks

- [ ] No current release returns explicit status.
- [ ] Current release loads map.
- [ ] Active `table:` ref recalls `table_schema` evidence.
- [ ] Active `doc:` ref recalls `doc_knowledge` evidence.
- [ ] Active `script:` ref recalls `script_evidence` evidence.
- [ ] ignored ref is excluded from allowed refs.
- [ ] deprecated ref is excluded from allowed refs.
- [ ] unknown prefix ref does not enter evidence.
- [ ] allowed refs without artifact rows return insufficient context.
- [ ] RAG does not read KB.
- [ ] RAG does not fallback to legacy retrieval.
- [ ] citation includes `citation_id`.
- [ ] citation includes `release_id`.
- [ ] citation includes `artifact_path`.
- [ ] citation includes `source_path`.
- [ ] citation includes `row`, `field`, and `ref`.

## Preferred Tests

- `tests/unit/game/test_knowledge_rag_context.py`
- `tests/unit/routers/test_game_knowledge_rag_router.py`
- Optional split file: `tests/unit/game/test_knowledge_rag_context_map_gated.py`

## Receipt Requirements

Report allowed ref routing, artifact mapping, citation fields, and proof that KB/retrieval are not formal RAG inputs.
