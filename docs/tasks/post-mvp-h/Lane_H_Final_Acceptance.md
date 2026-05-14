# Lane H Final Acceptance

## 定位

Lane H 用于验证和硬化已经完成的 Post-MVP 架构收口代码，不继续扩大功能。

本轮总验收结论：

```text
Post-MVP Architecture Baseline Locked
```

H1-H8 均已完成审核。P0 核心边界通过，P1 管理与 legacy 收口通过。

## 总结论

- KB / retrieval 不再属于正式知识链路。
- 正式 RAG 只走 Current Release + Formal Map + Map-gated artifacts。
- Release build 不读取 KB、retrieval、workspace/session approved docs、Draft Overlay 或普通 Proposal。
- Workbench Suggest 由 Formal Context + Runtime Context + Draft Overlay + validator 收口。
- Workbench source write 只允许受控 op，具备 capability gate、audit、SVN 外置提醒，并且不触发 rebuild/release/publish/RAG/SVN runtime。
- Agent Profile capabilities 已成为本地角色边界标准，`my_role` 仅为 legacy shortcut。
- Formal Game 模型调用统一走 Unified Model Router；generic agent chat runner 明确保留为 compatibility boundary。
- Candidate / Formal Map / Release / Admin Panel 已分离，Build 与 Publish / Set Current 是两个显式操作。
- Legacy KB、Doc Library、retrieval、SVN runtime surface 已被隐藏、重定向、冻结或显式标注为 legacy/debug/migration-only。

## H1 KB Formal Chain

结论：通过。

审核确认：

- Release build 不调用 `get_kb_store`。
- Release build 不调用 `_load_approved_doc_entries`。
- Release doc artifacts 来自 Formal Map / Current Release doc refs。
- RAG context / answer 不 fallback KB 或 retrieval。
- Chat formal knowledge 只注入 current-release context，不 fallback legacy KB/retrieval。
- Workbench Suggest formal evidence 只来自 Current Release + Map-gated RAG。
- Knowledge Base / Doc Library / retrieval 只保留 legacy/debug/migration-only 语义。

本轮硬化：

- KB route 返回统一 legacy metadata。
- Doc Library / KB 直达页文案改为 Legacy。

## H2 Map-gated RAG

结论：通过。

审核确认：

- RAG 先 route allowed refs，再读取 release artifacts。
- ignored / deprecated refs 不进入 chunks 或 citations。
- explicit `focus_refs` 是硬约束；全无效时 fail-closed。
- table/doc/script refs 固定映射到 table_schema/doc_knowledge/script_evidence。
- candidate evidence、raw source、pending/session draft、KB/retrieval 不进入 formal context。
- citation 保留 release/source/row/field/ref 等 deep-link 定位字段。

本轮硬化：

- 补了 routed refs 早停读取和 citation locator 字段测试。

## H3 Workbench Suggest

结论：通过。

审核确认：

- Formal Context 来自 Current Release + Map-gated RAG。
- Runtime Context 来自当前 workbench tables、fields、row_index、matched_columns。
- Draft Overlay 来自 current_pending，不能升级为 formal evidence。
- validator 过滤非法 table、field、row_id、evidence_ref。
- runtime-only suggestion 与 formal evidence 明确区分。
- Suggest 使用 `model_type=workbench_suggest` 调用 unified router。

本轮硬化：

- malformed model output 不再返回 200 空 changes，改为 `502 invalid_model_output`。

## H4 Workbench Source Write

结论：通过。

审核确认：

- `/game/workbench/source-write` 需要 `workbench.source.write`。
- allowlist 只有 `update_cell` 与 `insert_row`。
- `delete_row`、schema ops、新字段、新表、改主键、改路径等均被阻断。
- 支持 `.csv`、`.xlsx`、`.txt`；拒绝 `.xls` 与未知格式。
- 返回 `svn_update_required` 与 `svn_update_warning`，后端不执行 SVN update/commit/revert/watcher。
- 成功、业务失败、audit 失败 after write 三类返回 shape 已明确。
- 写回后不触发 index rebuild、Release build、Publish / Set Current、RAG rebuild 或 SVN watcher。

本轮硬化：

- `update_cell` 对 unknown field 增加显式早拒绝。
- 补了 source-write gate、failure audit、current release 不变等测试。

## H5 Agent Profile Capability

结论：通过。

审核确认：

- capability catalog 与前端类型一致。
- viewer / planner / source_writer / admin 默认能力符合边界。
- `my_role=maintainer` 映射 admin，`my_role=planner` 映射 planner，其他映射 viewer。
- Agent Profile capabilities 优先于 legacy shortcut。
- `get_agent_for_request()` 注入 `request.state.agent_profile`、`request.state.capabilities`、`request.state.user`。
- `require_capability()` 优先读取 request-state capabilities。
- Map、Candidate、Release、Publish、Workbench source-write route 均为后端 gate，不只靠前端隐藏。

本轮无代码修改，仅验证。

## H6 Unified Model Router

结论：通过。

审核确认：

- Formal Game model calls 使用 Unified Model Router。
- Workbench Suggest、TableIndexer、DependencyResolver、RAG Answer 通过 router 传递 `model_type`。
- unknown `model_type` fallback default。
- no active model、provider not configured、provider exception、empty response 均返回 structured error。
- generic agent chat runner 保留 compatibility boundary，不承担 Post-MVP Formal Game model routing 语义。
- console formal chat 只注入 current-release formal context，不自行选择 provider/model/api key/base URL。

