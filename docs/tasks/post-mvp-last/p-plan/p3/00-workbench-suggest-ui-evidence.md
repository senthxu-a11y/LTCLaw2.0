# P3-00 Workbench Suggest UI 与 Evidence 展示

来源：总规划书 P3、Phase 8、9.2-9.5；后端合同见 `../p0/07-workbench-suggest-context-builder.md`。

## 目标

在 P0 后端合同完成后，做前端建议卡、证据来源、Draft Overlay 标记和 citation 闭环展示。

## Checklist

- [ ] 消费 P0 已定义的 `evidence_refs`。
- [ ] 消费 P0 已定义的 `confidence`。
- [ ] 消费 P0 已定义的 `uses_draft_overlay`。
- [ ] 消费 P0 已定义的 `source_release_id`。
- [ ] 消费 P0 已定义的 `validation_status`。
- [ ] 前端建议卡展示证据来源。
- [ ] 前端明确区分正式知识与 Draft Overlay。
- [ ] 展示当前知识版本。
- [ ] citation 能回到对应工作台上下文。

## 输出物

- [ ] 建议卡 UI 信息结构。
- [ ] evidence_refs 展示规则。
- [ ] Draft Overlay 前端标记规则。

## 验收标准

- [ ] 建议卡能展示正式知识 evidence_refs。
- [ ] 建议卡能区分正式知识与 Draft Overlay。
- [ ] 当前知识版本可见。
- [ ] citation deep-link 不被破坏。

## 禁止范围

- [ ] 不把 KB 作为 Workbench Suggest 正式证据。
- [ ] 不让 Draft Overlay 进入正式 RAG。
- [ ] 不改 P0 后端合同。
