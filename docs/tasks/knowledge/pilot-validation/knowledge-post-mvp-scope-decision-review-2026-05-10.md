# Knowledge Post-MVP Scope Decision Review

Date: 2026-05-10
Scope: docs-only post-MVP scope decision review for the next mainline after P0-P3 MVP closeout

## 一、当前状态

1. P0-P3 MVP 已通过 P3.12，并已在 `docs/tasks/knowledge/mvp/knowledge-p0-p3-mvp-final-handover-2026-05-10.md` 完成交接。
2. external-provider 当前冻结在 `P3.external-provider-19`。
3. P20 real HTTP transport 不得默认继续，必须先经过单独 scope decision。
4. `P3.9 table_facts.sqlite`、relationship editor、graph canvas、real provider rollout 仍是 optional 或 deferred，而不是 MVP blocker。
5. 当前系统已经具备可继续稳定化的 MVP 基线：release build、rollback、current-release RAG、structured query、formal-map save/status edit、NumericWorkbench fast-test 与 export 边界都已落地。
6. 当前稳定性主轴已经从“补齐 MVP 缺口”转为“保持已关闭主线的稳定、可交付、可 handoff、可复核”。

## 二、候选路线评估

### 1. P20 real HTTP transport resume

价值：

1. 长期上能推进 external-provider 从 skeleton toward real transport。
2. 但对当前 MVP 用户可用性的直接提升有限，因为现有 Ask 已可在 deterministic/mock 与 current-release 边界内工作。

风险：

1. 这是当前候选里 secret、DLP、credential、redaction、rollback、transport failure、provider rollout 风险最高的一条。
2. 会显著提高边界出错成本，因为一旦做错，就会碰到 request/router/provider ownership 漂移。
3. 还会把当前“已关闭 MVP 主线”重新拉回高风险基础设施工作，而不是稳定化。

依赖：

1. 已冻结的 credential / transport / DLP / rollback 规则必须先继续保持有效。
2. 必须继续遵守 query-only Ask schema、router thin boundary、backend-only provider selection。
3. 必须继续隔离 `ProviderManager`、`SimpleModelRouter`、`secret_store`、frontend provider UI。

推荐程度：

1. 低。

是否适合下一轮实施：

1. 不适合。
2. 除非当前业务明确认为“真实 HTTP transport 比 MVP 稳定化更重要”，否则不应进入下一轮。

如果实施，第一刀应该是什么：

1. 只能是 `knowledge_rag_external_model_client.py` 内部的 backend-only minimal transport slice。
2. 不能改 Ask request schema。
3. 不能加 frontend provider/model/API key UI。
4. 不能默认视为 production rollout。

### 2. P3.9 optional table_facts.sqlite

价值：

1. 直接服务“精确值、字段、行级事实”可用性。
2. 与现有 structured query 路线天然一致，适合补强“RAG 负责解释、structured query 负责精确查值”的分工。
3. 如果做成 release-owned artifact，能继续保持 current-release-only 边界。

风险：

1. 中等。
2. 会新增 release artifact、manifest/build metadata、query path 的精确读取逻辑。
3. 如果做得过大，容易从“精确读增强”扩成新的索引系统或 schema redesign。

依赖：

1. 需要继续保持 release-owned build 边界。
2. 需要保持 current release pointer 驱动读取。
3. 需要避免把 optional sqlite 变成新的发布阻塞条件。

推荐程度：

1. 中。

是否适合下一轮实施：

1. 可以，但更适合作为“structured query hardening 的后续可选增强”，而不是当前首选主线。

如果实施，第一刀应该是什么：

1. 先做 docs-only contract review，冻结 sqlite 的 release-owned scope、manifest metadata、query API 复用策略。
2. 不直接先做全量实现。

### 3. relationship editor / graph governance UX

价值：

1. 能增强 formal knowledge 治理体验。
2. 长期有助于 map governance completeness。

风险：

1. 高。
2. 会直接触碰 formal knowledge 编辑语义、relationship validation、UI complexity、possibly backend validation 行为。
3. 很容易从最小 UX 扩成 graph canvas、bulk edit、auto-fix relationship 等大范围功能。

依赖：

1. 必须继续保持 candidate-map read-only、saved-formal-map-only edit boundary。
2. 必须明确 relationship 编辑是否仍沿用完整 `PUT /game/knowledge/map`。
3. 必须避免把 fast-test 或 candidate flow 混进 formal knowledge 编辑。

