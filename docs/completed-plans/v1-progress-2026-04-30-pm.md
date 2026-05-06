# LTCLAW-GY.X 游戏策划工作台 — v1 进度报告 (2)

> 更新日期：2026-04-30 (深夜补丁)
> 关联：[v1-progress-2026-04-30.md](./v1-progress-2026-04-30.md)、[game-planner-workbench-planv.0.md](./game-planner-workbench-planv.0.md)

## 1. 整体完成度（vs 上一版）

| 维度 | 上一版 | 本版 |
|---|---|---|
| 后端骨架 | 100% | 100% |
| 前端骨架 | ~90% | ~97% |
| 数值工作台核心闭环 | ~75% | ~88% |
| 多 agent 项目隔离 | ~30% | ~75% |
| 知识库 / 文档库实用度 | ~40% | ~75% |
| 整体 v1 完成度 | ~60% | **~88%** |

## 2. 本轮新增

### 后端
- [`game_workbench.py`](../src/ltclaw_gy_x/app/routers/game_workbench.py) `_build_row_index` 之前预过滤大表行：
  - 当 `query_terms` 非空时，先扫描 PK + matched_columns 生成命中行 / 未命中行；命中优先放进 row_index，未命中行兜底，封顶 1500。
  - 解决「大表 5000 行 + 1500 封顶 截断目标行」的盲区。

### 前端 — Chat
- [`AgentWorkspaceSelector.tsx`](../console/src/pages/Chat/components/AgentWorkspaceSelector.tsx)：顶部 agent 切换器，自动拉 `agentsApi.listAgents`，写回 `agentStore.setSelectedAgent`。
- [`ChatModeToolbar.tsx`](../console/src/pages/Chat/components/ChatModeToolbar.tsx)：5 模式（自由对话 / 策划案 / 数值查询 / 文档生成 / 知识查询），用 `Segmented` + zustand persist 保存。
- [`workbenchCardChannel.ts`](../console/src/pages/Chat/workbenchCardChannel.ts)：Chat ↔ Workbench 联动卡片协议 v0（localStorage + CustomEvent 广播；4 类卡：numeric_table / draft_doc / svn_change / kb_hit）。
- [`WorkbenchCardPanel.tsx`](../console/src/pages/Chat/components/WorkbenchCardPanel.tsx)：Chat 右栏卡片渲染面板；与 PlanPanel 共存（启用 Plan 时上 60% Plan + 下 40% 卡片；不启用 Plan 时全部为卡片）。
- Chat 主面板 [`pages/Chat/index.tsx`](../console/src/pages/Chat/index.tsx) `rightHeader` 注入 `ChatModeToolbar` + `AgentWorkspaceSelector`，并整合 `WorkbenchCardPanel` 到 `RightContextSidebar`。

### 前端 — NumericWorkbench
- [`NumericWorkbench.tsx`](../console/src/pages/Game/NumericWorkbench.tsx) `sendChat` 成功后 `pushWorkbenchCard({kind:"numeric_table"})`；`openDraft` 触发 `pushWorkbenchCard({kind:"draft_doc"})`。
- 表内全文搜索（上一版已落）保留。

### Skills
- 新增 `numeric_assist-zh/en`、`doc_gen-zh/en` 共 4 个内置技能 SKILL.md，落 `src/ltclaw_gy_x/agents/skills/`。
- 已存在 `game_query-zh/en` 不动。

## 3. 已闭环的高优先级项

- ✅ /suggest 注入 ai_summary
- ✅ /suggest 跨表联查（dependency_graph）
- ✅ /suggest 关键词列召回 + 行预过滤（避免大表截断丢命中）
- ✅ 多轮 chat_history（最近 6 轮）
- ✅ NumericWorkbench 表内全文搜索
- ✅ 项目级 agent 创建向导（GameProject「另存为新项目 Agent」）
- ✅ Chat workspace selector
- ✅ Chat 模式工具栏
- ✅ Chat ↔ Workbench 联动卡片协议
- ✅ 内置技能：numeric_assist + doc_gen（含 zh/en）
- ✅ Chat 模式落到提示词（X-Chat-Mode 头 → 后端 `_inject_chat_mode_prefix` 注入首条 text part）
- ✅ 审批流接 apply（env-gated，复用 `ApprovalService.wait_for_approval`，APPROVED/DENIED/TIMEOUT 三路径直跑通过）

## 4. 本轮新增（深夜批次）

### Chat 模式真正生效
- [`console/src/pages/Chat/index.tsx`](../console/src/pages/Chat/index.tsx) `customFetch` 与 `reconnect` 在请求头注入 `X-Chat-Mode: <design|numeric|doc|kb>`（free 模式不注入）。
- [`src/ltclaw_gy_x/app/routers/console.py`](../src/ltclaw_gy_x/app/routers/console.py) 新增 `_CHAT_MODE_PREFIX` 字典 + `_inject_chat_mode_prefix(request, native_payload)`，在 `post_console_chat` 中 `_extract_session_and_payload` 之后、`resolve_session_id` 之前调用：把模式前缀拼接到首个 user message 的首条 text part；兼容 `TextContent` 对象 / dict / str 三种 content 形态。

