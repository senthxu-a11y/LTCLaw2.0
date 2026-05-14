# P0-06 Unified Model Router

## Goal

Validate that formal Game LLM calls use Unified Model Router and failure semantics are structured.

## Required Checks

- [ ] `model_type=workbench_suggest` can be called.
- [ ] `model_type=field_describer` can be called.
- [ ] `model_type=table_summarizer` can be called.
- [ ] Unknown model type falls back to default.
- [ ] No active provider returns structured error.
- [ ] Provider exception returns structured error.
- [ ] Empty response returns structured error.
- [ ] Workbench Suggest model failure does not generate changes.
- [ ] TableIndexer model failure has explicit error/log behavior.

## Boundary

Generic agent chat runner remains a compatibility boundary unless a future lane explicitly unifies it. Lane H-B checks formal Game paths.

## Preferred Tests

- `tests/unit/game/test_service.py`
- `tests/unit/game/test_table_indexer.py`
- `tests/unit/game/test_dependency_resolver.py`
- `tests/unit/game/test_knowledge_rag_answer.py`
- `tests/unit/routers/test_game_workbench_router.py`
- Optional split file: `tests/unit/game/test_unified_model_router_contract.py`

## Receipt Requirements

Report model types covered, structured error cases, formal Game callers, and whether any module directly selects provider/model.
