# LTClaw Lane H：Post-MVP Architecture Stabilization Validation

## 0. 文档目的

本 Lane 用于验证和硬化当前已经完成的 Post-MVP 架构收口代码，目标不是继续扩大功能，而是确认第一批核心架构改造已经真正闭环。

本轮完成后，如果所有 P0 / P1 验收项通过，可以将整体架构标记为：

```text
Post-MVP Architecture Baseline Locked
```

含义是：

```text
Map-first / Map-gated RAG / Workbench Source Write / Agent Profile / Unified Model Router / SVN 外置流程
这些核心架构边界可以冻结，后续只在该架构内继续做功能增强。
```

但这不等于产品全部完成，也不等于 Canonical Schema、Map 质量、管理员面板体验已经完成。它只表示“架构主干可以收口”。

---

## 1. Lane H 总目标

### 1.1 目标

验证当前源码已经符合以下核心架构边界：

1. KB 不再是正式知识系统。
2. 正式知识查询只走 Map-gated RAG。
3. Release 不再读取 workspace/session KB。
4. Workbench Suggest 接入 Formal Context + Runtime Context + Draft Overlay。
5. Workbench Suggest 输出经过 table / field / row_id / evidence_refs 硬校验。
6. Workbench 写真实源表必须走 source-write wrapper。
7. 真实源表写回必须受 `workbench.source.write` 控制。
8. 普通工作台只允许 `update_cell` 和 `insert_row`。
9. 写回真实源表后必须记录 audit。
10. 写回真实源表后不触发 Rebuild / Release / Publish。
11. Agent Profile capabilities 已经进入后端 request state。
12. Formal Game model 调用统一走 Unified Model Router；generic agent chat runner 保持 compatibility boundary。
13. SVN runtime 已冻结，SVN update / commit / revert 交给外部 SVN 流程。
14. Candidate Map 已区分 release snapshot 和 source/canonical candidate。
15. Strict / Bootstrap Release 模式边界明确。

---

## 2. Lane H 不做范围

本 Lane 严格禁止扩大范围。

### 2.1 不做

- [ ] 不恢复 KB 正式链路。
- [ ] 不新增服务器账号系统。
- [ ] 不新增服务器审批流。
- [ ] 不新增文件锁。
- [ ] 不新增自动备份系统。
- [ ] 不做普通策划新增字段。
- [ ] 不做普通策划新增表。
- [ ] 不开放 delete_row 给普通工作台。
- [ ] 不开放删表、改表名、改路径、改主键。
- [ ] 不恢复 SVN watcher 主流程。
- [ ] 不让写源表自动触发 Rebuild / Release / Publish。
- [ ] 不让 RAG 绕过 Map 直接扫 artifacts。
- [ ] 不让 Workbench Suggest 读取 KB 作为正式证据。
- [ ] 不让 Map / RAG / Chat / Workbench 各自配置模型 API。
- [ ] 不做 LLM 自动生成数据整理脚本。
- [ ] 不一次性重构所有路径系统。
- [ ] 不直接删除 legacy KB / retrieval 代码，除非确认无依赖。

---

## 3. Lane H 任务分组

Lane H 分为 8 个任务组：

```text
H1：KB 移除与正式知识链路验收
H2：Map-gated RAG 验收
H3：Workbench Suggest 硬化验收
H4：Workbench Source Write 硬化验收
H5：Agent Profile / Capability 验收
H6：Unified Model Router 验收
H7：Release / Candidate / Admin Flow 验收
H8：Legacy UI / Route / Test Matrix 收口
```

推荐执行顺序：

```text
H1 → H2 → H3 → H4 → H5 → H6 → H7 → H8
```

其中 H1-H6 是 P0，H7-H8 是 P1。

---

## H1：KB 移除与正式知识链路验收

### 目标

确认 KB 已经从正式知识链路移除，正式知识底座只剩：

```text
Formal Map + Release Artifacts + Map-gated RAG
```

