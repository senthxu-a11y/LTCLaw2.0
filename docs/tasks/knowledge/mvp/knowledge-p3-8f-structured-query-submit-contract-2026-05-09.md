# Knowledge P3.8f Structured Query Submit Contract

Date: 2026-05-09

## Goal

Freeze the future minimal structured-query panel submit contract and frontend typing contract.

This slice is docs-only.

This slice does not modify backend code, frontend code, router behavior, request schema, or public API.

## Reviewed Anchors

1. `docs/tasks/knowledge/mvp/knowledge-p3-8d-structured-query-destination-discovery-2026-05-09.md`
2. `docs/tasks/knowledge/mvp/knowledge-p3-8e-structured-query-panel-contract-2026-05-09.md`
3. `docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md`
4. `console/src/api/modules/game.ts`
5. `console/src/api/types/game.ts`
6. `console/src/pages/Game/GameProject.tsx`
7. `console/src/pages/Game/ragUiHelpers.ts`
8. `src/ltclaw_gy_x/app/routers/game_knowledge_query.py`
9. `src/ltclaw_gy_x/app/routers/game_index.py`
10. `src/ltclaw_gy_x/game/query_router.py`
11. Additional repository search for `gameApi.query`, `/game/index/query`, `QueryRequest`, `exact_table`, `exact_field`, `semantic_stub`, and `not_configured`

## Baseline Carried Forward

The following boundaries remain fixed during this review:

1. The first-version structured-query destination remains a minimal in-page panel inside GameProject.
2. The panel remains exact lookup only for numeric, row-level, field-level, and value-level questions.
3. Change, edit, modify, patch, add, remove, rewrite, and release-oriented actions remain outside this panel and continue to route to workbench or later release flows.
4. The panel opens only from explicit user action.
5. Prefill may exist, but open and submit remain separate user actions.
6. Ordinary RAG answer request remains `{ query }` only.
7. No RAG router change is authorized.
8. No provider, model, provider hint, or service config field is authorized.
9. No provider-selection change is authorized.
10. No real LLM integration is authorized.
11. No citation artifact endpoint or raw-source reading endpoint is authorized.
12. `P3.8c` workbench affordance remains unchanged.

## Current Endpoint Reality

### 1. Which Endpoint Does `gameApi.query(agentId, q, mode = "auto")` Hit?

Current answer:

1. `console/src/api/modules/game.ts` sends `POST /agents/{agentId}/game/index/query`.
2. That route lands on `src/ltclaw_gy_x/app/routers/game_index.py`.
3. The route calls `QueryRouter.query(request.q, request.mode)` in `src/ltclaw_gy_x/game/query_router.py`.

### 2. Current Request Shape

The current backend request model is:

1. `q: str`
2. `mode: str = "auto"`

No other request fields are currently defined on this route.

There is no backend request field for:

1. provider
2. model
3. provider hint
4. service config
5. top_k
6. citation options
7. write or publish options

### 3. Current Response Shape

The current `/game/index/query` route has no dedicated response model.

Its effective response shape is the direct dict returned by `QueryRouter.query(...)`.

Observed current top-level response fields:

1. `mode: string`
2. `results: list`

Observed current response branches:

1. `{"mode": "not_configured", "results": []}`
2. `{"mode": "exact_table", "results": table_items}`
3. `{"mode": "exact_field", "results": field_items}`
4. `{"mode": "semantic_stub", "results": []}`

Observed current result-item shapes:

1. `exact_table` returns `list_tables(...)["items"]`, which are serialized `TableIndex` objects.
2. `exact_field` returns objects shaped like `{ "table": string, "field": FieldInfo-json }`.
3. `not_configured` and `semantic_stub` currently return empty arrays with no message field.

### 4. Current Mode Constraint Reality

Current answer:

1. Backend request model accepts `mode: str` with default `"auto"`.
2. No backend enum validation exists on this field.
3. No frontend literal type or documented mode union exists in `console/src/api/types/game.ts`.
4. The current `QueryRouter.query(...)` implementation only contains explicit behavior for `mode == "auto"`.
5. Any other mode currently falls through to `{"mode": "semantic_stub", "results": []}`.

