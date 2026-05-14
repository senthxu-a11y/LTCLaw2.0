# P3-00 Workbench Suggest UI 与 Evidence 展示

来源：总规划书 P3、Phase 8、9.2-9.5；后端合同见 `../p0/07-workbench-suggest-context-builder.md`。

## 目标

在 P0 后端合同完成后，做前端建议卡、证据来源、Draft Overlay 标记和 citation 闭环展示。

本轮只做前端消费与展示，不改 P0 后端合同。

## Checklist

- [x] 消费 P0 已定义的 `evidence_refs`。
- [x] 消费 P0 已定义的 `confidence`。
- [x] 消费 P0 已定义的 `uses_draft_overlay`。
- [x] 消费 P0 已定义的 `source_release_id`。
- [x] 消费 P0 已定义的 `validation_status`。
- [x] 消费当前响应已有的 `formal_context_status`。
- [x] 前端建议卡展示证据来源。
- [x] 前端明确区分正式知识与 Draft Overlay。
- [x] 展示当前知识版本。
- [x] citation 能回到对应工作台上下文。

## 输出物

- [x] 建议卡 UI 信息结构。
- [x] evidence_refs 展示规则。
- [x] Draft Overlay 前端标记规则。

## 验收标准

- [x] 建议卡能展示正式知识 evidence_refs。
- [x] 建议卡能区分正式知识与 Draft Overlay。
- [x] 当前知识版本可见。
- [x] citation deep-link 不被破坏。

## 本轮实现

### 建议卡 UI 信息结构

Workbench Suggest 建议卡现在展示两层信息：

- response / message 级：
	- `formal_context_status`
	- 聚合后的 `evidence_refs`
	- 当前知识版本 `source_release_id`
	- 是否存在 `uses_draft_overlay`
	- 是否存在 runtime-only suggestion
- suggestion 级：
	- `table`
	- `row_id`
	- `field`
	- `new_value`
	- `reason`
	- `confidence`
	- `validation_status`
	- `source_release_id`
	- `uses_draft_overlay`
	- `evidence_refs`

### evidence_refs 展示规则

- `evidence_refs` 只按后端已返回字段展示，不做额外后端推断。
- 前端对 `evidence_refs` 做去重并保序展示。
- 有 `evidence_refs` 的 suggestion 标记为 Formal evidence。
- 没有 `evidence_refs` 的 suggestion 不能伪装成 Formal evidence。
- response 级 evidence 采用 suggestion 内 refs 与响应顶层 refs 的并集去重展示。

### Draft Overlay 标记规则

- `uses_draft_overlay = true` 只显示为辅助标记。
- 如果同时存在 `evidence_refs`：
	- 仍显示为 Formal evidence
	- 同时显示 Draft Overlay assist only
- 如果不存在 `evidence_refs` 且 `uses_draft_overlay = true`：
	- 显示为 runtime-only suggestion
	- 不能升级为 Formal evidence

### Formal / Draft / Runtime-only 区分

- Formal evidence：来自 Current Release + Map-gated context，前端以非空 `evidence_refs` 呈现。
- Draft Overlay：只作为建议辅助，前端只显示标记，不把它当正式证据。
- Runtime-only suggestion：没有正式 `evidence_refs` 的建议，即使使用了 Draft Overlay，也仍是 runtime-only。

### citation / 定位闭环

- 本轮未改 Workbench 既有 `table` / `row` / `field` 定位逻辑。
- 建议卡仍沿用既有 `定位` 按钮与 `onJumpToCell(...)` 行为。
- RAG citation deep-link 到 Workbench 的 query 参数与定位行为保持不变。

## 禁止范围

- [x] 不把 KB 作为 Workbench Suggest 正式证据。
- [x] 不让 Draft Overlay 进入正式 RAG。
- [x] 不改 P0 后端合同。