### 源码重点

重点检查：

```text
src/ltclaw_gy_x/game/knowledge_release_service.py
src/ltclaw_gy_x/game/knowledge_rag_context.py
src/ltclaw_gy_x/app/routers/game_workbench.py
src/ltclaw_gy_x/app/routers/game_knowledge_release.py
legacy KB / retrieval 相关入口
前端 /knowledge-base 路由和导航
```

### Checklist

#### Release 链路

- [ ] `knowledge_release_service.py` 不再 import `get_kb_store`。
- [ ] Release build 不再调用 `_load_approved_doc_entries(workspace)`。
- [ ] Release build 不再读取 workspace KB。
- [ ] Release build 不再读取 session KB。
- [ ] Release build 的 docs 来自 Formal Map / project-owned facts / current indexes。
- [ ] `doc_knowledge.jsonl` 不再由 KB 直接输出。
- [ ] Build Release 缺 Formal Map 时默认 strict 阻断。
- [ ] Bootstrap 只能显式开启，并带 warning。

#### RAG 链路

- [ ] RAG 不读取 `knowledge_base`。
- [ ] RAG 不读取 `kb_store`。
- [ ] RAG 不读取 workspace/session KB。
- [ ] RAG 只读取 Current Release 对应 Release Artifacts。
- [ ] RAG 不把 KB 作为 fallback evidence。

#### Workbench Suggest 链路

- [ ] Workbench Suggest 不读取 KB。
- [ ] Workbench Suggest 的正式证据只来自 Formal Context。
- [ ] Formal Context 来自 Current Release + Map-gated RAG。
- [ ] Draft Overlay 不被误认为正式 evidence。

#### Chat / UI 链路

- [ ] 普通项目知识问答不再调用 KB。
- [ ] `/knowledge-base` 如果仍存在，必须标记 legacy 或隐藏。
- [ ] 导航中不再把 Knowledge Base 表述为正式知识入口。
- [ ] 文档中不再把 KB 作为正式知识系统。

### 验收标准

- [ ] 搜索 `get_kb_store`，确认不在 Release / RAG / Workbench 正式链路中出现。
- [ ] 搜索 `knowledge_base`，确认仅出现在 legacy/debug/migration 或旧 UI 中。
- [ ] 创建一个只有 Release Artifacts、没有 KB 的项目，RAG 可正常回答。
- [ ] 删除/清空 KB 后，Build Release 不受影响。
- [ ] 删除/清空 KB 后，Workbench Suggest 不受影响。

### 通过标准

```text
KB 不再影响 Release / RAG / Workbench / Chat 的正式项目知识结果。
```

---

## H2：Map-gated RAG 验收

### 目标

确认 RAG 必须先经过 Map Router / allowed refs，再读取 Release Artifacts，不允许直接全量扫 artifacts 形成正式结果。

### 源码重点

```text
src/ltclaw_gy_x/game/knowledge_rag_context.py
src/ltclaw_gy_x/app/routers/game_knowledge_rag.py 或相关 RAG route
前端 citation handoff
```

### Checklist

#### Routing

- [ ] RAG 查询先加载 Current Release。
- [ ] RAG 查询加载 release map。
- [ ] RAG 查询调用 map route 逻辑。
- [ ] RAG 生成 `allowed_refs`。
- [ ] RAG 只按 `allowed_refs` 读取 artifacts。
- [ ] `ignored` refs 不进入 `allowed_refs`。
- [ ] `deprecated` refs 不进入 `allowed_refs`。
- [ ] focus refs 存在时，只允许 active focus refs。
- [ ] focus refs 不存在时，可以基于 query 命中和 Map relationships 扩展邻接 refs。

#### Artifact 读取

