# Knowledge P3.external-provider-17 Backend Env-Var Credential Source Implementation Plan

Date: 2026-05-09
Scope: docs-only implementation plan
Source of truth: current source files and focused tests under `src/ltclaw_gy_x/game/`, `src/ltclaw_gy_x/security/`, `src/ltclaw_gy_x/providers/`, `src/ltclaw_gy_x/app/routers/`, and current P10-P16 task records

## 一、当前状态结论

本轮结论必须以当前源码为准，而不是以前序文档假设为准。

当前源码和当前 docs 基线确认：

1. P17 是 docs-only implementation plan。
2. P17 不实现 env credential source。
3. P17 不读取 env value。
4. P17 不接 secret store。
5. P17 不接 `ProviderManager`。
6. P17 不接 `SimpleModelRouter`。
7. P17 不接真实 HTTP。
8. P17 不接真实 provider。
9. 当前真实 credential source 数量仍为 0。
10. P18 才可能实现最小 env-var credential source。
11. P10 allowlist hardening 已完成。
12. P11 gate-order hardening 已完成。
13. P13 non-network transport skeleton 已完成。
14. P15 credential resolver skeleton 已完成。
15. P16 credential source governance boundary 已完成。
16. 当前 resolver skeleton 默认返回 `None`。
17. 当前没有 env value read。
18. 当前没有 secret store integration。
19. 当前没有 `ProviderManager` credential loading。
20. 当前没有 `SimpleModelRouter` 接入 RAG path。
21. 当前没有真实 HTTP。
22. 当前没有真实 provider。
23. Ask request schema 仍只有 `query`、`max_chunks`、`max_chars`。
24. router 仍不选择 provider，也不直接调用 provider registry。
25. frontend 仍没有 provider、model、API key 输入。
26. formal knowledge acceptance 仍只管是否进入正式知识库，不管 runtime credential approval。

只读审查还确认：

1. `ExternalRagModelEnvConfig.api_key_env_var` 已存在于当前 backend-owned config shape 中，但当前仍只是 metadata。
2. `secret_store.py`、provider manager、provider router 相关表面在仓库里存在，但当前都不属于这条 RAG credential path。
3. 当前 `future_external` 进入 runtime path 仍然必须经过 backend-owned external config、P10 allowlist、P11 gate order、P15 resolver seam 和 P13 transport skeleton，而不是 request、frontend 或 router ownership。

## 二、source 选择结论

P18 的最小候选 source 明确选择为 backend env-var credential source。

明确结论：

1. P18 的最小候选 source 是 backend env-var credential source。
2. 选择理由是当前代码已经有 `ExternalRagModelEnvConfig.api_key_env_var` 元数据字段。
3. 该方向保持 backend-owned，不需要 request、frontend 或 router 参与。
4. 该方向不需要 admin UI。
5. 该方向不需要 secret store。
6. 该方向不需要 `ProviderManager`。
7. 该方向适合先验证 resolver source contract、DLP、redaction 和 safe-failure semantics。
8. 这不是最终长期 credential architecture。
9. secret store、keychain、deployment-managed secret reference、admin-managed secret reference 都留给后续 review。
10. P18 只能做一个 source，不能同时接 env 和 secret store。
11. 不允许 silent fallback 到其他 source。

本轮必须避免误写：

1. 本轮并没有批准 env source 作为长期默认方案。
2. 本轮只是为最小可验证实现选择一个最窄 backend-owned candidate。
3. 本轮没有批准 production rollout。

## 三、P18 最小施工范围

P18 必须保持为一个最小、局部、可验证的 backend-only implementation。

允许 P18 修改：

1. `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py`
2. `tests/unit/game/test_knowledge_rag_external_model_client.py`
3. 必要时窄改：
4. `tests/unit/game/test_knowledge_rag_answer.py`
5. `tests/unit/game/test_knowledge_rag_provider_selection.py`
6. `tests/unit/game/test_knowledge_rag_model_registry.py`
7. `tests/unit/routers/test_game_knowledge_rag_router.py`
8. docs closeout 和三份汇总文档。

