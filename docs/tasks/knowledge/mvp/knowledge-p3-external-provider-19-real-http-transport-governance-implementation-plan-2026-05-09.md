# Knowledge P3.external-provider-19 Backend-Only Real HTTP Transport Governance And Implementation Plan

Date: 2026-05-09
Scope: docs-only implementation plan
Source of truth: current source files and focused tests under `src/ltclaw_gy_x/game/`, `src/ltclaw_gy_x/app/routers/`, `tests/unit/game/`, `tests/unit/routers/`, plus read-only review of `src/ltclaw_gy_x/security/secret_store.py`, `src/ltclaw_gy_x/providers/provider_manager.py`, `src/ltclaw_gy_x/providers/provider.py`, and `src/ltclaw_gy_x/app/routers/providers.py`

## 一、当前状态结论

本轮结论必须以当前源码为准，而不是以历史文档假设为准。

明确结论：

1. P19 是 docs-only implementation plan。
2. P19 不实现真实 HTTP。
3. P19 不接真实 provider。
4. P19 不做 production rollout。
5. P18 后，当前 Ask RAG runtime 已有最小 backend env-var credential source。
6. P13 transport 仍是 non-network skeleton。
7. 当前真实 HTTP transport 数量仍为 0。
8. 当前真实 provider rollout 数量仍为 0。
9. P20 才可能实现最小 real HTTP transport skeleton 或 minimal transport。
10. 即使 P20 实现 real HTTP transport，也不得自动等于 production rollout。

当前源码基线必须写清：

1. P10 allowlist hardening 已完成。
2. P11 gate-order hardening 已完成。
3. P13 non-network transport skeleton 已完成。
4. P15 credential resolver skeleton 已完成。
5. P18 backend env-var credential source 已完成。
6. 当前 env read 只通过 backend-owned `ExternalRagModelEnvConfig.api_key_env_var`。
7. 当前 env read 只发生在 enabled gate、transport_enabled gate、payload normalization、allowlist validation 之后。
8. 当前 default P13 transport skeleton 仍 non-network。
9. 当前没有真实 HTTP transport。
10. 当前没有真实 provider rollout。
11. 当前没有 `secret_store` integration。
12. 当前没有 `ProviderManager` credential loading。
13. 当前没有 `SimpleModelRouter` 接入 RAG path。
14. Ask request schema 仍只有 `query`、`max_chunks`、`max_chars`。
15. router 仍不选择 provider，也不直接调用 provider registry。
16. frontend 仍没有 provider、model、API key 输入。
17. formal knowledge acceptance 仍只管是否进入正式知识库，不管 runtime credential approval 或 provider rollout。
18. 当前 RAG runtime 唯一已实现的真实 credential source 是 P18 backend env-var credential source。

只读源码审查补充结论：

1. `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py` 中 `ExternalRagModelEnvCredentialResolver.__call__(...)` 在返回 credentials 之后仍留有一个不可达 `return None`。
2. 该不可达语句应记录为 future code cleanup。
3. 本轮是 docs-only slice，不在 P19 修改该源码。
4. `src/ltclaw_gy_x/security/secret_store.py`、`src/ltclaw_gy_x/providers/provider_manager.py`、`src/ltclaw_gy_x/app/routers/providers.py` 以及 `src/ltclaw_gy_x/providers/provider.py` 在仓库中真实存在，但当前未被授权接入 Ask RAG path。
5. `src/ltclaw_gy_x/game/service.py` 中 `SimpleModelRouter` 仍是另一条模型桥接线，不属于当前 RAG external-provider runtime surface。

## 二、P20 目标选择

P20 的目标必须继续收敛在 transport implementation，而不是 rollout。

明确结论：

1. P20 的目标应是 backend-only real HTTP transport minimal implementation 或 transport adapter skeleton。
2. P20 只能处理 transport contract、request building、timeout 或 error mapping、response normalization 和 redaction。
3. P20 不得改 credential source。
4. P20 不得改 router。
5. P20 不得改 frontend。
6. P20 不得改 Ask schema。
7. P20 不得接 `ProviderManager`。
8. P20 不得接 `SimpleModelRouter`。
9. P20 不得接 `secret_store`。
10. P20 不得做 production rollout。
11. P20 不得新增第二个 provider。
12. P20 不得把 `candidate_evidence` 自动送入 provider。

P20 的最小目标不是“上线真实 provider”，而是“在现有 backend-owned gates 内，为未来 real HTTP call 形成最小 transport contract 与可验证的安全失败路径”。

## 三、P20 最小代码施工范围

允许 P20 修改的最小范围：

1. `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py`
2. `tests/unit/game/test_knowledge_rag_external_model_client.py`
3. 必要时窄改：
4. `tests/unit/game/test_knowledge_rag_answer.py`
5. `tests/unit/game/test_knowledge_rag_provider_selection.py`
6. `tests/unit/game/test_knowledge_rag_model_registry.py`
7. `tests/unit/routers/test_game_knowledge_rag_router.py`
8. P20 closeout 文档与三份汇总文档。