推荐程度：

1. 低。

是否适合下一轮实施：

1. 不适合当前下一轮主线。
2. 更适合作为后续独立 boundary review，而不是 MVP 刚关闭后的第一优先项。

如果实施，第一刀应该是什么：

1. 先做 saved-formal-map-only 的 docs-only relationship edit boundary review。
2. 明确拒绝 graph canvas、drag-and-drop、LLM relationship generation。

### 4. release packaging / final QA

价值：

1. 直接服务当前用户可用性和交付可用性。
2. 能把“已经可用的 MVP”变成“更容易 handoff、复核、交付、演示和回归”的稳定产品基线。
3. 与 P3.10 rollback、P3.11 permission split、P3.12 gate closeout 完全一致，是最自然的 post-MVP 稳定化方向。

风险：

1. 低到中。
2. 主要风险是 scope drift，把 packaging / QA 做成新的功能扩张。
3. 但它不天然要求 secret、credential、real HTTP，也不要求 provider rollout。

依赖：

1. 依赖现有 release build / rollback / capability split 的稳定基线。
2. 依赖 docs、handover、deploy/runtime packaging、final QA checklist 的收口。
3. 若要实现，也应优先限制在 docs、scripts、packaging 或 smoke-level hardening，而不是改核心业务逻辑。

推荐程度：

1. 高。

是否适合下一轮实施：

1. 适合。
2. 这是最适合下一轮由 5.4 做的主线，因为边界清楚、风险低、直接服务交付质量。

如果实施，第一刀应该是什么：

1. 先做一个 narrow release packaging / final QA / handoff hardening slice。
2. 限制在 docs、packaging scripts、final QA checklist、handoff artifacts。
3. 不改 Ask request schema，不碰 provider rollout，不扩 product feature。

### 5. provider rollout admin/config boundary

价值：

1. 如果未来真的要推进 provider rollout，这条线能先把 admin config、runtime approval、secret ownership 的治理边界说清楚。
2. 能避免把 admin acceptance 错误复用成 runtime provider approval。

风险：

1. 中到高。
2. 容易把 provider governance、admin UI、credential ownership、runtime rollout 纠缠在一起。
3. 如果时机过早，会把当前稳定化主线重新带回 external-provider 决策链。

依赖：

1. 依赖已有 admin-vs-fast-test boundary。
2. 依赖 provider credential boundary review。
3. 依赖继续冻结 request/frontend/router ownership。

推荐程度：

1. 中低。

是否适合下一轮实施：

1. 只适合作为 docs-only 可选路线。
2. 不适合现在直接进入实现。

如果实施，第一刀应该是什么：

1. 先做 docs-only admin/config boundary review。
2. 明确 admin config 不等于 runtime provider approval。
3. 明确 admin acceptance 不控制 fast-test，也不控制 runtime transport。

### 6. structured query hardening

价值：

1. 直接服务用户对精确值、字段、表级事实的可用性。
2. 与 P3.12 gate 中“precise values go through structured query”完全对齐。
3. 相比 P20，不涉及 secret、real provider、real HTTP，是明显更贴近 MVP 用户价值的下一步。

风险：

1. 中等。
2. 需要谨慎控制在“精确查询 hardening”，避免扩成新的 query platform、schema redesign 或写路径。
3. 可能涉及 frontend panel、response typing/normalization、backend result semantics，但这些风险明显低于 P20。

依赖：

1. 依赖当前 GameProject 面板、`/game/index/query`、`mode='auto'`、read-only result contract。
2. 依赖保持 `knowledge.read` read boundary，或在后续单独评审 dedicated structured-query read capability。
3. 依赖继续保持“不自动写 test plan / candidate / release”的 routing 边界。

推荐程度：

1. 中高。

是否适合下一轮实施：

1. 适合，作为推荐主线之后的第一可选路线最合理。

如果实施，第一刀应该是什么：

1. 做一个 narrow structured query hardening slice。
2. 优先收口 `auto` mode 结果语义、read-only response normalization、error/empty-state clarity、exact-table/exact-field behavior。
3. 不新增 provider/request schema，不进入写流程。

## 三、推荐下一步

明确推荐主线：

1. 推荐下一步主线是 release packaging / final QA / handoff hardening。

推荐理由：

