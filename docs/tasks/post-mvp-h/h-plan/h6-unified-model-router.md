# H6 Unified Model Router Validation

## Goal

Confirm formal Game LLM calls use a unified model router instead of per-module provider/API configuration.
Generic agent chat runner may remain a compatibility boundary as long as console formal knowledge injection does not choose provider/model on its own.

## Source Focus

- `src/ltclaw_gy_x/game/unified_model_router.py`
- `src/ltclaw_gy_x/game/service.py`
- `src/ltclaw_gy_x/game/table_indexer.py`
- `src/ltclaw_gy_x/game/dependency_resolver.py`
- `src/ltclaw_gy_x/app/routers/game_workbench.py`
- Chat compatibility boundary / RAG answer paths
- Provider configuration files

## Checklist

- [ ] Unified Model Router exists.
- [ ] SimpleModelRouter is only a compatibility adapter.
- [ ] Workbench Suggest uses `call_model_result`.
- [ ] TableIndexer uses the unified router.
- [ ] DependencyResolver uses the unified router.
- [ ] RAG Answer uses the unified router.
- [ ] Generic agent chat runner is explicitly treated as a compatibility boundary.
- [ ] Console formal chat only injects current-release formal context and does not select provider/model.
- [ ] Supported model types include `default`, `field_describer`, `table_summarizer`, `map_builder`, `map_diff_explainer`, `rag_answer`, and `workbench_suggest`.
- [ ] Unknown model type falls back to `default`.
- [ ] Model type maps to project config model slots.
- [ ] Formal Game feature modules do not directly read API keys.
- [ ] Formal Game feature modules do not directly read base URLs.
- [ ] Formal Game feature modules do not directly choose provider/model.
- [ ] Formal Game feature modules submit prompt, model type, and metadata only.
- [ ] Empty response returns structured error.
- [ ] Provider exception returns structured error.
- [ ] No active model returns structured error.
- [ ] Provider not configured returns structured error.
- [ ] Modules do not treat empty strings as successful model output.
- [ ] Future timeout/temperature/max tokens/retry/fallback remain config work, not Lane H expansion.

## Tests To Prefer

- No active model makes Workbench Suggest return clear error.
- Empty model response does not create changes.
- `model_type=workbench_suggest` uses its slot or default.
- Unknown model type falls back to default.
- Provider exception is structured, not an unexplained 500.

## Pass Standard

LLM routing is centralized; quality/config refinements may continue in later lanes without new per-feature model APIs.

For Lane H, this standard applies to formal Game paths. Generic agent chat runner remains a compatibility boundary unless a later lane intentionally unifies it.