- [ ] `table:` refs 只映射到 `table_schema`。
- [ ] `doc:` refs 只映射到 `doc_knowledge`。
- [ ] `script:` refs 只映射到 `script_evidence`。
- [ ] 不支持未知 ref prefix 进入正式 evidence。
- [ ] 不全量读取所有 artifact rows 作为正式候选。
- [ ] allowed refs 无 evidence 时返回 insufficient context。

#### Citation

- [ ] citation 保留 `citation_id`。
- [ ] citation 保留 `release_id`。
- [ ] citation 保留 `source_type`。
- [ ] citation 保留 `artifact_path`。
- [ ] citation 保留 `source_path`。
- [ ] citation 保留 `title`。
- [ ] citation 保留 `row`。
- [ ] citation 保留 `field`。
- [ ] citation 保留 `ref`。
- [ ] Workbench citation deep-link 仍可用。

#### Fallback

- [ ] 无 Current Release 时返回 `no_current_release`。
- [ ] 无 allowed refs 时返回 `insufficient_context`。
- [ ] allowed refs 无 evidence 时返回 `allowed_refs_without_evidence`。
- [ ] 不 fallback 到 KB。
- [ ] 不 fallback 到 legacy retrieval。

### 测试用例

- [ ] 查询 active table ref，能召回 table_schema evidence。
- [ ] 查询 ignored table ref，不返回 evidence。
- [ ] 查询 deprecated doc ref，不返回 evidence。
- [ ] 指定 focus ref 时，只返回该 focus ref 相关 evidence。
- [ ] release 缺 artifact 文件时，返回 insufficient context，而不是报 500。
- [ ] citation 点击进入 Workbench 后 table / field / row 上下文仍然可用。

### 通过标准

```text
RAG 正式结果只能由 Current Release Map 的 allowed refs 驱动。
```

---

## H3：Workbench Suggest 硬化验收

### 目标

确认 Workbench Suggest 已升级为：

```text
Formal Knowledge Context + Workbench Runtime Context + Draft Overlay + Chat History
```

并且 LLM 输出必须经过硬校验。

### 源码重点

```text
src/ltclaw_gy_x/app/routers/game_workbench.py
src/ltclaw_gy_x/game/workbench_suggest_context.py
console/src/pages/Game/components/WorkbenchChat.tsx
console/src/api/modules/gameWorkbench.ts
```

### Checklist

#### Context Builder

- [ ] Suggest 构建 Formal Context。
- [ ] Formal Context 来自 Current Release + Map-gated RAG。
- [ ] Suggest 构建 Runtime Context。
- [ ] Runtime Context 包含 context_tables。
- [ ] Runtime Context 包含 fields。
- [ ] Runtime Context 包含 row_index。
- [ ] Runtime Context 包含 matched_columns。
- [ ] Suggest 构建 Draft Overlay。
- [ ] Draft Overlay 包含 current_pending。
- [ ] Suggest 构建 Chat History。
- [ ] Chat History 截断最近若干轮，避免 prompt 过大。

#### Prompt Contract

- [ ] prompt 明确禁止修改 Formal Map。
- [ ] prompt 明确禁止修改 Current Release。
- [ ] prompt 明确禁止修改正式 RAG。
- [ ] prompt 明确 evidence_refs 只能来自 Formal Context。
- [ ] prompt 明确 Draft Overlay 不能作为 formal evidence。
- [ ] prompt 明确 row_id 必须来自 row_index。
- [ ] prompt 明确 field 必须来自对应表 fields。
- [ ] prompt 明确无法定位时 changes 留空。

#### Validator

- [ ] table 必须在 context_tables。
- [ ] field 必须在对应 table fields。
- [ ] row_id 必须在 row_index primary key 集合。
- [ ] evidence_refs 必须在 allowed evidence refs。
- [ ] 非法 suggestion 被过滤。
- [ ] 被过滤的 suggestion 在 message 中说明。
- [ ] 无 formal evidence 时，source_release_id 不应伪造。
- [ ] 只使用 runtime context 的 change 标记 `validated_runtime_only`。

#### Model Router