P18 不允许修改：

1. `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py`
2. `console/src`
3. `ProviderManager`
4. `SimpleModelRouter`
5. `secret_store.py`
6. provider routers
7. admin UI 或 admin API
8. Ask request 或 response schema
9. map、formal map、snapshot、export writers

P18 的最小代码目标应该只包含：

1. 在 external client 内部引入 env-var credential source helper 或 resolver branch。
2. 保持现有 injected resolver seam 仍可用。
3. 保持 current warning mapping、allowlist order、transport order、request boundary 和 response normalization 路径不变。

## 四、P18 resolver contract

P18 未来实现必须遵守以下规则：

1. env var name 只能来自 backend-owned `ExternalRagModelEnvConfig.api_key_env_var`。
2. env var name 不得来自 request body。
3. env var name 不得来自 frontend。
4. env var name 不得来自 router。
5. env var name 不得来自 map、formal map、snapshot、export、docs、tasks。
6. env var value 只允许在 P18 resolver 内部读取。
7. env var value 读取必须发生在 `enabled=True`、`transport_enabled=True`、payload normalization 已通过、provider 或 model allowlist 已通过之后。
8. `enabled=False` 时不得读取 env。
9. `transport_enabled=False` 时不得读取 env。
10. allowlist failure 时不得读取 env。
11. missing env config -> not configured。
12. blank env var name -> not configured。
13. missing env var value -> not configured。
14. blank env var value -> not configured。
15. env read exception -> safe not configured。
16. env value 不得进入 returned credential repr、log、warning、error。
17. resolver exception 不得泄露 env var value。
18. 不允许 fallback 到 secret store。
19. 不允许 fallback 到 `ProviderManager`。
20. 不允许 fallback 到 request、frontend、router。

与当前源码一致的 gate 顺序必须保持：

1. enabled gate
2. transport-enabled gate
3. payload normalization
4. allowlist validation
5. credential resolution
6. transport invocation
7. response normalization

P18 不得把 env read 前移到任何更早的 gate 前面。

## 五、DLP / redaction / logging 要求

P18 如果进入实现，必须满足以下强制要求：

1. API key 不进 prompt payload。
2. API key 不进 request preview。
3. API key 不进 warnings。
4. API key 不进 error response。
5. API key 不进 docs 或 tasks。
6. API key 不进 map。
7. API key 不进 formal map。
8. API key 不进 snapshot。
9. API key 不进 export。
10. API key 不进 fixture。
11. API key 不进普通日志。
12. `Authorization` header 不记录。
13. endpoint query string 继续 redacted。
14. provider raw response 默认不记录。
15. resolver exception 原文不暴露。
16. DLP 失败必须阻断 rollout。

额外要求：

1. env var name 可以作为 backend-owned metadata 出现，但 env var value 不得出现在 docs、logs、warnings、errors、preview 或 fixtures。
2. P18 closeout 必须明确复核这一点，而不是只靠实现意图描述。

## 六、runtime gate / rollback 要求

P18 必须保持并强化当前 runtime gate 与 rollback 语义：

1. `enabled=False` 是 adapter kill switch。
2. `transport_enabled=False` 是 transport + credential kill switch。
3. allowlist 移除 provider 或 model 必须阻断 env read。
4. 删除 env var 或置空 env var value 必须 safe not-configured。
5. env read exception 必须 safe not-configured。
6. rollback 不需要改 frontend。
7. rollback 不需要改 request body。
8. rollback 不依赖 formal knowledge acceptance。
9. 不允许 silent switch 到另一个 provider。
10. 不允许 silent switch 到另一个 credential source。

P18 实现前必须明确：

