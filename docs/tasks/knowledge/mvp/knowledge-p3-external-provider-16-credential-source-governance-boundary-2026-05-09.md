# Knowledge P3.external-provider-16 Credential Source Governance Boundary Review

Date: 2026-05-09
Scope: docs-only credential source governance boundary review
Source of truth: current source files and focused tests under `src/ltclaw_gy_x/game/`, `src/ltclaw_gy_x/security/`, `src/ltclaw_gy_x/providers/`, `src/ltclaw_gy_x/app/routers/`, and the current P10-P15 task records

## 一、当前状态结论

本轮结论必须以当前源码为准，而不是以未来设想为准。

当前源码可确认的事实：

1. P10 allowlist hardening 已完成。
2. P11 gate-order hardening 已完成。
3. P13 non-network transport skeleton 已完成。
4. P15 credential resolver skeleton 已完成。
5. P15 后只有 resolver skeleton。
6. 当前 `ExternalRagModelCredentialResolverSkeleton` 默认返回 `None`，只进入 safe not-configured path。
7. skeleton 默认不读取任何 secret。
8. backend runtime 仍然不能认为已有 production credential capability。
9. `future_external` 虽已进入 backend runtime allowlist，但真实 provider 仍未 rollout。
10. `transport_enabled=True` 仍不等于允许真实 secret source。
11. 当前真实 credential source 数量为 0。
12. 当前没有真实 env value read。
13. 当前没有 secret store integration。
14. 当前没有 config-file secret value read。
15. 当前没有 `ProviderManager` credential loading。
16. 当前没有 `SimpleModelRouter` 接入 RAG path。
17. 当前没有真实 provider。
18. 当前没有真实 HTTP。
19. Ask request schema 仍只有 `query`、`max_chunks`、`max_chars`。
20. router 仍不选择 provider，也不直接调用 provider registry。
21. frontend 仍没有 provider、model、API key 输入。

只读审查还确认：

1. `src/ltclaw_gy_x/security/secret_store.py` 在仓库内真实存在，但当前没有接入这条 RAG external-provider path。
2. `src/ltclaw_gy_x/providers/provider_manager.py`、`src/ltclaw_gy_x/providers/provider.py`、`src/ltclaw_gy_x/app/routers/providers.py` 在仓库内也真实存在，但它们当前不构成 Ask RAG path 的 credential source。
3. `src/ltclaw_gy_x/game/service.py` 中的 `SimpleModelRouter` 仍是另一条模型调用桥接线，不属于当前 RAG external-provider credential governance surface。

## 二、credential source governance 原则

未来真实 credential source 的治理必须先冻结以下原则，之后才能进入 implementation plan：

1. credential source 只能是 backend-owned。
2. credential source 不能来自 request body。
3. credential source 不能来自 frontend。
4. credential source 不能来自 router。
5. credential source 不能来自 map、formal map、snapshot、export、docs、tasks。
6. credential source 不能来自普通用户快速测试输入。
7. credential source 不能借用“管理员接受进入正式知识库”的流程。
8. 管理员接受只用于“是否进入正式知识库”，不用于快速测试、runtime provider selection 或 credential approval。
9. credential 配置如果未来需要管理界面，必须另起 admin config review，且只保存 secret reference 或 env var name，不保存 secret value。
10. 任何真实 secret source 上线前，必须有独立 implementation plan 和 rollback plan。

治理含义必须写清：

1. backend-owned config 可以声明 provider、model、allowlist、transport gate、env var name 或 secret reference 的元数据。
2. backend-owned config 不能在本轮被解释成已有 production credential capability。
3. 普通 Ask 路径仍然只能消费 backend 解释后的 provider/runtime config，而不能参与 credential ownership。
4. 普通用户快速测试与管理员正式知识治理是两条不同治理线，不能互相替代。

## 三、未来允许讨论的 source 类型

以下 source 类型只能作为未来候选讨论项，不得写成已实现：

1. env var value source
2. local secret store source
3. OS keychain / credential manager source
4. deployment-managed secret reference
5. admin-managed secret reference

本轮必须明确：

1. P16 不选择最终实现。
2. P16 不读取这些 source。
3. P16 只定义评审维度和禁止边界。
4. 任何 source 都必须经过 DLP、redaction、rollback、audit、test matrix 后才能 implementation。

未来评审维度至少应包括：

1. source ownership 是否 backend-only
2. source 是否可被 request、frontend、router 绕过
3. source miss 与 source error 是否能 safe-fail
4. source 是否支持 kill switch 与 rollback
5. source 是否会把 secret value 暴露到 docs、logs、warnings、errors、preview、fixtures
6. source 是否会与 `ProviderManager`、`SimpleModelRouter` 或管理员正式知识流程发生错误耦合

## 四、source precedence 草案

以下 precedence 只作为未来评审草案，不是当前行为，也不是已批准的生产规则：

1. `enabled=False` 或 `transport_enabled=False` 优先级最高，直接阻断。
2. allowlist 不通过时，任何 credential source 都不得解析。
3. explicit backend service config 必须存在。
4. backend service config 只能给 secret reference 或 env var name，不能给 secret value。
5. 单次 runtime 只允许一个明确 credential source 生效。
6. 不允许 silent fallback 到另一个真实 credential source。
7. credential source miss 必须 safe not-configured。
8. credential source error 必须 safe not-configured 或明确 safe warning。
9. 不允许 fallback 到 request body、frontend、`ProviderManager`、`SimpleModelRouter`。
10. 不允许 unknown provider 或 unknown model 自动选择 credential。

本草案还必须与当前源码基线对齐：