- [ ] Suggest 调用 `call_model_result`。
- [ ] model_type 使用 `workbench_suggest`。
- [ ] 模型失败返回 502 或明确错误。
- [ ] 模型失败不生成空 changes 冒充成功。

#### Frontend

- [ ] 建议卡显示 reason。
- [ ] 建议卡显示 confidence。
- [ ] 建议卡显示 validation_status。
- [ ] 建议卡显示 evidence_refs。
- [ ] 建议卡显示是否 uses_draft_overlay。
- [ ] Draft Overlay 明确标记为非正式上下文。
- [ ] formal_context_status 可见或可诊断。

### 测试用例

- [ ] LLM 返回不存在 table，被过滤。
- [ ] LLM 返回不存在 field，被过滤。
- [ ] LLM 返回不存在 row_id，被过滤。
- [ ] LLM 返回不在 allowed list 的 evidence_ref，被过滤。
- [ ] 无 current release 时，Suggest 仍可基于 runtime context 给出低等级建议或说明证据不足。
- [ ] 有 current release 时，Suggest 返回 evidence_refs。
- [ ] current_pending 存在时，uses_draft_overlay 可正确标记。

### 通过标准

```text
Workbench Suggest 不再是“LLM 猜改表”，而是正式证据 + 运行态数据驱动的可校验建议。
```

---

## H4：Workbench Source Write 硬化验收

### 目标

确认真实源表写回已经安全收口。

### 源码重点

```text
src/ltclaw_gy_x/game/workbench_source_write_service.py
src/ltclaw_gy_x/app/routers/game_workbench.py
src/ltclaw_gy_x/game/change_applier.py
console/src/api/modules/gameWorkbench.ts
前端写回按钮/确认弹窗
```

### Checklist

#### Permission

- [ ] `/game/workbench/source-write` 调用 `require_capability("workbench.source.write")`。
- [ ] 无 `workbench.source.write` 返回 403。
- [ ] `planner` 默认没有 `workbench.source.write`。
- [ ] `source_writer` 有 `workbench.source.write`。
- [ ] `admin` 有 `*` 或等价权限。

#### Op Allowlist

- [ ] 允许 `update_cell`。
- [ ] 允许 `insert_row`。
- [ ] 禁止 `delete_row`。
- [ ] 禁止 schema ops。
- [ ] 禁止新增字段。
- [ ] 禁止新增表。
- [ ] 禁止删除字段。
- [ ] 禁止删除表。
- [ ] 禁止改表名。
- [ ] 禁止改路径。
- [ ] 禁止改主键。

#### update_cell 校验

- [ ] `update_cell` 必须有 field。
- [ ] `update_cell` 不能改 primary key。
- [ ] `update_cell` 应显式校验 field 存在于 headers。
- [ ] `update_cell` 失败时返回明确错误。

#### insert_row 校验

- [ ] `insert_row` 的 new_value 必须是 object。
- [ ] `insert_row` 的所有字段必须存在于 headers。
- [ ] `insert_row` 不允许带新增字段。
- [ ] `insert_row` 不允许修改 primary key。
- [ ] 主键值与 row_id 不一致时失败。

#### File Support

- [ ] 支持 `.xlsx` 写回。
- [ ] 支持 `.csv` 写回。
- [ ] 支持 `.txt` 写回。
- [ ] 明确拒绝 `.xls` 写回。
- [ ] 明确拒绝未知文件格式。
- [ ] TXT 表头 metadata 如存在，写回前必须确认不会丢失。

#### SVN Boundary

- [ ] 写回前端展示 SVN Update 提示。
- [ ] 后端 response 包含 `svn_update_required=true`。
- [ ] 后端 response 包含 `svn_update_warning`。
- [ ] 后端不执行 SVN Update。
- [ ] 后端不执行 SVN Commit。
- [ ] 后端不执行 SVN Revert。

#### Audit

