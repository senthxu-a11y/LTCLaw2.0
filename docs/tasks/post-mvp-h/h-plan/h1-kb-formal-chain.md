# H1 KB Formal Chain Validation

## Goal

Confirm that KB/retrieval is no longer part of the formal knowledge system. KB may remain only as legacy, debug, or migration surface.

## Source Focus

- `src/ltclaw_gy_x/game/knowledge_release_service.py`
- `src/ltclaw_gy_x/app/routers/game_knowledge_query.py`
- `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py`
- `src/ltclaw_gy_x/game/knowledge_rag_context.py`
- `src/ltclaw_gy_x/game/workbench_suggest_context.py`
- `src/ltclaw_gy_x/app/routers/game_knowledge_base.py`
- `src/ltclaw_gy_x/app/routers/game_doc_library.py`
- `src/ltclaw_gy_x/game/retrieval.py`
- Console Knowledge Base / Doc Library / Workbench Suggest UI surfaces

## Checklist

- [ ] Release build does not call `get_kb_store`.
- [ ] Release build does not call `_load_approved_doc_entries`.
- [ ] Release build does not load workspace/session approved docs.
- [ ] Release doc artifacts are derived from Formal Map / Current Release doc refs.
- [ ] Strict build fails without a saved Formal Map.
- [ ] Bootstrap build is explicit and returns warning/status.
- [ ] RAG context does not call KB store.
- [ ] RAG context does not call legacy retrieval.
- [ ] RAG context fails closed when no Current Release exists.
- [ ] RAG answer does not fall back to legacy provider/retrieval in GameService formal path.
- [ ] Workbench Suggest formal evidence comes only from Current Release + Map-gated RAG context.
- [ ] Draft Overlay is never promoted to formal evidence.
- [ ] Chat formal knowledge mode does not fall back to KB/retrieval.
- [ ] Knowledge Base UI is hidden or labelled legacy/debug/migration-only.
- [ ] Doc Library sync is labelled `legacy_kb_migration_only` or equivalent.
- [ ] Index/status surfaces separate formal knowledge status from legacy retrieval status.

## Tests To Prefer

- Release builds without KB store.
- Strict Release build fails without Formal Map.
- Bootstrap Release build succeeds only when explicitly requested.
- RAG context returns insufficient context without Current Release instead of KB fallback.
- Chat/no-current-release path records no legacy fallback.
- Workbench Suggest filters formal evidence to allowed formal refs.

## Pass Standard

Formal knowledge is Current Release + Formal Map + Map-gated artifacts only. KB/retrieval remains outside the formal chain.
