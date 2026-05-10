# Knowledge P3.external-provider-14 Credential Resolver Boundary And Implementation Plan

Date: 2026-05-09

Authority:

1. docs/tasks/knowledge-p3-external-provider-13-real-transport-skeleton-closeout-2026-05-09.md
2. docs/tasks/knowledge-p3-external-provider-12-real-transport-skeleton-implementation-plan-2026-05-09.md
3. docs/tasks/knowledge-p3-external-provider-11-gate-order-hardening-closeout-2026-05-09.md
4. docs/tasks/knowledge-p3-external-provider-10-allowlist-hardening-closeout-2026-05-09.md
5. docs/tasks/knowledge-p3-external-provider-9-real-transport-design-review-2026-05-09.md
6. docs/tasks/knowledge-p0-p3-implementation-checklist.md
7. docs/tasks/knowledge-p3-gate-status-2026-05-07.md
8. docs/tasks/knowledge-p3-gate-consolidation-2026-05-08.md
9. src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py
10. src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py
11. src/ltclaw_gy_x/game/knowledge_rag_model_registry.py
12. src/ltclaw_gy_x/game/knowledge_rag_answer.py
13. src/ltclaw_gy_x/app/routers/game_knowledge_rag.py
14. src/ltclaw_gy_x/game/service.py
15. src/ltclaw_gy_x/security/secret_store.py
16. src/ltclaw_gy_x/providers/provider_manager.py
17. src/ltclaw_gy_x/providers/provider.py
18. src/ltclaw_gy_x/app/routers/providers.py
19. tests/unit/game/test_knowledge_rag_external_model_client.py
20. tests/unit/game/test_knowledge_rag_answer.py
21. tests/unit/game/test_knowledge_rag_provider_selection.py
22. tests/unit/game/test_knowledge_rag_model_registry.py
23. tests/unit/routers/test_game_knowledge_rag_router.py

## 一、本轮性质

1. 这是 docs-only implementation plan。
2. 不是 implementation。
3. 不是 credential rollout。
4. 不是 production provider rollout。
5. 不接真实 provider。
6. 不发真实 HTTP。
7. 不引入真实 credential。
8. 不读取真实 env var value。
9. 不新增 API。
10. 不改 frontend。
11. 不改 Ask request schema。
12. 不改 router provider 选择权。
13. 不接入 `ProviderManager.active_model`。
14. 不接入 `SimpleModelRouter`。

本轮只记录下一轮 credential resolver skeleton 或 backend-owned credential source boundary 的施工图纸。

## 源码基线结论

本计划以当前源码和当前测试为准，而不是以前序文档假设为准。

当前源码可确认的事实：

1. P10 allowlist hardening 已完成，`transport_enabled=True` 时缺失、空值、空白值或不命中的 provider/model allowlist 仍会在 resolver 和 transport 之前阻断执行。
2. P11 gate-order hardening 已完成，`enabled=False` 和 `transport_enabled=False` 仍在 payload normalization 之前短路返回。
3. P13 non-network transport skeleton 已完成，`ExternalRagModelHttpTransportSkeleton` 已存在，默认不会发真实网络。
4. `ExternalRagModelClient` 当前仍只接受 injected `credential_resolver`。
5. 当前没有真实 credential resolver。
6. `ExternalRagModelEnvConfig.api_key_env_var` 当前只是一段 backend-owned env metadata shape，不会读取 env value。
7. 当前没有 RAG path 的 secret-store integration。
8. 当前没有 RAG path 的 config-file secret value read。
9. 当前没有 request、frontend、admin UI 驱动的 credential input for this RAG path。
10. Ask request schema 仍只有 `query`、`max_chunks`、`max_chars`。
11. router 不选择 provider，也不直接调用 registry。
12. `ProviderManager.active_model` 不参与 RAG provider selection。
13. `SimpleModelRouter` 不在 RAG path。
14. `no_current_release` 和 `insufficient_context` 仍在 provider init 之前早返回。
15. `candidate_evidence` 不自动进入 RAG provider 输入。

只读审查还确认了两点与后续规划直接相关的仓库事实：

1. 仓库里存在 `src/ltclaw_gy_x/security/secret_store.py` 和 provider-manager 持久化能力，但它们当前没有接进这条 RAG external-provider path。
2. provider 管理相关 API 与 UI 已在仓库其它表面存在，但这些能力当前不属于 Ask RAG path 的授权或配置来源。

如果后续需要真实 secret source、provider manager bridge、admin config path 或 rollout switch，必须另起独立 review 或 implementation slice。

## 二、下一轮 credential resolver skeleton 的允许施工范围

下一轮最多允许改这些源码：

1. `src/ltclaw_gy_x/game/knowledge_rag_external_model_client.py`

只有确有必要时才允许窄改：

1. `src/ltclaw_gy_x/game/knowledge_rag_provider_selection.py`
2. `src/ltclaw_gy_x/game/knowledge_rag_model_registry.py`
3. `src/ltclaw_gy_x/game/knowledge_rag_answer.py`

下一轮不允许改：