P20 不允许修改：

1. `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py`
2. `console/src`
3. `ProviderManager`
4. `SimpleModelRouter`
5. `secret_store.py`
6. provider routers
7. admin UI 或 admin API
8. Ask request schema 或 response schema
9. map、formal map、snapshot、export writers

P20 的 allowed surface 仍必须以 `knowledge_rag_external_model_client.py` 为中心，任何超出该面的 widening 都应视为超范围。

## 四、real HTTP transport contract

未来 P20 如果进入实现，必须遵守以下 transport contract：

1. transport 只能接收 normalized RAG prompt payload。
2. transport 输入不得包含 request-owned provider、model、api_key。
3. transport 输入不得包含 raw credential object in payload。
4. `Authorization` header 只能在 transport 内部构造，不得进入 preview、warning、error 或 log。
5. endpoint 或 base_url 必须来自 backend-owned config。
6. endpoint 或 base_url 不得来自 request body。
7. endpoint 或 base_url 不得来自 frontend。
8. endpoint 或 base_url 不得来自 router。
9. endpoint query string 不得记录。
10. timeout 必须有固定上限。
11. response 必须先转换成 internal mapping，再经过 `_normalize_response(...)`。
12. transport 不得绕过 answer 层 grounding。
13. empty answer、invalid `citation_ids`、invalid `warnings`、oversize output 都必须 safe map。
14. provider raw response 默认不得记录。
15. provider raw error 原文不得暴露给普通用户。
16. provider timeout 必须映射到 `External provider adapter skeleton timed out.`。
17. provider HTTP error 必须映射到 `External provider adapter skeleton HTTP error.`。
18. invalid provider response 必须映射到 `External provider adapter skeleton returned an invalid response.`。
19. unknown transport failure 必须映射到 `External provider adapter skeleton request failed.`。
20. `no_current_release` 与 `insufficient_context` early return 不得初始化 provider 或 transport。

补充治理要求：

1. real HTTP transport 只能消费 backend-owned provider selection、backend-owned model selection、backend-owned base_url 或 proxy config、以及 backend-owned credential result。
2. transport preview 仍应保持 redacted shape，而不是记录 raw request。
3. 即使 future P20 允许 real HTTP adapter，也不能把 transport contract 扩大成“provider rollout approval”。

## 五、network / rollout gate

未来 P20 如果实现 real HTTP transport，也必须继续受现有 runtime gate 约束：

1. P20 即使实现 real HTTP transport，也必须默认受 enabled 和 transport_enabled 控制。
2. `enabled=False` 必须阻断 credential resolution 和 transport。
3. `transport_enabled=False` 必须阻断 credential resolution 和 transport。
4. allowlist failure 必须阻断 credential resolution 和 transport。
5. missing env credential 必须阻断 transport。
6. blank env credential 必须阻断 transport。
7. env read exception 必须阻断 transport。
8. rollback 只需要 backend config 或 env state，不需要 frontend 或 request body。
9. 不允许 silent switch 到另一个 provider。
10. 不允许 silent switch 到另一个 credential source。
11. 不允许 fallback 到 `ProviderManager`。
12. 不允许 fallback 到 `SimpleModelRouter`。
13. 不允许 fallback 到 `secret_store`。

补充说明：

1. 当前 env credential source 仍是唯一已实现 source，因此 P20 transport gate 必须把 credential source 视为既有前置，而不是扩展 source scope。
2. transport rollout gate 与 provider rollout gate 是两层不同治理面，P20 最多能实现 transport adapter，不得借此声明 provider 已可对外生产启用。

## 六、DLP / redaction / logging 要求

未来 P20 implementation 必须继续满足以下 DLP、redaction 与 logging 规则：

1. API key 不进 prompt payload。
2. API key 不进 request preview。
3. API key 不进 warning。
4. API key 不进 error response。
5. API key 不进 docs 或 tasks。
6. API key 不进 map。
7. API key 不进 formal map。
8. API key 不进 snapshot。
9. API key 不进 export。
10. API key 不进 fixture。
11. API key 不进普通日志。
12. `Authorization` header 不记录。
13. endpoint query string 必须 redacted。
14. proxy query string 必须 redacted。
15. provider raw response 默认不记录。
16. provider raw error 默认不记录。
17. resolver exception 原文不暴露。
18. transport exception 原文不暴露。
19. DLP 失败必须阻断 rollout。

额外要求：

1. 即使 future P20 使用“real HTTP”字样，文档、日志和错误文本也必须明确区分 planned 或 internal transport behavior 与 production rollout。
2. 任何把 secret-like material 写入 docs、tasks、map、formal map、snapshot、export、fixture、warning、error response 或普通日志的实现，都应被视为阻断级失败。