Conclusion:

1. There is no stable public mode enumeration today.
2. There is only one meaningful first-version mode in practice: `"auto"`.

## Contract Decision

### 1. Should The First-Version Panel Bind Directly To The Existing Wrapper?

Decision: not directly as an untyped raw call.

Reasoning:

1. The transport endpoint already exists and is likely reusable.
2. But the current frontend wrapper is untyped and the backend response is too loose for a stable product-facing panel contract.
3. The first implementation-capable slice should therefore introduce a frontend typed wrapper or normalization layer over the existing endpoint rather than changing backend behavior first.

### 2. Should The First-Version Panel Reuse The Existing Backend Endpoint?

Decision: yes, conditionally.

Condition:

1. The panel should reuse `POST /game/index/query` only through a new typed frontend wrapper contract that fixes request fields, fixed mode, normalized read-only response shape, and empty or error handling.

This is a frontend contract freeze, not a backend redesign.

## Frozen First-Version Request Contract

The first-version panel submit contract should be frozen as a read-only request with only two payload fields sent to the existing endpoint.

Allowed transport payload:

1. `q: string`
2. `mode: "auto"`

Product-level request contract for the future panel:

1. The visible panel input should be called `query` in frontend state.
2. The frontend typed wrapper should map that to backend `q`.
3. `mode` should be fixed internally to `"auto"` for the first version.
4. The first version should not expose a mode selector.

Explicitly forbidden request fields:

1. provider
2. model
3. provider hint
4. service config
5. build flag
6. publish flag
7. candidate flag
8. test-plan flag
9. write or patch flag

## Frozen First-Version Submit Behavior

The first-version panel submit behavior should be:

1. User opens the panel explicitly.
2. Panel may prefill the current RAG query into local input state.
3. No request is sent on open.
4. No request is sent on prefill.
5. Only explicit user click on `Submit` may call the typed wrapper.
6. Submit performs read-only lookup only.
7. Submit must not create a test plan.
8. Submit must not create a candidate.
9. Submit must not build.
10. Submit must not publish.
11. Submit must not mutate workbench state.

## Frozen First-Version Response Typing Contract

### 1. Why A Frontend Response Wrapper Is Needed

Current response is too loose for direct panel rendering because:

1. The route has no declared response model.
2. `mode` doubles as both branch signal and rough status.
3. Empty states currently contain no message.
4. Error detail is HTTP-only and not normalized into panel state.
5. Two success branches return different item shapes.

Therefore the first version should freeze a frontend normalization contract over the current backend response.

### 2. Recommended Frontend Wrapper Response Shape

Recommended normalized panel response contract:

1. `query: string`
2. `request_mode: "auto"`
3. `result_mode: "exact_table" | "exact_field" | "semantic_stub" | "not_configured"`
4. `status: "success" | "empty" | "unavailable" | "error"`
5. `message: string | null`
6. `warnings: string[]`
7. `items: StructuredQueryDisplayItem[]`
8. `error: string | null`

Recommended `StructuredQueryDisplayItem` union:

1. `kind: "table"`
2. `table_name: string`
3. `source_path: string`
4. `system: string | null`
5. `row_count: number`
6. `primary_key: string`
7. `summary: string | null`

And:

1. `kind: "field"`
2. `table_name: string`
3. `field_name: string`
4. `field_type: string`
5. `description: string`
6. `confidence: string`
7. `references: string[]`
8. `tags: string[]`

### 3. Result Mapping Rules

Recommended first-version normalization rules:

1. Backend `mode = "exact_table"` maps to `status = "success"` and `kind = "table"` items.
2. Backend `mode = "exact_field"` maps to `status = "success"` and `kind = "field"` items.
3. Backend `mode = "semantic_stub"` maps to `status = "empty"` with a fixed read-only empty-state message.
4. Backend `mode = "not_configured"` maps to `status = "unavailable"` with a fixed configuration message.
5. HTTP failure maps to `status = "error"` and `error = detail`.

### 4. Source Or Citation-Like Refs Policy