1. `src/ltclaw_gy_x/app/routers/game_knowledge_rag.py`
2. `console/src/`
3. provider manager runtime behavior
4. `src/ltclaw_gy_x/game/service.py`
5. Ask request/response schema
6. admin UI
7. production provider config UI

## 三、下一轮允许做什么

建议下一轮只允许做 credential resolver skeleton，不接真实 secret source：

1. 新增明确命名的 backend-only credential resolver skeleton 或 helper。
2. resolver skeleton 默认不读取任何真实 secret。
3. resolver skeleton 可以验证 `ExternalRagModelCredentialRequest` shape。
4. resolver skeleton 可以按默认行为返回 `None` 或 safe not-configured behavior。
5. resolver skeleton 可以支持 injected mapping 或 test double，但只用于 tests。
6. resolver skeleton 可以保留 env var name metadata 的只读透传，但不能读取 env var value。
7. resolver skeleton 必须与 P13 non-network transport skeleton 并存，且不能把它变成 production transport。
8. resolver skeleton success path 只能配合 injected test transport 验证，不得触发真实 network。

## 四、下一轮仍禁止做什么

下一轮 implementation 仍明确禁止：

1. 不接生产 provider。
2. 不发真实 HTTP。
3. 不引入真实 API key。
4. 不读取真实 env var value。
5. 不读取 secret store。
6. 不读取 config file secret value。
7. 不新增 Ask request provider/model/api_key。
8. 不新增 Ask request credential 字段。
9. 不改 frontend。
10. 不给 router credential 或 provider 或 model 选择权。
11. 不把 `ProviderManager.active_model` 接进 RAG provider selection。
12. 不把 `SimpleModelRouter` 接进 RAG path。
13. 不做 credential store。
14. 不做 admin UI。
15. 不做 runtime rollout。
16. 不做 production transport。
17. 不做 cost billing 或 real quota。
18. 不把 `candidate_evidence` 自动送入 provider。

## 五、credential resolver contract

下一轮 resolver skeleton 必须遵守以下契约：

1. 输入只允许 `ExternalRagModelCredentialRequest`。
2. request 里只允许使用 `provider_name`、`model_name` 和 env var name metadata，不允许读取 env var value。
3. 输出只允许是 `ExternalRagModelClientCredentials` 或 `None`。
4. credentials object 只允许 `api_key` 和 `endpoint`，且 `endpoint` 只能在确有必要时存在。
5. resolver 不得返回 provider 或 model selection。
6. resolver 不得修改 config。
7. resolver 不得 fallback 到另一个 provider。
8. resolver 不得从 request body 读取任何字段。
9. resolver 不得从 frontend 读取任何字段。
10. resolver 不得记录 secret value。
11. resolver 抛异常时，最终行为必须映射为 not configured 或 safe warning，不得泄露 raw message。

当前源码相关事实需要保持：

