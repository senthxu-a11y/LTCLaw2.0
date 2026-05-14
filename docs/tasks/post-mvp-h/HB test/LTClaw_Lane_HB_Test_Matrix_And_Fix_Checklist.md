# LTClaw Lane H-B：Architecture Baseline Test Matrix & Fix Checklist

## 0. 文档目的

本文件是 Lane H-A 硬化后的独立测试与修复执行文档。

目标是把当前 LTClaw Post-MVP 架构从“主干基本完成”推进到：

```text
Architecture Baseline Closed
```

本轮不继续扩大功能范围，只做测试、验证、小修和收口判定。

---

## 1. Lane H-B 总目标

验证以下核心架构边界在代码层、接口层、UI 层和测试层都成立：

1. KB 不参与正式知识链路。
2. RAG 必须 Map-gated。
3. Release 不读取 KB。
4. Workbench Suggest 不编造 table / field / row_id / evidence_refs。
5. Workbench Source Write 只允许安全 op。
6. Workbench Source Write 必须写 audit。
7. 普通工作台写源表不触发知识更新。
8. Capability gate 对核心接口生效。
9. Unified Model Router failure 行为明确。
10. Legacy UI 不误导用户。

---

## 2. 本轮必须修复的问题

### 2.1 P0 修复项

- [ ] `WorkbenchSourceWriteService` 的 `update_cell` 必须显式校验字段存在。  
  当前状态：最新源码已补，需要测试覆盖。

- [ ] 确认 source-write audit 路径是否满足“按 agent/session 可追溯”。  
  如果当前路径不是按 agent 拆分，至少 audit record 必须包含：
  - `agent_id`
  - `session_id`
  - `time`
  - `release_id_at_write`

- [ ] 检查所有核心 route 是否先调用 `get_agent_for_request()` 再 `require_capability()`。

- [ ] 确认 Legacy KB / Doc Library UI 已明确标记 legacy，且不再作为正式知识入口。

- [ ] 确认 RAG citation deep-link 到 Workbench 不被 Map-gated 改造破坏。

### 2.2 P1 记录项

这些不阻塞 Architecture Baseline 收口，但必须记录为后续 Lane：

- [ ] Unified Model Router 的 timeout / temperature / max_tokens 仍有硬编码，记录为后续 Model Config Hardening。
- [ ] RAG Map Router 召回质量仍是基础词匹配，记录为后续 RAG Quality Lane。
- [ ] Canonical Schema 仍未完成最终质量层，记录为后续 Canonical Schema Lane。

---

## 3. 建议新增测试文件

建议新增或补齐以下测试文件：

```text
tests/unit/game/test_workbench_source_write_service.py
tests/unit/game/test_knowledge_rag_context_map_gated.py
tests/unit/game/test_workbench_suggest_context.py
tests/unit/game/test_knowledge_release_strict_bootstrap.py
tests/unit/app/test_capabilities_agent_profile.py
tests/unit/game/test_unified_model_router_contract.py
console/src/pages/Game/__tests__/legacyKnowledgeLabels.test.tsx
console/src/pages/Game/__tests__/adminPanelStatus.test.ts
```

如果当前测试目录结构不同，可以按现有规范调整，但测试覆盖范围不能删减。

---

# 4. P0 测试矩阵

## 4.1 Workbench Source Write 测试

### 目标

验证真实源表写回能力被 wrapper 正确收口。

### 必测用例

- [ ] `update_cell` 修改已存在字段成功。
- [ ] `update_cell` 修改不存在字段失败。
- [ ] `update_cell` 修改 primary key 失败。
- [ ] `insert_row` 插入合法行成功。
- [ ] `insert_row` 的 `new_value` 不是 object 时失败。
- [ ] `insert_row` 带不存在字段时失败。
- [ ] `insert_row` 的 primary key 与 `row_id` 不一致时失败。
- [ ] `delete_row` 被拒绝。
- [ ] 未知 op 被拒绝。
- [ ] `.xls` 表写回被拒绝。
- [ ] 未知文件格式被拒绝。
- [ ] 写回成功后生成 audit。
- [ ] 写回失败也尽量生成 failure audit。
- [ ] 写回 response 包含 `svn_update_required=true`。
- [ ] 写回 response 包含 `svn_update_warning`。
- [ ] 写回 response 包含 `release_id_at_write`。
- [ ] 写回 response 包含 `source_files`。
- [ ] 写回 response 包含 `changes`。
- [ ] 写回成功后不触发 Rebuild / Release / Publish。