本轮硬化：

- `unified_model_router.py` 将“slot 已解析但 provider 缺失”从 `no_active_model` 修正为 `provider_not_configured`。
- H6 文档明确 generic agent chat compatibility boundary。

## H7 Release Candidate Admin

结论：通过。

审核确认：

- release snapshot candidate 标记 `candidate_source=release_snapshot`，不是 Formal Map。
- source/canonical candidate 标记 `candidate_source=source_canonical`，不 fallback release snapshot。
- existing Formal Map 只作为 hint，不保留 canonical facts 中不存在的 refs。
- diff_review 包含 added / removed / changed / unchanged / warnings。
- Formal Map get/save 分别 gate `knowledge.map.read` / `knowledge.map.edit`。
- Release build gate `knowledge.build`；Publish / Set Current gate `knowledge.publish`。
- strict build 无 Formal Map fail-closed。
- bootstrap build 必须显式且带 warning。
- Build Release 不自动 Publish / Set Current。
- Admin Panel 展示 project bundle path、source config path、current release、previous release、map hash、formal map status、RAG status、current knowledge version。

本轮硬化：

- Admin Panel 增加 previous release 只读状态卡。

## H8 Legacy UI / Route / Test Matrix

结论：通过。

审核确认：

- Main navigation 不再展示 Knowledge Base / Doc Library 作为正式入口。
- `/doc-library` 与 `/knowledge-base` 仍可直达，但页面和导航名均显式 Legacy。
- `/game/advanced/svn` 重定向到 `/game/advanced`。
- `/svn-sync` 重定向到 `/game/project`。
- SVN service start/stop/status 返回 disabled/frozen。
- SVN status/sync/log stream route 返回 frozen/disabled 语义，不执行 update/sync/revert/commit。
- retrieval 只保留 legacy debug/migration-only 语义。

本轮硬化：

- legacy 直达页 locale 标题和导航名改为 explicit Legacy。
- 清理根目录临时文件 `PLACEHOLDER_SECRET_FOR_SMOKE`；确认 `.vite/` 和 `test_output.txt` 不存在。

## 保留兼容边界

- KB / Doc Library / retrieval 保留 legacy/debug/migration-only surface，不删除。
- `/doc-library` 与 `/knowledge-base` 保留直达访问，但不在主正式流程中。
- generic agent chat runner 保留现有 provider/model factory compatibility boundary；Formal Game model calls 已统一走 Unified Model Router。
- source-write 不自动执行 SVN Update；用户仍需在 LTClaw 外自行完成 SVN 更新流程。
- Admin Panel 当前是状态聚合与既有入口跳转，不是新的中心化审计服务或管理员 workflow 引擎。

## 非本轮完成项

- Canonical facts 质量提升。
- LLM 字段语义归一化。
- LLM 系统聚类。
- LLM diff explanation。
- Admin Panel 完整交互体验。
- RAG 质量优化、rerank、embedding 增强。
- Workbench UI polish。
- MCP/Admin Toolpool 实现。
- legacy KB/retrieval 物理删除。
- 全自动端到端验收流水线。

## 最终验证记录

本轮 main 审核期间已复跑各 H 项聚焦测试。最终收口前建议继续执行：

```bash
.venv/bin/python -m pytest \
  tests/unit/routers/test_game_knowledge_base_router.py \
  tests/unit/routers/test_console_chat_mode.py \
  tests/unit/game/test_knowledge_release_service.py \
  tests/unit/game/test_knowledge_rag_context.py \
  tests/unit/routers/test_game_workbench_router.py \
  tests/unit/routers/test_game_knowledge_rag_router.py \
  tests/unit/game/test_knowledge_rag_answer.py \
  tests/unit/game/test_workbench_source_write_service.py \
  tests/unit/game/test_change_applier.py \
  tests/unit/app/test_capabilities.py \
  tests/unit/app/test_agent_context.py \
  tests/unit/routers/test_game_knowledge_map_router.py \
  tests/unit/routers/test_game_knowledge_release_router.py \
  tests/unit/routers/test_game_knowledge_release_candidates_router.py \
  tests/unit/routers/test_game_knowledge_test_plans_router.py \
  tests/unit/game/test_service.py \
  tests/unit/game/test_table_indexer.py \
  tests/unit/game/test_dependency_resolver.py \
  tests/unit/game/test_knowledge_map_candidate.py \
  tests/unit/game/test_map_diff_review.py \
  tests/unit/routers/test_game_svn_router.py \
  tests/unit/routers/test_game_doc_library_router.py \
  -q
```

Frontend helper checks:

```bash
cd console
npx tsx --test \
  src/pages/Game/components/adminPanel.test.ts \
  src/pages/Game/components/mapBuildReview.test.ts \
  src/pages/Game/components/workbenchSuggestEvidence.test.ts
```

## 提交前检查

- [ ] `git status --short` 中无临时文件。
- [ ] `PLACEHOLDER_SECRET_FOR_SMOKE` 不存在。
- [ ] `.vite/` 不存在或被忽略。
- [ ] `test_output.txt` 不存在。
- [ ] 后端最终聚焦矩阵通过。
- [ ] 前端 helper tests 通过。
- [ ] 如要发布静态产物，重新执行 console build 流程，确保 Legacy 文案进入产物。