1. missing resolver 仍应退化为 `External provider adapter skeleton is not configured.`。
2. blank credential 仍应退化为 `External provider adapter skeleton is not configured.`。
3. 当前 `_resolve_credentials()` 已经把 `None` resolver、`None` credential、blank api_key` 都统一映射到 not configured；下一轮应保持这种收口行为，而不是引入多条泄露式错误通道。

## 六、secret source policy

后续真实 credential source 仍需要单独 review。

本轮建议冻结：

1. env var name 可以来自 backend-owned config。
2. env var value 不得在 P14 或 P15 中读取，除非另起明确 implementation slice。
3. secret store integration 不在下一轮范围内。
4. config file secret value 不在下一轮范围内。
5. docs、tasks、map、formal map、snapshot、export 不得包含 credential。
6. tests 不得包含真实 secret-like key。
7. fixture 只能使用 placeholder。
8. credential source 优先级不得在本轮定为生产规则，只能作为 future review item。
9. 任何真实 secret source 接入前必须有 DLP 和 redaction tests。
10. 任何真实 secret source 接入前必须有 rollback 或 disable switch。

只读审查结论也必须写清：

1. `src/ltclaw_gy_x/security/secret_store.py` 已存在，但当前未接入本 RAG external-provider path。
2. `src/ltclaw_gy_x/providers/provider_manager.py` 已存在 provider credential 持久化与解密能力，但当前未作为此 RAG path 的 credential source。
3. `src/ltclaw_gy_x/app/routers/providers.py` 与 provider config request API 也存在，但当前未授权进入 Ask RAG path。

## 七、redaction / DLP

计划必须冻结以下 redaction、DLP 与 logging 规则：

1. API key 不得进入 prompt payload。
2. API key 不得进入 request preview。
3. API key 不得进入 warnings。
4. API key 不得进入 error responses。
5. API key 不得进入 exceptions。
6. API key 不得进入 logs。
7. API key 不得进入 docs 或 tasks。
8. API key 不得进入 snapshot 或 formal map 或 export。
9. `Authorization` header 不得出现。
10. endpoint 如含 secret query string，不得进入 warning 或 error 或 preview。
11. credential request logging 默认禁止。
12. provider raw response 默认不得记录。
13. NUL 检查仍作为触及文件验证项。
14. DLP 相关失败必须阻断后续 rollout。

## 八、与 P13 transport skeleton 的关系

计划必须明确：

1. P13 skeleton transport 已存在。
2. P14 或 P15 credential resolver skeleton 不得把 P13 变成 production transport。
3. 即使 resolver skeleton 存在，默认也不得发真实 HTTP。
4. `transport_enabled=True` 仍必须经过 P10 allowlist。
5. `enabled` 与 `transport_enabled` 仍必须保持 P11 gate order。
6. default transport skeleton safe failure 仍可用。
7. injected transport tests 仍是主要 success/failure 验证路径。
8. resolver skeleton success 只能配合 injected test transport，不得触发真实 network。

## 九、API/router/frontend 边界

计划必须冻结：

1. Ask request schema 不新增 provider 或 model 或 api_key 或 credential。
2. router 不直接调用 registry。
3. router 不选择 provider。
4. router 不创建 resolver。
5. router 不创建 transport。
6. router 只把 `game_service` 交给 answer service。
7. request 注入 provider 或 model 或 api_key 或 service_config 或 credential 仍被忽略。
8. frontend 不出现 provider 或 model 或 API key 输入。
9. `ProviderManager.active_model` 不参与 RAG provider selection。
10. `SimpleModelRouter` 不得接入 RAG path。
11. 管理员配置路径必须另起 review，不混入普通 Ask。

## 十、测试矩阵

下一轮 implementation 必须使用这些 focused test files：

1. `tests/unit/game/test_knowledge_rag_external_model_client.py`
2. `tests/unit/game/test_knowledge_rag_answer.py`
3. `tests/unit/game/test_knowledge_rag_provider_selection.py`
4. `tests/unit/game/test_knowledge_rag_model_registry.py`
5. `tests/unit/routers/test_game_knowledge_rag_router.py`

external client 或 credential resolver 必测：

1. resolver skeleton default returns `None` or safe not configured。
2. resolver skeleton does not read `os.environ`。
3. resolver skeleton does not read files。
4. resolver skeleton does not open socket。
5. resolver skeleton does not access secret store。
6. resolver skeleton request uses `provider_name`、`model_name`、env metadata only。
7. resolver skeleton output does not contain logs or warnings。
8. missing resolver remains not configured。
9. blank credential remains not configured。
10. resolver exception maps to safe not configured or safe warning without raw secret。
11. injected credential resolver success still works with injected transport。
12. injected credential resolver success with default skeleton still safe-fails without network。
13. api_key does not enter preview or payload or warnings or errors。
14. endpoint query string remains redacted。
15. P10 allowlist failures block resolver。
16. P11 disabled or not-connected gates block resolver before payload normalization。
17. P13 default skeleton safe failure remains redacted。

answer 层必测：

1. external warning response degrades to `insufficient_context`。
2. provider answer with valid grounded citation returns `answer`。
3. provider answer without citation degrades。
4. provider answer with out-of-context citation degrades。
5. `no_current_release` does not initialize resolver or provider。
6. `insufficient_context` does not initialize resolver or provider。

router 必测：

1. request injection provider 或 model 或 api_key 或 credential 或 service_config ignored。
2. router does not call registry。
3. router does not create resolver。
4. Ask schema unchanged。

## 十一、文档完成标准

本轮新增 plan 文档只有在以下内容都写清楚时才算完成：

1. P14 是 docs-only implementation plan。
2. P14 不改变 runtime。
3. 下一轮仍不是 production rollout。
4. 下一轮 credential resolver skeleton 仍不读取真实 secret。
5. 下一轮仍不发真实 HTTP。
6. 下一轮仍不改 API 或 router 或 frontend。
7. P10、P11、P13 是下一轮前置条件，且已经完成。
8. 下一步建议是 P15 credential resolver skeleton implementation 或 admin config boundary review，而不是 production rollout。

## 十二、源代码与前序文档差异处理

如果前序文档和当前源码不一致，必须以当前源码为准，并把差异写成风险或待补项，而不是写成已完成能力。

当前需要保留的源码优先结论：

1. 当前 RAG path 没有 secret-store integration。
2. 当前 RAG path 没有 env credential loading。
3. 当前 RAG path 没有 provider-manager-based credential loading。
4. 当前 Ask path 没有 request-owned credential source。
5. 当前 default transport 仍是 non-network safe-failure skeleton。

## 十三、推荐下一步

下一步建议不是 production rollout。

下一步建议是：

1. `P3.external-provider-15` credential resolver skeleton implementation，仍保持 backend-only、non-production、non-network。
2. 或者单独做 admin config boundary review，定义未来 backend-owned provider credential governance path，但仍不混入 Ask。

## 十四、验证说明

本轮是 docs-only。

本轮不跑 pytest。

本轮不跑 TypeScript。

本轮 post-edit validation 仅限：

1. `git diff --check` on touched docs files
2. NUL-byte scan on touched docs files
3. keyword review 确认文本没有声称 completed rollout、completed credential resolver、completed credential store、completed env credential loading 或 production credential enablement