### 建议断言

```text
assert response.success is True
assert response.audit_recorded is True
assert response.svn_update_required is True
assert audit.event_type == "workbench.source.write"
assert audit.agent_id is not empty
assert audit.changes[0].old_value is captured
assert audit.changes[0].new_value is captured
```

### 禁止误判

- [ ] 不能只测 `ChangeApplier.apply()`，必须测 `WorkbenchSourceWriteService`。
- [ ] 不能绕过 `workbench.source.write` 权限直接写源表。
- [ ] 不能把 `delete_row` 作为普通成功路径。

---

## 4.2 Capability / Agent Profile 测试

### 目标

验证本地 Agent Profile capabilities 能真正限制后端接口。

### 必测用例

- [ ] viewer 无法写源表。
- [ ] planner 无法写源表。
- [ ] source_writer 可以写源表。
- [ ] admin 可以写源表。
- [ ] viewer 无法保存 Formal Map。
- [ ] planner 无法 Build Release。
- [ ] source_writer 无法 Publish Release。
- [ ] admin 可以 Publish Release。
- [ ] `my_role=maintainer` 映射 admin。
- [ ] `my_role=planner` 映射 planner。
- [ ] unknown role 映射 viewer。
- [ ] `request.state.capabilities` 被正确注入。
- [ ] `require_capability()` 能读取 request capabilities。

### 建议断言

```text
assert "workbench.source.write" in source_writer.capabilities
assert "workbench.source.write" not in planner.capabilities
assert "*" in admin.capabilities
assert request.state.capabilities is not None
```

### Route 覆盖检查

- [ ] `/game/workbench/source-write` 检查 `workbench.source.write`。
- [ ] `/game/knowledge/map` PUT 检查 `knowledge.map.edit`。
- [ ] `/game/knowledge/map/candidate/from-source` 检查 `knowledge.candidate.write`。
- [ ] `/game/knowledge/releases/build-from-current-indexes` 检查 `knowledge.build`。
- [ ] `/game/knowledge/releases/{release_id}/current` 检查 `knowledge.publish`。

---

## 4.3 Map-gated RAG 测试

### 目标

验证 RAG 只能通过 Current Release Map 的 allowed refs 读取 Release Artifacts。

### 必测用例

- [ ] 无 current release 时返回明确状态。
- [ ] current release 存在时能加载 map。
- [ ] active `table:` ref 可以召回 `table_schema` evidence。
- [ ] active `doc:` ref 可以召回 `doc_knowledge` evidence。
- [ ] active `script:` ref 可以召回 `script_evidence` evidence。
- [ ] ignored ref 不进入 allowed refs。
- [ ] deprecated ref 不进入 allowed refs。
- [ ] unknown prefix ref 不进入 evidence。
- [ ] allowed refs 无 artifact row 时返回 insufficient context。
- [ ] RAG 不读取 KB。
- [ ] RAG 不 fallback 到 legacy retrieval。
- [ ] citation 包含 `citation_id`。
- [ ] citation 包含 `release_id`。
- [ ] citation 包含 `artifact_path`。
- [ ] citation 包含 `source_path`。
- [ ] citation 包含 `row` / `field` / `ref`。

### 建议断言

```text
assert all(item.ref in allowed_refs for item in context.items)
assert ignored_ref not in allowed_refs
assert deprecated_ref not in allowed_refs
assert "knowledge_base" not in loaded_sources
```

---

## 4.4 Workbench Suggest Validator 测试

### 目标

验证 LLM 输出必须经过硬校验，不能编造表、字段、行或 evidence。

### 必测用例