- [ ] 写回成功后写 audit。
- [ ] 写回失败也尽量写 audit。
- [ ] audit 记录 event_type。
- [ ] audit 记录 agent_id。
- [ ] audit 记录 session_id。
- [ ] audit 记录 time。
- [ ] audit 记录 release_id_at_write。
- [ ] audit 记录 reason。
- [ ] audit 记录 source_files。
- [ ] audit 记录 changes。
- [ ] audit 记录 old_value / new_value。
- [ ] audit 路径与文档最终约定一致。

#### Non-trigger

- [ ] 写回后不调用 Rebuild Index。
- [ ] 写回后不调用 Build Release。
- [ ] 写回后不调用 Publish / Set Current。
- [ ] 写回后不调用 RAG rebuild。
- [ ] 写回后不启动 SVN watcher。

### 测试用例

- [ ] viewer 调用 source-write，403。
- [ ] planner 调用 source-write，403。
- [ ] source_writer update_cell 成功。
- [ ] source_writer insert_row 成功。
- [ ] source_writer delete_row 失败。
- [ ] update_cell 不存在字段失败。
- [ ] insert_row 带新字段失败。
- [ ] 修改 primary key 失败。
- [ ] `.xls` 表写回失败并提示转换。
- [ ] 写回成功后 audit 文件生成。
- [ ] 写回成功后 current release 不变。

### 通过标准

```text
普通策划写真实源表能力受控、可追溯、不影响知识底座。
```

---

## H5：Agent Profile / Capability 验收

### 目标

确认本地 Agent Profile 已经成为角色边界标准，`my_role` 只作为 legacy shortcut。

### 源码重点

```text
src/ltclaw_gy_x/app/agent_context.py
src/ltclaw_gy_x/app/capabilities.py
src/ltclaw_gy_x/game/config.py
console/src/api/types/permissions.ts
console/src/api/types/agent.ts
前端 Agent Store / 权限工具
```

### Checklist

#### Capability Catalog

- [ ] 包含 `knowledge.read`。
- [ ] 包含 `knowledge.build`。
- [ ] 包含 `knowledge.publish`。
- [ ] 包含 `knowledge.map.read`。
- [ ] 包含 `knowledge.map.edit`。
- [ ] 包含 `knowledge.candidate.read`。
- [ ] 包含 `knowledge.candidate.write`。
- [ ] 包含 `workbench.read`。
- [ ] 包含 `workbench.test.write`。
- [ ] 包含 `workbench.test.export`。
- [ ] 包含 `workbench.source.write`。

#### Roles

- [ ] viewer 只有只读能力。
- [ ] planner 可以读知识、读工作台、生成草案、导出测试。
- [ ] source_writer 可以写真实源表。
- [ ] admin 具备 `*`。
- [ ] unknown role 回退 viewer。

#### Legacy my_role

- [ ] `my_role=maintainer` 映射 admin。
- [ ] `my_role=planner` 映射 planner。
- [ ] 其他 my_role 映射 viewer。
- [ ] 新逻辑以 Agent Profile capabilities 为准。

#### Request State

- [ ] `get_agent_for_request()` 注入 `request.state.agent_id`。
- [ ] `get_agent_for_request()` 注入 `request.state.agent_profile`。
- [ ] `get_agent_for_request()` 注入 `request.state.capabilities`。
- [ ] `get_agent_for_request()` 注入 `request.state.user`。
- [ ] require_capability 可以读到 request capabilities。

#### Coverage

- [ ] Map read route 检查 `knowledge.map.read`。
- [ ] Map save route 检查 `knowledge.map.edit`。
- [ ] Candidate read route 检查 `knowledge.candidate.read`。
- [ ] Candidate write route 检查 `knowledge.candidate.write`。
- [ ] Release build 检查 `knowledge.build`。
- [ ] Publish current release 检查 `knowledge.publish`。
- [ ] Workbench source-write 检查 `workbench.source.write`。

### 测试用例