### 审批流接 apply（env-gated 默认关闭）
- [`src/ltclaw_gy_x/app/approvals/service.py`](../src/ltclaw_gy_x/app/approvals/service.py) 新增 `ApprovalService.create_generic_pending(*, agent_id, title, summary, severity, kind, timeout_seconds, extra)`，不依赖 `ToolGuardResult`，直接构造 `PendingApproval` 并复用同一锁/池/通道。
- [`src/ltclaw_gy_x/app/routers/game_change.py`](../src/ltclaw_gy_x/app/routers/game_change.py) 新增 `_apply_approval_required()` / `_apply_approval_timeout()` / `_maybe_request_apply_approval(workspace, proposal)`；在 `POST /proposals/{id}/apply` 的 `applier.apply` 之前调用：
  - APPROVED → 继续 apply
  - DENIED → HTTP 403 `Apply denied by reviewer`
  - TIMEOUT → HTTP 408（提示 "resolve via /approval and retry"）
- 启用方式：环境变量 `QWENPAW_GAME_APPLY_REQUIRE_APPROVAL=true`，可选 `QWENPAW_GAME_APPLY_APPROVAL_TIMEOUT=300`（秒）。
- 默认行为不变（开关关），不影响现有自动化与冒烟。

## 5. 仍未做（按优先级）

### P1（本批次已闭环 ✅）
- ✅ 本地向量库落地：零依赖 hashing TF-IDF 向量索引 + KnowledgeBaseStore（JSONL 持久化 + 启动时 `_rebuild_index`）。新增 [`src/ltclaw_gy_x/knowledge_base/{__init__.py,local_vector_store.py,kb_store.py}`](../src/ltclaw_gy_x/knowledge_base/)；改写 [`src/ltclaw_gy_x/app/routers/game_knowledge_base.py`](../src/ltclaw_gy_x/app/routers/game_knowledge_base.py) 提供 CRUD + `/search`(`top_k`+`category`) + `/stats`；前端 [`console/src/api/modules/gameKnowledgeBase.ts`](../console/src/api/modules/gameKnowledgeBase.ts) 同步扩 `createEntry/updateEntry/deleteEntry/search/stats`。
- ✅ 卡片协议 v1（后端 SSE）：新增 [`src/ltclaw_gy_x/app/workbench_cards.py`](../src/ltclaw_gy_x/app/workbench_cards.py)（per-agent 内存 broker，asyncio.Queue 订阅 + 50 条循环 buffer + 启动 snapshot），新增 [`src/ltclaw_gy_x/app/routers/game_workbench_cards.py`](../src/ltclaw_gy_x/app/routers/game_workbench_cards.py) 暴露 `GET/POST /workbench-cards` + `GET /workbench-cards/stream`（EventSourceResponse + 20s ping），并接入 [`agent_scoped.py`](../src/ltclaw_gy_x/app/routers/agent_scoped.py)。前端 [`workbenchCardChannel.ts`](../console/src/pages/Chat/workbenchCardChannel.ts) 新增 `subscribeWorkbenchCardsBackend(agentId)`，[`WorkbenchCardPanel.tsx`](../console/src/pages/Chat/components/WorkbenchCardPanel.tsx) 在选中 agent 时自动并行订阅，多 tab/多端同步。
- ✅ 审批 push 通知：[`ApprovalService`](../src/ltclaw_gy_x/app/approvals/service.py) 新增 `subscribe_events/unsubscribe_events/_publish_event_nowait`，在 `create_pending`/`create_generic_pending`/`resolve_request` 三处发事件（`type ∈ {created, resolved}` + 关键字段）。新增 [`/api/approval/stream`](../src/ltclaw_gy_x/app/routers/approval.py) SSE：进入即下发现有 pending snapshot，再持续推送增量 + 20s ping；`/approval/list` 序列化补 `extra`，generic-kind 审批的 `title/kind` 等字段不再丢失。

