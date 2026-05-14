# Lane H-B Final Acceptance

## 定位

Lane H-B 用于对 Lane H-A 之后的架构基线做测试矩阵补齐、小修闭环、最终归档与关闭判定。

本轮收口目标：

```text
Architecture Baseline Closed
```

本文件只记录 H-B 自动化测试矩阵、小修范围、兼容边界、manual acceptance 执行状态与最终关闭结论，不新增功能，不扩大边界。

## 总结论

- P0-01 至 P0-07 已完成自动化验证与最小修复闭环。
- P1-01 至 P1-03 已完成自动化验证与最小修复闭环。
- 最终后端聚焦矩阵通过。
- 最终前端 helper/static tests 通过。
- 真实临时文件已清理。
- Manual Acceptance 本轮未执行人工步骤，已明确记录为未执行，不伪造通过。
- 依据 closure criteria，可标记：

```text
Architecture Baseline Closed
```

## P0 结论

### P0-01 Workbench Source Write

结论：通过。

- source-write wrapper 仅允许安全 op。
- `update_cell` 对不存在字段显式 fail-closed。
- audit、release_id_at_write、svn warning/source files/changes 均有覆盖。
- 不触发 rebuild / release / publish / SVN runtime。

### P0-02 Capability / Agent Profile

结论：通过。

- request capability 注入成立。
- role template / legacy role mapping 成立。
- 核心 route capability gate 生效。

### P0-03 Map-gated RAG

结论：通过。

- formal RAG 只读 Current Release + Map-gated artifacts。
- ignored / deprecated / unknown prefix refs 均 fail-closed。
- citation 保留 release/source/row/field/ref，最终补齐显式 table locator。
- 不读取 KB / retrieval。

### P0-04 Workbench Suggest Validator

结论：通过。

- validator 会过滤非法 table / field / row / evidence。
- runtime-only / draft overlay / formal evidence 边界清晰。
- 空模型输出返回明确错误，不生成空白 changes 成功响应。

### P0-05 Release Strict / Bootstrap

结论：通过。

- strict build 依赖 Formal Map。
- bootstrap 必须显式开启。
- build 与 publish / set current 分离。
- build-from-current-indexes 拒绝 proposal candidate_ids。
- Release 不读取 KB / Draft / Proposal。

### P0-06 Unified Model Router

结论：通过。

- formal Game model 调用统一走 router。
- service / table_indexer / dependency_resolver / RAG answer 合同已验证。
- structured failure 行为已覆盖。
- 本轮未扩大 generic agent chat runner 语义边界。

### P0-07 SVN Freeze

结论：通过。

- start / stop / status freeze 合同成立。
- game_svn router fail-closed。
- source-write 不执行 SVN runtime。
- Advanced / route 文案与重定向已对齐 frozen boundary。

## P1 结论

### P1-01 Legacy UI

结论：通过。

- Legacy Knowledge Base / Doc Library 在导航与页面中显式标记为 Legacy。
- legacy surface 不再误导为 formal knowledge entry。
- backend metadata 合同已覆盖。

### P1-02 Admin Panel

结论：通过。

- Admin Panel helper / release status 聚合合同成立。
- previous release 缺失时显示 `-` 与 warning。
- planner / viewer 不可见 admin write actions。
- admin / wildcard capability 可见全部 admin write actions。
- Build Release 与 Publish / Set Current 为两个显式操作。

### P1-03 Citation Deep-link

结论：通过。

- citation payload 保留 table / row / field / ref。
- Workbench route context 可读取 citation query。
- citation deep-link 只驱动开表 / 激活 / 高亮，不触发 draft/source-write/publish。
- deep-link helper 现已优先消费显式 locator，而不是仅依赖 source_path/title 推导。

## 最终测试矩阵结果

### 后端最终聚焦矩阵

执行命令：