- [ ] viewer 保存 Formal Map 被拒绝。
- [ ] planner Build Release 被拒绝。
- [ ] source_writer source-write 成功。
- [ ] planner source-write 被拒绝。
- [ ] admin Publish 成功。
- [ ] 无 agent profile 时 my_role legacy mapping 生效。

### 通过标准

```text
权限不再只靠前端按钮隐藏，后端 route 能识别当前 agent capabilities。
```

---

## H6：Unified Model Router 验收

### 目标

确认 Formal Game LLM 调用统一走一个模型路由入口，不再让 Map / RAG / Workbench 分别配置模型 API。
generic agent chat runner 可以保留现有兼容边界，但必须明确它不承担 Post-MVP formal Game model routing 语义。

### 源码重点

```text
src/ltclaw_gy_x/game/unified_model_router.py
src/ltclaw_gy_x/game/service.py
src/ltclaw_gy_x/game/table_indexer.py
src/ltclaw_gy_x/game/dependency_resolver.py
src/ltclaw_gy_x/app/routers/game_workbench.py
Chat compatibility boundary / RAG answer route
provider config 相关文件
```

### Checklist

#### Unified Entry

- [ ] 存在 Unified Model Router。
- [ ] SimpleModelRouter 只是 compatibility adapter。
- [ ] Workbench Suggest 调用 `call_model_result`。
- [ ] TableIndexer 调用统一 router。
- [ ] DependencyResolver 调用统一 router。
- [ ] RAG Answer 调用统一 router。
- [ ] generic agent chat runner 被明确标记为 compatibility boundary。
- [ ] console formal chat 只注入 current-release formal context，不自行选择 provider/model。

#### model_type

- [ ] 支持 `default`。
- [ ] 支持 `field_describer`。
- [ ] 支持 `table_summarizer`。
- [ ] 支持 `map_builder`。
- [ ] 支持 `map_diff_explainer`。
- [ ] 支持 `rag_answer`。
- [ ] 支持 `workbench_suggest`。
- [ ] 未知 model_type 回退 default。
- [ ] model_type 进入 project config model slot 映射。

#### Provider Boundary

- [ ] Formal Game 功能模块不直接读取 API Key。
- [ ] Formal Game 功能模块不直接读取 Base URL。
- [ ] Formal Game 功能模块不直接选择 Provider。
- [ ] Formal Game 功能模块不直接选择 Model。
- [ ] Formal Game 功能模块只提交 prompt / model_type / metadata。

#### Error Handling

- [ ] 空响应返回 structured error。
- [ ] provider exception 返回 structured error。
- [ ] no active model 返回 structured error。
- [ ] provider not configured 返回 structured error。
- [ ] 模块不能把空字符串当成功结果。

#### 后续待增强

- [ ] timeout 从配置读取。
- [ ] temperature 从配置读取。
- [ ] max_tokens 从配置读取。
- [ ] retry 从配置读取。
- [ ] fallback 从配置读取。

### 测试用例

- [ ] 无 active model 时 Workbench Suggest 返回明确错误。
- [ ] 模型空响应时不生成 changes。
- [ ] model_type=workbench_suggest 走对应 slot 或 default。
- [ ] model_type 未知时回退 default。
- [ ] provider exception 不导致 500 无说明。

### 通过标准

```text
Formal Game 模型调用统一入口已经建立；generic agent chat runner 作为 compatibility boundary 被明确隔离，配置化细节可以进入下一 lane 继续完善。
```

---

## H7：Release / Candidate / Admin Flow 验收

### 目标

确认管理员知识维护线符合：

```text
Candidate from Source → Map Diff Review → Formal Map → Build Release → Publish Current
```

### 源码重点

```text
src/ltclaw_gy_x/app/routers/game_knowledge_map.py
src/ltclaw_gy_x/app/routers/game_knowledge_release.py
src/ltclaw_gy_x/game/knowledge_map_candidate.py
src/ltclaw_gy_x/game/knowledge_release_service.py
Admin Panel 前端
```