### P2（本批次已闭环 ✅）
- ✅ KB 混合检索（BM25-lite + 向量加权融合）：[`src/ltclaw_gy_x/knowledge_base/kb_store.py`](../src/ltclaw_gy_x/knowledge_base/kb_store.py) 新增 `_kw_postings/_kw_doc_len/_bm25_search`，与 hashing TF-IDF 余弦双路召回；`search(query, top_k, category, mode={vector|keyword|hybrid}, alpha=0.6)` 默认 hybrid，min-max 归一化后线性加权；增删改改三处同步维护倒排表。
- ✅ KB 页面接 search/CRUD：[`console/src/pages/Game/KnowledgeBase.tsx`](../console/src/pages/Game/KnowledgeBase.tsx) 移除全部 mock 兜底；接 `gameKnowledgeBaseApi.search/list/create/update/delete`，hits 显示 `score` 徽章，新建/编辑/删除走 Modal + Popconfirm，`enterButton="语义搜索"` 触发 `runSearch`。
- ✅ 前端 ApprovalProvider 升级 SSE：[`console/src/contexts/ApprovalContext.tsx`](../console/src/contexts/ApprovalContext.tsx) 在挂载时打开 `EventSource("/api/approval/stream", {withCredentials:true})`，监听 `approval` 事件后立即调 `consoleApi.getPushMessages()` 刷新；`onerror` 后置 3s 重连。原有 `ConsolePollService` 轮询保留作为兜底，新通道把审批延迟从 ~2.5s 收敛到准实时。
- ✅ SVN 自动 commit 防冲突：[`src/ltclaw_gy_x/game/svn_client.py`](../src/ltclaw_gy_x/game/svn_client.py) 新增 `commit_with_retry(paths, message, max_retries=5, base_delay=1.0)`：识别 conflict / out-of-date / lock 类错误后跑 `svn update` 再退避重试（`base * 2**i * U(0.5, 1.5)`），非冲突错误立即抛出。[`SvnCommitter.commit_proposal`](../src/ltclaw_gy_x/game/svn_committer.py) 增加 `expected_revision` 守卫：本地 revision 比期望大时抛 `CommitError`，避免 clobber 新工作；commit 改走 `commit_with_retry`。

### P2（仍未做）
- 主索引机模式 vs 竞争模式（需用户决策）
- 代码类索引（.cs 类名/方法签名）
- 变更影响分析（reverse-impact）

## 6. 验证

- 后端 AST OK（console.py / approvals/service.py / routers/game_change.py / game_workbench.py / knowledge_base/* / workbench_cards.py / routers/game_knowledge_base.py / routers/game_workbench_cards.py / routers/approval.py / routers/agent_scoped.py，0 nul bytes）。
- ApprovalService `create_generic_pending` 三路径直跑通过：APPROVED / DENIED / TIMEOUT。
- ApprovalService 事件 pub/sub 烟雾：`subscribe_events` → `create_generic_pending` 收到 `type=created` + 正确 `kind/title`，`resolve_request(APPROVED)` 收到 `type=resolved` + `decision=approved`。
- 卡片 broker 烟雾：`get_broker(agent_id).subscribe()` → `publish_card(...)` 在 2s 内收到事件，字段完整（id/agent_id/kind/title/summary/payload/created_at）。
- KB 烟雾：vector 检索 top-1 命中 score=0.707；落 JSONL 后冷启动 `KnowledgeBaseStore(td)` 读回 3 条并重建索引，第二次搜索 `紫橙 装备` 命中正确条目。
- `_inject_chat_mode_prefix` 5 形态烟雾：free / design / numeric / doc / kb，对 TextContent / dict / str / 空 part 均正确注入。
- pytest `tests/unit/{game,routers,app}` → **145 passed / 0 failed**（本批次新增 KB router + cards router 后回归全绿）。
- pytest `tests/unit/game/test_svn_committer.py + test_svn_client.py` → **15 passed**（新增 `test_commit_proposal_revision_guard` 校验 revision 守卫；`commit` 走点改为 `commit_with_retry`）。
- KB 混合检索烟雾：3 模式（vector / keyword / hybrid）对同一 query 均 top-1 命中 score=1.0；hybrid + 类别过滤命中正确条目（`装备数值递增`）。
- 前端 `pnpm build` 通过（含 KB UI CRUD + ApprovalContext SSE；56.48s）。
- 真实 LLM 冒烟（上一版）：`黑铁头盔品质改成3` → `row_id=1011001 / Quality=3`，`context_summary` 正确产出。

## 7. 下一步建议

按重要性：
1. **真实 LLM + 真实 SVN 冒烟**：在用户配置生产 SVN URL/凭据后，跑 game_propose_change → dry_run → approve（走 `/approval/stream` 推送）→ apply → commit；验证审批 SSE 在多 reviewer 端联动。
2. **前端 ApprovalProvider 改 SSE**：把现有轮询替换为 `/api/approval/stream` 订阅；snapshot + 增量结合，断线 3s 重连。
3. **KB 页面接 search**：替换 mock，接 `/search` + `/stats`，hits 显示 score 徽章；支持新建/编辑/删除模态。
4. **SVN 防冲突**：apply 前 `svn info` 校验 revision，commit 重试加 jitter；与 `registry.json` 的版本号串起来。
5. **混合检索**：KB 向量 + 关键词召回融合（BM25-lite + 向量分加权 0.4/0.6）。