```bash
.venv/bin/python -m pytest \
  tests/unit/game/test_workbench_source_write_service.py \
  tests/unit/routers/test_game_workbench_router.py \
  tests/unit/game/test_change_applier.py \
  tests/unit/app/test_capabilities.py \
  tests/unit/app/test_agent_context.py \
  tests/unit/routers/test_game_knowledge_map_router.py \
  tests/unit/routers/test_game_knowledge_release_router.py \
  tests/unit/routers/test_game_knowledge_release_candidates_router.py \
  tests/unit/game/test_knowledge_rag_context.py \
  tests/unit/routers/test_game_knowledge_rag_router.py \
  tests/unit/game/test_knowledge_rag_answer.py \
  tests/unit/game/test_workbench_suggest_context.py \
  tests/unit/game/test_knowledge_release_service.py \
  tests/unit/game/test_knowledge_release_builders.py \
  tests/unit/game/test_service.py \
  tests/unit/game/test_table_indexer.py \
  tests/unit/game/test_dependency_resolver.py \
  tests/unit/routers/test_game_svn_router.py \
  tests/unit/routers/test_game_doc_library_router.py \
  tests/unit/routers/test_game_knowledge_base_router.py \
  -q
```

结果：`346 passed`。

### 前端最终 helper/static tests

执行命令：

```bash
cd console && pnpm --allow-build=esbuild dlx tsx --test \
  src/pages/Game/components/adminPanel.test.ts \
  src/pages/Game/components/workbenchSuggestEvidence.test.ts \
  src/pages/Game/citationDeepLink.test.ts \
  src/pages/Game/legacyUiSurface.test.ts \
  src/layouts/MainLayout.routePolicy.test.ts
```

结果：`26 passed`。

### 合计

- 自动化最终收口测试：`372 passed`

## 小修范围

本轮 H-B 只做了测试矩阵闭环所需的最小修复，范围受控于以下边界：

- source-write 校验 / audit / no-side-effect 收口
- capability / role template 合同收口
- map-gated RAG fail-closed 与 citation locator 收口
- Workbench Suggest validator / empty output 收口
- Release strict/bootstrap fail-closed 收口
- Unified Model Router 合同测试补齐
- SVN frozen boundary 文案 / route 合同收口
- Legacy UI / locale / metadata 收口
- Admin Panel helper/action visibility 收口
- Citation deep-link locator 与无副作用 route parsing 收口

未引入新的产品流程、能力模型或架构面。

## 保留兼容边界

- KB / Doc Library / retrieval 保留 legacy/debug/migration-only surface，不删除。
- generic agent chat runner 仍为 compatibility boundary，不承载 formal Game model routing 语义。
- Workbench source-write 仍要求显式人工确认与手工 SVN 外部更新，不执行 SVN runtime。
- Admin Panel 当前仍是状态聚合与既有操作入口，不是新的中心化管理工作流。
- Build Release 与 Publish / Set Current 仍然分离。

## Manual Acceptance 记录

执行状态：未执行。

原因：本轮仅完成自动化测试矩阵、最小修复、归档与提交；未在浏览器环境中逐项执行 `manual-acceptance.md` 中的 Admin Knowledge Chain、Planner Workbench、Legacy KB 人工流。

明确记录：

- 未执行人工验收。
- 未提供截图。
- 未记录 browser/environment。
- 未记录人工 agent role walkthrough。

因此本轮结论基于自动化矩阵与代码/接口/helper/static contract 验证，不伪造 manual acceptance 通过。

## Closure Criteria 结论

### Blocking checks

- H1-H6 P0 tests pass：是。
- Source-write wrapper fixes and tests pass：是。
- Legacy KB UI is marked legacy：是。
- Release does not read KB：是。
- RAG does not read KB：是。
- RAG does not bypass Map：是。
- Workbench Suggest does not bypass Formal Context：是。
- Source write does not trigger knowledge update：是。
- Capability gate works on core routes：是。
- Unified Model Router is the formal Game model-call entry：是。
- SVN runtime remains frozen：是。

### Cannot-close conditions

- KB participates in Release / RAG / Workbench：否。
- RAG full-scans artifacts as the formal query path：否。
- source-write bypasses `workbench.source.write`：否。
- Workbench can `delete_row` or run schema ops through source-write：否。
- Source write auto Builds or Publishes：否。
- Important routes lack capability context：未发现。
- Formal Game model calls return to module-owned API config：否。
- SVN watcher returns to main flow：否。

## 最终关闭结论

在 manual acceptance 未执行但已明确记录为未执行、且自动化测试矩阵与架构闭环条件满足的前提下，本轮可标记：

```text
Architecture Baseline Closed
```

## 收口后续方向

- Lane I: Canonical Schema / Map build quality
- Lane J: Workbench Suggest interaction experience
- Lane K: Admin Panel complete operation closure
- Lane L: RAG recall quality