1. rollback 触发面只能来自 backend-owned config 和 environment state。
2. rollback 后 ordinary Ask path 仍应表现为当前 safe warnings，而不是暴露内部故障。

## 七、formal knowledge / fast test 边界

P18 计划必须继续冻结 formal knowledge 与 runtime credential governance 的分离：

1. 管理员接受只用于是否进入正式知识库。
2. 管理员接受不用于 runtime credential approval。
3. 管理员接受不用于 provider rollout。
4. 管理员接受不用于普通快速测试。
5. 普通快速测试不得携带真实 credential。
6. 普通快速测试不得被管理员接受流程阻塞。
7. runtime credential governance 是另一条 backend-owned 治理线。
8. env var name 或 value 不得写入 formal knowledge。

这部分必须继续与 P16 保持一致，避免把知识资产治理和 runtime credential governance 混线。

## 八、P18 测试矩阵

P18 未来 implementation 必测项至少包括：

1. default resolver skeleton 仍 safe not-configured。
2. env resolver disabled gate 不读 env。
3. env resolver `transport_enabled=False` 不读 env。
4. env resolver allowlist failure 不读 env。
5. env resolver missing env config -> not configured。
6. env resolver blank env var name -> not configured。
7. env resolver missing env var value -> not configured。
8. env resolver blank env var value -> not configured。
9. env resolver reads env only after allowlist success。
10. env resolver success + injected transport success works。
11. env resolver success + default P13 transport skeleton safe-fails without network。
12. env resolver exception redacted。
13. env value not in prompt payload。
14. env value not in request preview。
15. env value not in warning or error response。
16. request body provider、model、api_key ignored。
17. frontend has no provider、model、api_key input。
18. router schema unchanged。
19. `ProviderManager` not accessed。
20. `SimpleModelRouter` not accessed。
21. `secret_store` not accessed。
22. no fallback to other source。
23. endpoint query string still redacted。
24. focused five-file suite passes。

建议 P18 继续聚焦这些测试文件：

1. `tests/unit/game/test_knowledge_rag_external_model_client.py`
2. `tests/unit/game/test_knowledge_rag_answer.py`
3. `tests/unit/game/test_knowledge_rag_provider_selection.py`
4. `tests/unit/game/test_knowledge_rag_model_registry.py`
5. `tests/unit/routers/test_game_knowledge_rag_router.py`

## 九、P18 closeout expectations

P18 如果进入实现，closeout 至少必须新增或同步：

1. `docs/tasks/knowledge/mvp/knowledge-p3-external-provider-18-env-credential-source-closeout-2026-05-09.md`
2. 三份汇总文档同步。
3. focused pytest 结果。
4. `git diff --check`。
5. NUL 检查。
6. 禁止性关键词复核。
7. 明确仍不是 production provider rollout。
8. 明确仍没有真实 HTTP，除非另一个独立 slice 批准。

P18 closeout 还必须明确写出：

1. env read 只发生在 resolver 内部。
2. env value 不进入 docs、logs、warnings、errors、preview、fixtures。
3. `ProviderManager`、`SimpleModelRouter`、`secret_store` 仍未接入。

## 十、下一步建议

下一步建议必须收敛为：

1. `P18` backend env-var credential source implementation。

本轮明确不建议：

1. production rollout
2. 直接接真实 provider
3. 直接接 secret store
4. 直接接 `ProviderManager`
5. 直接改 frontend
6. 直接改 router request schema
7. 直接做 admin UI

## 验证说明

本轮是 docs-only implementation plan。

本轮不改任何源码。

本轮不改任何测试。

本轮不跑 pytest。

本轮不跑 TypeScript。

本轮 post-edit validation 仅限：

1. `git diff --check` on touched docs files
2. NUL-byte scan on touched docs files
3. keyword review 确认文本没有声称已完成 env credential source、real provider rollout、real HTTP enablement、frontend provider selector、request-owned credential input 或 admin credential UI