### Checklist

#### Candidate

- [ ] `GET /candidate` 表示 release snapshot candidate。
- [ ] `POST /candidate/from-source` 表示 source/canonical candidate。
- [ ] from-source 检查 `knowledge.candidate.write`。
- [ ] from-release 检查 `knowledge.candidate.read`。
- [ ] from-source 可以使用 existing formal map as hint。
- [ ] from-source 生成 diff_review。
- [ ] diff_review 包含 added_refs。
- [ ] diff_review 包含 removed_refs。
- [ ] diff_review 包含 changed_refs。
- [ ] diff_review 包含 unchanged_refs。
- [ ] diff_review 包含 warnings。

#### Formal Map

- [ ] get formal map 检查 `knowledge.map.read`。
- [ ] save formal map 检查 `knowledge.map.edit`。
- [ ] save formal map 校验 map 必填。
- [ ] 保存后返回 map_hash。
- [ ] 保存后返回 updated_at。
- [ ] 保存后返回 updated_by。

#### Release

- [ ] build release 检查 `knowledge.build`。
- [ ] build-from-current-indexes 检查 `knowledge.build`。
- [ ] publish current 检查 `knowledge.publish`。
- [ ] strict build 无 Formal Map 时阻止。
- [ ] bootstrap build 必须显式传参。
- [ ] bootstrap build 返回 warning。
- [ ] Build Release 不自动 Publish。
- [ ] Publish Current 单独接口。

#### Admin Panel

- [ ] Admin Panel 显示 current release。
- [ ] Admin Panel 显示 previous release。
- [ ] Admin Panel 显示 Formal Map 状态。
- [ ] Admin Panel 显示 storage summary。
- [ ] Admin 操作按钮按 capability 显示。
- [ ] 普通策划看不到管理员写操作。

### 测试用例

- [ ] 无 Formal Map strict build 失败。
- [ ] 无 Formal Map bootstrap build 成功但带 warning。
- [ ] 有 Formal Map strict build 成功。
- [ ] Build 后 current release 不变。
- [ ] Publish 后 current release 更新。
- [ ] planner 调用 publish 被拒绝。
- [ ] candidate/from-source 返回 diff_review。

### 通过标准

```text
管理员知识维护线已经和普通工作台完全分离。
```

---

## H8：Legacy UI / Route / Test Matrix 收口

### 目标

确认旧入口不会误导用户，测试矩阵能覆盖本轮硬化。

### Checklist

#### Legacy UI

- [ ] Knowledge Base 页面隐藏或标记 legacy。
- [ ] Doc Library 如果仍存在，明确不等于正式 RAG。
- [ ] `/knowledge-base` 不在主导航中作为正式入口。
- [ ] `/svn-sync` 不进入旧 SVN runtime 页面。
- [ ] `/game/advanced/svn` 重定向到新入口或说明页。
- [ ] Advanced Page 表述为 Admin Panel 或本地管理入口。
- [ ] SVN 配置文案改为 local project root / legacy SVN notes。

#### Legacy Backend

- [ ] SVN watcher 默认不启动。
- [ ] start_svn_monitoring 返回 disabled。
- [ ] stop_svn_monitoring 返回 disabled。
- [ ] get_svn_monitoring_status 返回 disabled reason。
- [ ] sync route 返回 disabled 或不执行 SVN 操作。
- [ ] legacy retrieval 不作为正式知识入口。

#### Test Matrix

- [ ] 权限测试完成。
- [ ] RAG 测试完成。
- [ ] Release 测试完成。
- [ ] Workbench Suggest 测试完成。
- [ ] Source-write 测试完成。
- [ ] Audit 测试完成。
- [ ] Model Router 测试完成。
- [ ] SVN freeze 测试完成。
- [ ] Citation deep-link 测试完成。

### 通过标准