## 七、formal knowledge / fast test 边界

P19 继续冻结 formal knowledge acceptance 与 runtime provider rollout 的分离：

1. 管理员接受只用于是否进入正式知识库。
2. 管理员接受不用于 runtime credential approval。
3. 管理员接受不用于 provider rollout。
4. 管理员接受不用于普通快速测试。
5. 普通快速测试不得携带真实 credential。
6. 普通快速测试不得绕过 backend-owned gates。
7. runtime credential governance 与 formal knowledge acceptance 是两条治理线。
8. real HTTP transport rollout 不得依赖 formal knowledge acceptance。

补充结论：

1. 普通快速测试仍应走现有 backend-owned runtime path，而不是借用 admin acceptance、provider manager 或外部配置面。
2. formal knowledge acceptance 不能被复用为 credential approval、transport approval 或 provider rollout approval。

## 八、P20 测试矩阵

未来 P20 implementation 必测项至少包括：

1. disabled gate 不读 env，不调用 transport。
2. `transport_enabled=False` 不读 env，不调用 transport。
3. allowlist provider failure 不读 env，不调用 transport。
4. allowlist model failure 不读 env，不调用 transport。
5. payload normalization failure 不读 env，不调用 transport。
6. missing env config -> not configured，且不调用 transport。
7. blank env var name -> not configured，且不调用 transport。
8. missing env value -> not configured，且不调用 transport。
9. blank env value -> not configured，且不调用 transport。
10. env read exception -> not configured，且不调用 transport。
11. env success + transport success -> normalized answer。
12. env success + transport timeout -> timed out warning。
13. env success + HTTP error -> HTTP error warning。
14. env success + invalid provider response -> invalid response warning。
15. env success + unknown transport exception -> request failed warning。
16. API key 不进入 request preview。
17. API key 不进入 warning 或 error response。
18. `Authorization` header 不进入 preview、log 或 error。
19. endpoint query string 被 redacted。
20. proxy query string 被 redacted。
21. request body provider、model、api_key ignored。
22. router schema unchanged。
23. frontend unchanged。
24. `ProviderManager` not accessed。
25. `SimpleModelRouter` not accessed。
26. `secret_store` not accessed。
27. `no_current_release` does not initialize provider 或 transport。
28. `insufficient_context` does not initialize provider 或 transport。
29. default non-network skeleton behavior remains covered if real transport is not explicitly selected。
30. focused five-file suite passes。

建议未来仍聚焦以下测试文件：

1. `tests/unit/game/test_knowledge_rag_external_model_client.py`
2. `tests/unit/game/test_knowledge_rag_answer.py`
3. `tests/unit/game/test_knowledge_rag_provider_selection.py`
4. `tests/unit/game/test_knowledge_rag_model_registry.py`
5. `tests/unit/routers/test_game_knowledge_rag_router.py`

## 九、P20 closeout expectations

如果 P20 进入实现，closeout 至少必须新增或同步：

1. `knowledge-p3-external-provider-20-real-http-transport-closeout-2026-05-09.md`
2. 三份汇总文档同步。
3. focused pytest 结果。
4. `git diff --check`。
5. NUL 检查。
6. 禁止性关键词复核。
7. 明确是否仍不是 production rollout。
8. 明确是否仍没有 router、request、frontend、provider-manager expansion。
9. 明确 DLP 或 redaction 结果。
10. 明确 rollback 或 kill switch 仍可用。

P20 closeout 还必须明确写出：

1. transport implementation 是否仍保持 backend-only。
2. request、frontend、router 是否仍未取得 provider 或 credential ownership。
3. `ProviderManager`、`SimpleModelRouter`、`secret_store` 是否仍未接入。
4. real HTTP transport implementation 与 production rollout 是否仍被清楚分离。

## 十、下一步建议

下一步建议必须继续收敛为：

1. P20 backend-only real HTTP transport minimal implementation。
2. 或 P20 backend-only real HTTP transport skeleton implementation。

本轮明确不建议：

1. production rollout
2. 直接接真实 provider 对外发布
3. 直接改 frontend
4. 直接改 router request schema
5. 直接接 `ProviderManager`
6. 直接接 `SimpleModelRouter`
7. 直接接 `secret_store`
8. 直接做 admin UI
9. 直接把普通快速测试接到真实 credential 或真实 provider

## 验证说明

本轮是 docs-only implementation plan。

本轮不改任何源码。

本轮不改任何测试。

本轮不跑 pytest。

本轮不跑 TypeScript。

本轮 post-edit validation 仅限：

1. `git diff --check` on touched docs files。
2. NUL-byte scan on touched docs files。
3. keyword review，确认没有把 P19 误写成已经实现真实 HTTP、真实 provider rollout、production transport enabled、frontend provider selector、request-owned provider selection、`ProviderManager` 接管 RAG，或 `SimpleModelRouter` 接入 RAG path。