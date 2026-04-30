# LTCLAW-GY.X 游戏策划工作台 — v1 进度报告 (3 · 深夜批次 II)

> 更新日期：2026-04-30（深夜补丁 II）
> 关联：[v1-progress-2026-04-30-pm.md](./v1-progress-2026-04-30-pm.md)、[game-planner-workbench-planv.0.md](./game-planner-workbench-planv.0.md)

## 1. 整体完成度

| 维度 | 上一版 (pm) | 本版 (night II) |
|---|---|---|
| 后端骨架 | 100% | 100% |
| 前端骨架 | ~97% | ~98% |
| 数值工作台核心闭环 | ~88% | ~90% |
| 多 agent 项目隔离 | ~75% | ~80% |
| 知识库 / 文档库实用度 | ~75% | ~85% |
| **整体 v1 完成度** | ~88% | **~90%** |

## 2. 本批次新增（P2 4/6 + 模式工具栏正式生效）

### KB 混合检索（P2 #1 ✅）
- [`src/ltclaw_gy_x/knowledge_base/kb_store.py`](../src/ltclaw_gy_x/knowledge_base/kb_store.py) 新增 `_kw_postings/_kw_doc_len/_bm25_search`（k1=1.5, b=0.75，IDF=log(1+(n-df+0.5)/(df+0.5))），与 hashing TF-IDF 余弦双路召回。
- 新方法签名：`search(query, top_k=10, category=None, mode={"vector"|"keyword"|"hybrid"}, alpha=0.6)`，min-max 归一化后线性加权 `alpha*v + (1-alpha)*k`。
- 增删改三处同步维护倒排表（`_index_doc_kw / _unindex_doc_kw`）。

### KB 页面 UI（P2 #2 ✅）
- [`console/src/pages/Game/KnowledgeBase.tsx`](../console/src/pages/Game/KnowledgeBase.tsx) 移除全部 mock；接 `gameKnowledgeBaseApi.{listEntries, createEntry, updateEntry, deleteEntry, search}`。
- `Input.Search enterButton="语义搜索" onSearch={runSearch}`，命中条目带 `Tag color="purple">score {score.toFixed(3)}` 徽章。
- 新建 / 编辑走 Modal，删除走 Popconfirm；tags 在 `[,，;；]` 上分割。

### ApprovalProvider EventSource（P2 #3 ✅）
- [`console/src/contexts/ApprovalContext.tsx`](../console/src/contexts/ApprovalContext.tsx) 在挂载时打开 `EventSource("/api/approval/stream", {withCredentials:true})`，监听 `approval` 事件后立即调 `consoleApi.getPushMessages()` 刷新；`onerror` 后置 3s 重连。
- 原 `ConsolePollService` 轮询保留作兜底；审批延迟从 ~2.5s 收敛到准实时。

### SVN 防冲突（P2 #4 ✅）
- [`src/ltclaw_gy_x/game/svn_client.py`](../src/ltclaw_gy_x/game/svn_client.py) 新增 `commit_with_retry(paths, message, max_retries=5, base_delay=1.0)`：识别 conflict / out-of-date / lock 类错误后跑 `svn update` 再退避重试（`base * 2**i * U(0.5, 1.5)`），非冲突错误立即抛出。
- [`src/ltclaw_gy_x/game/svn_committer.py`](../src/ltclaw_gy_x/game/svn_committer.py) 新签名 `commit_proposal(..., expected_revision=None, max_retries=5)`：本地 revision 比期望大时抛 `CommitError`，避免 clobber 新工作；commit 改走 `commit_with_retry`。

### 5-模式工具栏正式生效（A/B/C/D 全部落地 ✅）
- **A（行为差异化）/ C（header 链路验证）**：`src/ltclaw_gy_x/app/routers/console.py` 已实现 `_inject_chat_mode_prefix(request, native_payload)`，把 `_CHAT_MODE_PREFIX` 中 `design/numeric/doc/kb` 的提示前缀拼到首条 user message 的首条 text part。新增 [`tests/unit/routers/test_console_chat_mode.py`](../tests/unit/routers/test_console_chat_mode.py) 12 个用例覆盖：
  - free / unknown / no-header → noop
  - dict / TextContent 对象 / str 三种 part 形态命中
  - 仅修改首条 text part；无 text part 时插入合成 `TextContent`
  - header 大小写不敏感（`KB` 与 `kb` 等价）
- **B（UI 反馈）**：[`console/src/pages/Chat/components/ChatModeToolbar.tsx`](../console/src/pages/Chat/components/ChatModeToolbar.tsx) 切换模式时调 `App.useApp().message.success/info` 弹 toast。
- **D（模式驱动卡片）**：切换 `numeric/kb/doc/design` 自动 `pushWorkbenchCard` 推 `mode-hint-{mode}` 卡（numeric→`numeric_table`、kb→`kb_hit`、其余→`draft_doc`），`summary` 即注入到首条 text part 的提示前缀；用户在右栏面板能直接看到当前模式的"系统层指令"。

## 3. P2 仍未做（推迟到下一批次）

- [ ] **P2 #5** 代码类索引（.cs 类名 / 方法签名）— 需 Roslyn 级 .cs 解析器 + 单独索引存储，独立子系统
- [ ] **P2 #6** 变更影响分析（reverse-impact）— 需依赖图反向传播、引用追踪，独立子系统
- [ ] **P3** 主索引机模式 vs 竞争模式 — 需用户决策

## 4. 真实环境冒烟（待用户配生产 SVN 凭据）

- [ ] T1 真实 SVN 连通性（拉 changelog / update / checkout）
- [ ] T2 dry_run + apply 闭环（csv/xlsx 编码、commit、rollback）
- [ ] T3 真 LLM + 真 SVN 端到端（含审批 SSE 多 reviewer 联动）
- [ ] T4 前端体验小修（lazyWithRetry warn 抑制等）

## 5. 验证

- pytest `tests/unit` → **1932 passed / 0 failed / 3 skipped**（含本批次新增 12 个 `test_console_chat_mode` + 5 个 `test_svn_committer`，全量耗时 ~419s）。
- pnpm build → 55.15s 绿（含 KB UI、ApprovalContext SSE、ChatModeToolbar toast+卡片）。
- 13 个易腐 .py / .tsx 文件全部 NUL-free，AST OK；svn_client / svn_committer / test_svn_committer 本批 DLP 撞坏后已通过 `git checkout HEAD -- ...` + heredoc 重 patch 恢复。

## 6. 下一步建议

按重要性：
1. **真实 LLM + 真实 SVN 冒烟**：用户配置生产 SVN URL/凭据后，跑 `game_propose_change → dry_run → approve（走 /approval/stream 推送）→ apply → commit_with_retry`；验证 multi-reviewer SSE 联动 + revision 守卫真实表现。
2. **P2 #5 .cs 索引**：起独立 `code_index` 子系统（.cs → 类/方法符号表），与 `table_indexer` 解耦，落 `{workspace}/code_index/`。
3. **P2 #6 reverse-impact**：基于 `dependency_graph` + .cs 索引做反向传播，在 propose / preview 阶段提示「本次改动会影响 X、Y、Z」。
