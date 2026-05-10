# Lane B: P20 Backend-Only Real LLM Transport Minimal Implementation

Date: 2026-05-10
Status: planning guidance only.

## Goal

1. Make RAG answer capable of calling a real LLM through backend-owned config.
2. Keep the implementation backend-only, gated, and reversible.
3. Avoid UI provider rollout, Ask-schema expansion, and production-provider claims.

## Why This Lane Matters

1. The current MVP already proves retrieval, release grounding, and current-release query behavior.
2. Practical NumericWorkbench and planner Q&A need a real answer model rather than only deterministic or skeleton behavior.
3. This is the shortest useful path forward, but it must remain narrow and backend-owned.

## Entry Conditions

1. Start from the current `P3.external-provider-19` and P20 governance baseline.
2. Confirm `ExternalRagModelClient` gate order is still `enabled`, `transport_enabled`, payload normalization, allowlist, credential resolution, transport, response normalization.
3. Confirm allowlist hardening still requires non-empty allowed providers and models before credential or transport.
4. Confirm env credential source remains backend-owned and does not read request or frontend fields.
5. Confirm default behavior remains disabled or safe when config is missing.

## Allowed Scope

1. `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py`.
2. Narrowly related tests under `tests/unit/game/test_knowledge_rag_external_model_client.py`.
3. If necessary, narrow provider-selection or registry tests that prove no router or request ownership drift.
4. Closeout docs for P20.

## Forbidden Scope

1. No `console/src/**` provider or API-key UI.
2. No `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py` request schema expansion.
3. No `ProviderManager.active_model` RAG control.
4. No `SimpleModelRouter` RAG path connection.
5. No secret-store or admin credential UI.
6. No multiple-provider UI.
7. No production rollout, billing, quota, streaming, or conversation memory.

## Expected Effect

1. A backend-configured real LLM can be exercised for RAG answer in a controlled environment.
2. GameProject Ask behavior remains the same from the UI and API perspective.
3. The feature can be killed by config without code changes.
4. This is real transport enablement for a narrow backend path, not production provider rollout.

## Minimum Validation

1. Disabled adapter never normalizes payload and never resolves credentials.
2. `transport_enabled=False` never resolves credentials or calls transport.
3. Missing allowlist blocks before resolver and transport.
4. Disallowed provider blocks before resolver and transport.
5. Disallowed model blocks before resolver and transport.
6. Missing env credential safe-fails.
7. Successful env credential plus injected or real transport produces normalized response.
8. Provider raw error maps to safe warning without leaking secrets.
9. Request-like provider, model, or api_key fields remain ignored.
10. Router Ask schema remains unchanged.
11. Focused five-file RAG suite passes.

## Closeout Wording

1. If implemented, write `P20 backend-only real HTTP transport minimal implementation completed`.
2. Do not write `production provider rollout completed`.
3. Do not write `Ask request now supports provider/model/api_key`.
4. Do not write `frontend provider selector implemented`.

## Prompt Seed For GPT-5.4

```text
接手当前仓库，只执行 Lane B: P20 backend-only real LLM transport minimal implementation。
先阅读 docs/tasks/post-mvp/engineering-roadmap-2026-05-10.md、docs/tasks/post-mvp/lane-b-p20-backend-real-llm-transport-2026-05-10.md 和 docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md 的 P20 相关历史段落。
不要改 GameProject Ask request schema，不要改 frontend provider/model/API-key UI，不要让 router 选择 provider，不要接 ProviderManager.active_model 或 SimpleModelRouter。
只在 backend-owned config/env credential/allowlist/gate 已满足时允许 real HTTP transport path。
默认关闭，失败安全降级，所有 secret 和 provider raw errors 必须 redacted。
完成后跑 focused RAG provider tests、router schema regression、git diff --check、NUL check、keyword boundary review，并新增 P20 closeout 文档。
```