- [ ] 合法 suggestion 通过。
- [ ] 不存在 table 被过滤。
- [ ] 不存在 field 被过滤。
- [ ] 不存在 row_id 被过滤。
- [ ] 不在 allowed evidence refs 中的 evidence_ref 被过滤。
- [ ] 无 formal context 时，不伪造 source_release_id。
- [ ] 只使用 runtime context 的建议标记 `validated_runtime_only`。
- [ ] Draft Overlay 被标记为 draft，不作为 formal evidence。
- [ ] LLM 返回非 JSON 时不生成 changes。
- [ ] LLM 返回空响应时返回明确错误。

### 建议断言

```text
assert invalid_change not in response.changes
assert "filtered" in response.message or diagnostics
assert change.validation_status in ("valid", "validated_runtime_only")
assert evidence_ref in allowed_evidence_refs
```

---

## 4.5 Release strict/bootstrap 测试

### 目标

验证 Release build 不再绕过 Formal Map 审核，bootstrap 必须显式开启。

### 必测用例

- [ ] 有 Formal Map 时 strict build 成功。
- [ ] 无 Formal Map 且 `bootstrap=false` 时 build 失败。
- [ ] 无 Formal Map 且 `bootstrap=true` 时 build 成功并返回 warning。
- [ ] Build Release 不自动 Publish。
- [ ] Publish Current 必须单独调用。
- [ ] Publish Current 需要 `knowledge.publish`。
- [ ] Release 不读取 KB。
- [ ] Release 不读取 Draft / Proposal。
- [ ] Release Artifacts 包含 `map.json`。
- [ ] Release Artifacts 包含 `table_schema.jsonl`。
- [ ] Release Artifacts 包含 `doc_knowledge.jsonl`。
- [ ] Release Artifacts 包含 `script_evidence.jsonl`。

### 建议断言

```text
assert result.build_mode == "strict" or "bootstrap"
assert current_release_id unchanged after build
assert warning contains "bootstrap" when bootstrap=True
```

---

## 4.6 Unified Model Router 测试

### 目标

验证所有正式 LLM 调用走统一模型路由，并且失败语义一致。

### 必测用例

- [ ] `model_type=workbench_suggest` 可调用。
- [ ] `model_type=field_describer` 可调用。
- [ ] `model_type=table_summarizer` 可调用。
- [ ] 未知 model_type 回退 default。
- [ ] 无 active provider 返回 structured error。
- [ ] provider exception 返回 structured error。
- [ ] 空响应返回 structured error。
- [ ] Workbench Suggest 模型失败不生成 changes。
- [ ] TableIndexer 模型失败有明确 error log。

### 建议断言

```text
assert result.ok is False
assert result.error_code is not None
assert result.message is not empty
assert not changes when model failed
```

---

## 4.7 SVN Freeze 测试

### 目标

验证 LTClaw 不再把 SVN runtime 放进主流程。

### 必测用例

- [ ] `start_svn_monitoring()` 返回 disabled。
- [ ] `stop_svn_monitoring()` 返回 disabled。
- [ ] `get_svn_monitoring_status()` 返回 disabled reason。
- [ ] 写源表不执行 SVN Update。
- [ ] 写源表不执行 SVN Commit。
- [ ] 写源表不执行 SVN Revert。
- [ ] UI 中 `/svn-sync` 不再进入旧主流程。
- [ ] 文案提示用户自行 SVN Update / Commit / Revert。

---

# 5. P1 测试矩阵

## 5.1 Legacy UI 测试

- [ ] 导航中显示 `Legacy Knowledge Base` 或等价文案。
- [ ] 导航中显示 `Legacy Doc Library` 或等价文案。
- [ ] Knowledge Base 页面描述明确“不参与正式 Release / RAG / Chat / Workbench Suggest”。
- [ ] Doc Library 页面描述明确“不属于正式 Current Release 知识链路”。
- [ ] Legacy 页面不提供 Build Release / Publish 操作。
- [ ] 用户不会从 Legacy KB 入口进入正式 RAG 查询。

---

## 5.2 Admin Panel 测试

- [ ] Admin Panel 显示 project bundle path。
- [ ] Admin Panel 显示 source config path。
- [ ] Admin Panel 显示 current release id。
- [ ] Admin Panel 显示 previous release id。
- [ ] Admin Panel 显示 current map hash。
- [ ] Admin Panel 显示 formal map status。
- [ ] Admin Panel 显示 RAG status。
- [ ] 无 previous release 时显示 `-` 并 warning。
- [ ] planner / viewer 看不到 admin write actions。
- [ ] admin 可以看到 admin write actions。

