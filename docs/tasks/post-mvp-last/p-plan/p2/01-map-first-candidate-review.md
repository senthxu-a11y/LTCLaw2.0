# P2-01 Map-first Candidate 与 Map Diff Review

来源：总规划书 Phase 4、18.10、3.4、3.5。

## 目标

让 Map 成为唯一知识结构编排层。Candidate Map 是建议态，Formal Map 是管理员确认后的正式结构，Release `map.json` 是 Formal Map 的快照。

## Checklist

- [ ] 定义 Formal Map 是正式项目知识结构。
- [ ] 定义 Candidate Map 是建议态，不是正式结构。
- [ ] 定义 Map Diff Review 流程。
- [ ] 定义 Map refs：system / table / doc / script / relationship。
- [ ] 定义 active / ignored / deprecated 状态语义。
- [ ] 确认 Formal Map 不存全文、不存完整表格、不存完整代码。
- [ ] 确认 Release 中 `map.json` 是 Formal Map 的快照。
- [ ] 明确 Candidate Map 的来源：Canonical Facts + Existing Formal Map + LLM 候选。
- [ ] 拆分 candidate-from-release 与 candidate-from-source 的语义。
- [ ] 保留现有 release-based candidate 兼容能力。
- [ ] 新增 source/canonical-based candidate 构建方向。
- [ ] 定义管理员保存 Formal Map 的流程。
- [ ] 定义 Formal Map 修改不会自动 Build Release。

## 输出物

- [ ] Map-first Contract。
- [ ] Map 数据模型边界说明。
- [ ] Candidate / Formal / Release Map 区分说明。
- [ ] Map Diff Review 大纲。

## 验收标准

- [ ] Candidate Map 不能被当作正式知识结构。
- [ ] Existing Formal Map 只能作为 hint，不能隐式覆盖 source/canonical 结果。
- [ ] source/canonical-based candidate 是管理员更新 Map 的主路径。
- [ ] Save Formal Map 和 Build Release 是两个显式动作。

## 禁止范围

- [ ] 不用一个 `/candidate` 同时承载加载、更新、重建三种语义。
- [ ] 不让 candidate-from-release 成为主要重建路径。
- [ ] 不把 Formal Map 做成全文、完整表数据或完整代码仓库。