1. disabled gate 必须继续早于 payload normalization。
2. not-connected gate 必须继续早于 payload normalization。
3. allowlist failure 必须继续早于 credential resolution。
4. `future_external` 仍必须继续只通过 backend-owned `external_provider_config` 进入 runtime path。
5. 当前 `None` resolver、source miss、blank credential 仍应继续退化为 `External provider adapter skeleton is not configured.`。

## 五、admin config 边界

本轮必须明确把 admin config 与正式知识接受流程拆开：

1. 本轮不做 admin UI。
2. 本轮不做 admin API。
3. 本轮不做 credential store。
4. 未来 admin config 如需存在，只能管理 backend-owned runtime config。
5. admin config 不等于正式知识库接受。
6. 管理员“接受进入正式知识库”只管知识资产是否进入 formal knowledge。
7. runtime provider credential 或 config 是另一条治理线。
8. 普通用户快速测试不得被管理员接受流程阻塞。
9. 普通用户快速测试也不得携带真实 credential。
10. 如果未来有 admin-managed credential reference，必须单独 review 权限、审计、DLP、回滚。

只读审查结论要写清：

1. 仓库已存在 provider router 和 provider manager，但它们服务的是另一条 provider 管理面。
2. 当前 Ask RAG path 没有被授权直接读取这些 provider 配置面。
3. 当前管理员接受正式知识流程也没有被授权成为 runtime credential approval gate。

## 六、DLP / redaction / logging 要求

未来任何真实 credential source implementation 都必须先满足以下冻结边界：

1. API key 不得进入 prompt payload。
2. API key 不得进入 request preview。
3. API key 不得进入 warning。
4. API key 不得进入 error response。
5. API key 不得进入 docs 或 tasks。
6. API key 不得进入 formal map。
7. API key 不得进入 map。
8. API key 不得进入 snapshot。
9. API key 不得进入 export。
10. API key 不得进入 fixture。
11. API key 不得进入普通日志。
12. `Authorization` header 不得记录。
13. endpoint query string 必须 redacted。
14. provider raw response 默认不得记录。
15. credential resolver exception 原文不得直接暴露。
16. DLP 失败必须阻断后续 rollout。

本轮还要明确：

1. 以上规则适用于 future env source、secret store、keychain、deployment reference、admin-managed reference 等所有候选 source。
2. 这些规则不能只停留在代码注释层，未来必须体现在测试矩阵与 rollout gate 里。
3. 任何把 secret 写入 docs、tasks、map、formal map、snapshot、export、fixture、warning、error response、普通日志的实现，都必须视为阻断级失败。

## 七、rollback / kill switch 要求

未来真实 credential source 如果要进入实现，必须先满足以下 rollback 与 kill switch 要求：

1. `transport_enabled=False` 必须能立即阻断真实 transport 和 credential resolution。
2. `enabled=False` 必须能立即阻断整个 adapter。
3. allowlist 移除 provider 或 model 必须阻断 resolver 和 transport。
4. credential source 缺失必须 safe not-configured。
5. credential source 错误必须 safe not-configured。
6. 不允许 silent switch 到另一个真实 provider。
7. 不允许 silent switch 到另一个真实 credential source。
8. rollback 不得需要改 frontend 或 request body。

额外治理要求：

1. rollback 触发面必须是 backend-owned gate，而不是用户输入。
2. rollback 后普通 Ask path 仍应保持现有 safe behavior，而不是暴露内部故障细节。
3. rollback 不能借助“管理员接受正式知识库”流程代替 credential/runtime kill switch。

## 八、测试矩阵要求

本轮不执行测试，但未来 implementation plan 至少必须覆盖以下测试矩阵：

1. disabled gate 不读 credential source。
2. `transport_enabled=False` 不读 credential source。
3. allowlist failure 不读 credential source。
4. missing backend config 不读 credential source。
5. missing source reference -> not configured。
6. blank source reference -> not configured。
7. unknown provider -> provider not allowed。
8. unknown model -> model not allowed。
9. resolver exception redacted。
10. env var name allowed as metadata only。
11. env var value 不进 docs、log、warning、error。
12. secret store source 不得默认接入。
13. `ProviderManager` 不参与。
14. `SimpleModelRouter` 不参与。
15. request body provider、model、api_key ignored。
16. frontend provider、model、api_key absent。
17. API key 不进 prompt payload。
18. API key 不进 request preview。
19. endpoint query string redacted。
20. rollback gate 阻断 resolver 和 transport。

建议未来 focused suite 仍以这些文件为主：

1. `tests/unit/game/test_knowledge_rag_external_model_client.py`
2. `tests/unit/game/test_knowledge_rag_answer.py`
3. `tests/unit/game/test_knowledge_rag_provider_selection.py`
4. `tests/unit/game/test_knowledge_rag_model_registry.py`
5. `tests/unit/routers/test_game_knowledge_rag_router.py`

## 九、下一步建议

下一步建议必须收敛为二选一，而不是 production rollout：

1. `P17` admin config boundary review
2. `P17` credential source implementation plan

本轮明确不建议：

1. production rollout
2. 直接接真实 provider
3. 直接读 env value
4. 直接接 secret store

## 验证说明

本轮是 docs-only boundary review。

本轮不改任何源码。

本轮不改任何测试。

本轮不跑 pytest。

本轮不跑 TypeScript。

本轮 post-edit validation 仅限：

1. `git diff --check` on touched docs files
2. NUL-byte scan on touched docs files
3. keyword review 确认文本没有声称已完成真实 credential source、production credential rollout、admin credential UI、frontend provider selector、request-owned credential input 或 real HTTP enablement