---

## 5.3 Citation Deep-link 测试

- [ ] RAG citation 可携带 table。
- [ ] RAG citation 可携带 row。
- [ ] RAG citation 可携带 field。
- [ ] Workbench 页面能读取 citation route context。
- [ ] Workbench 不因 citation 自动创建 draft。
- [ ] Workbench 不因 citation 自动写源表。
- [ ] Workbench 不因 citation 自动发布知识。

---

# 6. 手工验收脚本建议

## 6.1 手工流程 1：管理员知识链路

```text
1. 使用 admin agent 打开 Admin Panel。
2. 确认 current release / previous release / formal map / rag status 可见。
3. 触发 candidate-from-source。
4. 查看 diff review。
5. 保存 Formal Map。
6. Build Release，确认 current 不变。
7. Publish Current，确认 current 更新。
8. 用 RAG 查询正式知识，确认 citation 来自 release artifacts。
```

## 6.2 手工流程 2：普通策划工作台

```text
1. 使用 planner agent 打开 Workbench。
2. 尝试生成 AI suggestion。
3. 确认 suggestion 有 formal_context_status。
4. 确认 Draft Overlay 标记为非正式。
5. 尝试 source-write，确认 403。
6. 切换 source_writer agent。
7. 写回 update_cell。
8. 确认写回前有 SVN Update 提示。
9. 确认写回成功后 audit 生成。
10. 确认 current release 没变。
```

## 6.3 手工流程 3：Legacy KB 验收

```text
1. 打开 Legacy Knowledge Base。
2. 确认页面文案说明它不参与正式 Release / RAG / Chat / Workbench Suggest。
3. 执行 RAG 查询。
4. 确认 citation 来源不是 KB。
5. Build Release，确认不读取 KB。
```

---

# 7. Agent 执行 Checklist

每个测试 / 修复 agent 必须输出：

- [ ] 改动文件列表。
- [ ] 新增测试文件列表。
- [ ] 测试命令。
- [ ] 测试结果。
- [ ] 未覆盖原因。
- [ ] 是否触碰正式知识链路。
- [ ] 是否触碰真实源表写回。
- [ ] 是否触碰权限系统。
- [ ] 是否触碰模型路由。
- [ ] 是否触碰 legacy KB / retrieval。
- [ ] 是否引入新范围。

---

# 8. 收口判定

## 8.1 可以宣布 Architecture Baseline Closed 的条件

- [ ] H1-H6 P0 测试全部通过。
- [ ] Source-write wrapper 修复项全部通过。
- [ ] Legacy KB UI 已标记 legacy。
- [ ] Release 不再读取 KB。
- [ ] RAG 不再读取 KB。
- [ ] RAG 不再绕过 Map。
- [ ] Workbench Suggest 不再绕过 Formal Context。
- [ ] 写源表不触发知识更新。
- [ ] Capability gate 在核心 route 生效。
- [ ] Unified Model Router 是正式模型调用入口。
- [ ] SVN runtime 保持冻结。

## 8.2 不能宣布 Closed 的情况

- [ ] KB 仍参与 Release / RAG / Workbench。
- [ ] RAG 仍全量扫 artifacts 作为正式查询路径。
- [ ] source-write 可以绕过 `workbench.source.write`。
- [ ] 普通工作台可以 delete_row 或 schema ops。
- [ ] 写源表后自动 Build / Publish。
- [ ] 重要 route 没有 capability context。
- [ ] 模型调用又回到模块自配 API。
- [ ] SVN watcher 回到主流程。

---

## 9. 执行结论

Lane H-B 完成后，如果 P0 全部通过，可以正式标记：

```text
Architecture Baseline Closed
```

后续开发进入功能型 Lane：

```text
Lane I：Canonical Schema / Map 构建质量
Lane J：Workbench Suggest 交互体验
Lane K：Admin Panel 完整操作闭环
Lane L：RAG 召回质量提升
```