```text
旧入口不会把用户带回 KB / legacy retrieval / SVN runtime / 自动知识更新流程。
```

---

## 4. Lane H 总验收标准

Lane H 完成必须满足以下硬性标准。

### P0 必须全部通过

- [ ] KB 不参与正式链路。
- [ ] RAG 必须 Map-gated。
- [ ] Release 不读 KB。
- [ ] Workbench Suggest 接入 Formal Context。
- [ ] Suggest 输出 table / field / row_id / evidence_refs 校验通过。
- [ ] source-write 受 `workbench.source.write` 控制。
- [ ] source-write 禁止 delete_row / schema ops。
- [ ] source-write 成功写 audit。
- [ ] source-write 不触发 Rebuild / Release / Publish。
- [ ] Agent Profile capabilities 注入 request state。
- [ ] Unified Model Router 作为模型调用入口。
- [ ] SVN runtime 已冻结。

### P1 应尽量完成

- [ ] KB UI 标记 legacy 或隐藏。
- [ ] legacy retrieval 标记 debug / migration。
- [ ] Admin Panel 显示关键状态。
- [ ] Candidate from source 可用。
- [ ] Strict / Bootstrap Release UX 明确。
- [ ] Workbench evidence_refs 前端可见。
- [ ] SVN Update 提示在写回前可见。
- [ ] 最小测试矩阵完成。

---

## 5. Lane H 完成后的收口判断

### 5.1 可以收口的部分

Lane H 完成后，可以冻结以下架构边界：

```text
1. 正式知识系统只保留 Map-gated RAG。
2. KB 不再作为正式知识来源。
3. Map 是唯一正式知识结构。
4. Release Artifacts 是正式证据快照。
5. Workbench 只消费 Map/RAG，不更新知识底座。
6. 普通策划可写真实源表，但不能改结构。
7. 写真实源表不触发知识更新。
8. 管理员手动维护 Map/RAG/Release。
9. 权限以 Agent Profile capabilities 为新标准。
10. 模型调用统一走 Model Router。
11. SVN 同步与恢复交给外部 SVN 流程。
```

这意味着整体框架可以标记为：

```text
Architecture Baseline Closed
```

### 5.2 不能说已经完成的部分

Lane H 完成后，以下仍然属于后续增强：

```text
1. Canonical Schema 质量。
2. 字段别名 / 语义归一化。
3. LLM 辅助系统聚类。
4. Map Diff Review 体验。
5. Admin Panel 完整操作体验。
6. RAG 召回质量提升。
7. Workbench 建议卡交互体验。
8. MCP 管理员工具池。
9. Legacy 代码最终删除。
10. 完整自动化测试覆盖。
```

### 5.3 最终判断

如果 Lane H 的 P0 全部通过，P1 关键项没有明显缺口，则：

```text
整个框架可以收口。
```

收口后的开发策略应改为：

```text
不再讨论大架构方向。
只在当前架构内继续做功能 lane。
```

---

## 6. Agent 执行提示词模板

可以把以下模板交给执行 agent：

```text
你正在执行 LTClaw Lane H：Post-MVP Architecture Stabilization Validation。

严格遵守：
1. 不新增大架构方向。
2. 不恢复 KB 正式链路。
3. 不让 RAG 绕过 Map。
4. 不开放普通工作台结构变更。
5. 不让 source-write 触发 Rebuild / Release / Publish。
6. 不新增服务端账号、审批、文件锁、自动备份。
7. 不让各模块单独配置模型 API。

请按 H1 → H8 的顺序逐项检查和修复。
每次只处理一个明确 slice。
提交时必须说明：
- 修改了哪些文件
- 对应哪个 Hx checklist
- 哪些验收项通过
- 哪些验收项仍未完成
- 是否触碰正式知识链路
- 是否触碰真实源表写回
- 是否触碰权限
- 是否触碰模型调用
- 是否保留 legacy 兼容
```