The first-version panel may display only source-like refs already present in current payloads.

Allowed source-like display fields:

1. `source_path` from table results.
2. `references` from field results.

Not allowed:

1. New citation artifact endpoint.
2. New raw-source endpoint.
3. New source expansion flow.

## Mode Strategy

### Decision

The first-version panel should use fixed `mode = "auto"` only.

Reasoning:

1. `auto` is the only backend mode with explicit logic today.
2. There is no stable backend enum for other modes.
3. There is no typed frontend union for other modes.
4. Exposing a mode selector now would create product semantics that current backend does not truly support.

### Consequence

1. The future typed wrapper should hardcode `mode = "auto"`.
2. If later slices need additional modes, that should be a separate contract review.

## Permission Boundary

### Current Reality

1. `POST /game/knowledge/query` already requires `knowledge.read`.
2. `POST /game/index/query` currently has no explicit route-level capability check.
3. The future structured-query panel should still be treated as a read-only lookup surface.

### Frozen First-Version Recommendation

1. The panel must not require `knowledge.build`.
2. The panel must not require `knowledge.publish`.
3. The temporary first-version panel entry and submit permission may use `knowledge.read` as the interim read gate if no dedicated structured-query read capability exists yet.
4. This temporary use of `knowledge.read` is an implementation bridge, not a permanent product truth.
5. Long term, a dedicated structured-query read capability remains the preferred destination.

This review does not authorize build or publish fallback and does not collapse the long-term capability model.

## Exact Scope Boundary

The first-version panel remains limited to:

1. exact numeric lookup
2. row-level lookup
3. field-level lookup
4. value-level lookup

The first-version panel explicitly excludes:

1. change intent
2. edit intent
3. modify intent
4. patch intent
5. add or remove intent
6. rewrite intent
7. test-plan generation
8. candidate creation
9. build
10. publish

All such requests remain outside this panel and continue toward workbench or later governance flows.

## RAG And Routing Boundary Confirmation

The following remain unchanged:

1. RAG answer request still sends only `{ query }`.
2. RAG router remains unchanged.
3. Provider selection remains unchanged.
4. No real LLM integration is added.
5. No citation artifact endpoint is added.
6. No raw-source endpoint is added.
7. `P3.8c` workbench affordance remains unchanged.

## Recommendation

Recommendation for this round:

1. Keep this slice docs-only.
2. Freeze first-version panel submit to a typed frontend wrapper over `POST /game/index/query`.
3. Freeze first-version request to `query + fixed auto mode` only.
4. Freeze first-version response rendering to a normalized read-only display contract.
5. Do not change backend yet.
6. The next implementation-capable step may proceed as frontend-only if it includes the typed wrapper and normalization layer.

## Acceptance

This review is acceptable only if all of the following remain true:

1. The document records that `gameApi.query(...)` currently hits `POST /game/index/query`.
2. The document records that the current backend request shape is only `q` plus `mode`.
3. The document records that the current backend response shape is only `mode` plus `results` with branch-specific item shapes.
4. The document records that there is no stable backend or frontend mode enum today.
5. The document selects fixed `mode = "auto"` as the only first-version mode.
6. The document freezes first-version request fields to query plus fixed mode and forbids provider or model or service-config fields.
7. The document recommends a frontend typed wrapper or normalization contract rather than immediate backend change.
8. The document freezes a read-only normalized response typing contract for the future panel.
9. The document keeps prefill allowed but submit explicit only.
10. The document keeps submit read-only and non-writing.
11. The document keeps exact numeric, row-level, field-level, and value-level lookup as the only first-version target.
12. The document keeps build and publish out of the permission requirement and records interim `knowledge.read` only as a temporary bridge.
13. The document preserves the `{ query }` RAG boundary and all existing provider, router, and citation boundaries.
14. This slice adds no backend code, no frontend code, and no new API.

## Validation Note

1. This slice is docs-only.
2. This slice does not run pytest.
3. This slice does not modify `src/`.
4. This slice does not modify `console/src`.
5. Post-edit validation for this slice is limited to documentation error checking.
