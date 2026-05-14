# P0-07 Workbench Suggest Context Builder 与 SuggestChange 证据合同

来源：总规划书 P0、Phase 8、9.2-9.5、19.3.2、19.3.3。

## 前置边界

本任务必须遵循 P0-00《架构边界冻结》：这里只补齐 Workbench Suggest 的后端上下文合同和证据边界，不做前端体验增强，不让普通策划借建议链路更新 Formal Map、Current Release 或正式 RAG。

## 目标

先在 P0 补齐工作台 AI 建议的后端合同：Workbench Suggest 必须消费 Current Map/RAG 正式知识上下文、工作台运行上下文和 Draft Overlay，并返回可校验的 `evidence_refs`。前端展示增强放到 P3。

## Capability 与 Legacy 兼容说明

- [ ] 本任务只允许引用已有 capability 名称 `workbench.read`、`knowledge.read`；不新增 capability。
- [ ] 本任务不赋予普通策划 `knowledge.publish` 或 `workbench.source.write` 的额外范围。
- [ ] 如存在 legacy KB / legacy retrieval / 旧 Suggest 上下文拼装逻辑，只能兼容迁移到 Map-gated RAG + Draft Overlay 新合同，不得继续作为正式 evidence 主链路。

## Checklist

- [ ] 定义 Workbench Suggest Context Builder。
- [ ] 接入 Current Release Map。
- [ ] 接入 Map Router。
- [ ] 接入 Map-gated RAG Context。
- [ ] 接入 Release Artifacts citations。
- [ ] 保留当前 `context_tables`。
- [ ] 保留当前 `row_index`。
- [ ] 保留 `current_pending`。
- [ ] 保留 `chat_history`。
- [ ] 定义 Draft Overlay 输入。
- [ ] 定义 Suggest Prompt 标准模板。
- [ ] 定义 SuggestResponse 增加 `evidence_refs`。
- [ ] 定义 SuggestChange 增加 `confidence`。
- [ ] 定义 SuggestChange 增加 `uses_draft_overlay`。
- [ ] 定义 SuggestChange 增加 `source_release_id`。
- [ ] 定义 SuggestChange 增加 `validation_status`。
- [ ] 后端硬校验 LLM 输出的 table / field / row_id。
- [ ] 非法 field 被 validator 拦截。
- [ ] 无法定位 row_id 时不编造。

## 上下文分层

- [ ] Formal Knowledge Context：Current Release Map + Map-gated RAG + citations。
- [ ] Workbench Runtime Context：context_tables、row_index、current_pending、Draft Overlay。
- [ ] Conversation Context：chat_history 和当前用户请求。

## 输出物

- [ ] Workbench Suggest Context Builder 设计。
- [ ] SuggestChange v2 结构。
- [ ] evidence_refs 数据合同。
- [ ] Draft Overlay 输入说明。
- [ ] 后端硬校验规则。

## 验收标准

- [ ] Workbench Suggest 不再读取 KB 作为正式 evidence。
- [ ] Suggest 能读取 Current Map/RAG context。
- [ ] Suggest 能读取 row_index。
- [ ] Suggest 能读取 current_pending 作为 Draft Overlay。
- [ ] Suggest 返回 evidence_refs。
- [ ] SuggestChange 带 `source_release_id`。
- [ ] Draft Overlay 在数据合同中明确标记为非正式上下文。
- [ ] 后端 validator 拦截非法 table / field / row_id。

## 禁止范围

- [ ] 不把 Draft Overlay 写入 Formal Map、Release 或正式 RAG。
- [ ] 不把 KB 接回 Workbench Suggest 正式证据。
- [ ] 不绕过 Map-gated RAG 自行检索正式知识。
- [ ] 不在本任务做前端建议卡体验增强。