1. 它直接服务当前 MVP 的可交付性和可复核性。
2. 它最少触碰稳定性风险，不需要真实 provider、真实 HTTP、secret、credential、frontend provider UI 或 Ask schema 变更。
3. 它不会改变当前权限边界，也不会改变 formal knowledge / fast-test 边界。
4. 它最符合 “P0-P3 MVP 已闭合后先做稳定化，而不是重新打开高风险基础设施线” 的当前阶段目标。
5. 它最适合下一轮由 5.4 用一个小而清晰的 slice 落地。

推荐主线之后的可选路线：

1. structured query hardening。
2. provider rollout admin/config boundary review。
3. `P3.9 table_facts.sqlite` contract/planning。

为什么不是默认 P20：

1. P20 当前不直接解决 MVP 主线最迫切的用户可用性问题。
2. P20 会立刻进入 credential、DLP、rollback、transport、provider governance 的高风险区。
3. P20 还会扩大对 router/request/provider ownership 的守边成本。
4. 在 MVP 刚通过 P3.12 的当下，稳定化和交付硬化比 real HTTP transport 更重要。

明确 deferred 的路线：

1. P20 real HTTP transport resume：deferred，非默认继续。
2. relationship editor / graph governance UX：deferred，非当前主线。
3. graph canvas：继续 deferred，不在当前候选实施列表内。
4. real provider rollout：继续 deferred。

如果未来要推荐 P20，必须先同时满足：

1. 明确说明为什么真实 HTTP 比 MVP 稳定化更重要。
2. 明确先过 credential ownership gate。
3. 明确先过 DLP/redaction gate。
4. 明确先过 rollback/kill-switch gate。
5. 明确先过 request/router/frontend ownership gate。
6. 明确先过 provider rollout 与 production rollout 分离 gate。

## 四、明确禁止

1. 不默认继续 external-provider P20。
2. 不直接接真实 provider。
3. 不直接加 provider/model/API key UI。
4. 不改 Ask request schema。
5. 不把 ordinary RAG Q&A 变成写流程。
6. 不把 fast-test 自动并入 formal knowledge。
7. 不把 admin acceptance 用作 runtime provider approval。
8. 不做 SVN commit/update integration。
9. 不做大重构。

## 五、下一轮 prompt seed

### slice 名称

1. Post-MVP Release Packaging / Final QA / Handoff Hardening

### 目标

1. 在不扩大产品功能的前提下，收口 MVP 的 release packaging、final QA、handoff artifacts 与交付检查。
2. 让当前 MVP 更容易被复核、部署、演示和交接。
3. 保持 rollback、permission、structured query、fast-test、formal knowledge 边界不变。

### 允许改哪些文件

1. `docs/tasks/` 下与 packaging、handoff、final QA closeout 直接相关的文档。
2. `docs/README.md`、`README_zh.md`，仅当需要补齐 handoff/runbook 说明时。
3. `scripts/` 下与 final QA、packaging、smoke checklist 直接相关的窄范围脚本。
4. `deploy/` 下与 packaging/handoff 直接相关的窄范围文档或模板说明文件。

### 禁止改哪些文件

1. `src/ltclaw_gy_x/` 业务源码。
2. `console/src/` 前端源码。
3. `tests/`。
4. Ask request schema、provider config surface、router capability surface。
5. external-provider `P20` 相关实现文件。

### 必须跑哪些验证

1. `git diff --check`。
2. touched docs/scripts NUL check。
3. 如果改了 shell/python packaging scripts，只跑与脚本语法或帮助输出直接相关的最小静态检查，不跑 pytest，不跑 TypeScript。
4. keyword review，确认没有误写成新增 product feature、real provider rollout 或 Ask schema 扩张。

### 必须更新哪些 docs

1. 新的 packaging/final-QA/handoff closeout 文档。
2. `docs/tasks/knowledge/status/knowledge-p0-p3-implementation-checklist.md`。
3. `docs/tasks/knowledge/status/knowledge-p3-gate-status-2026-05-07.md`。
4. `docs/tasks/knowledge/status/knowledge-p3-gate-consolidation-2026-05-08.md`。
5. 必要时同步 `docs/tasks/knowledge/mvp/knowledge-p0-p3-mvp-final-handover-2026-05-10.md` 的 next-step note。

### 完成后怎么汇报

1. 列出新增/修改的 docs 与 scripts。
2. 说明 packaging/final QA/handoff 哪些点被收口。
3. 明确说明没有继续 P20。
4. 明确说明没有改业务源码、前端源码、测试和 Ask schema。
5. 给出 `git diff --check`、NUL check、keyword review 结果。