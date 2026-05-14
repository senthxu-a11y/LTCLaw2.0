# P2-02 管理员 Map 构建体验

来源：总规划书 P2、5.2、Phase 11。

## 目标

在 P0/P1/P2-00/P2-01 主链路稳定后，补齐管理员构建 Map 的最小审阅体验：

- 管理员从 source/canonical 显式构建 Candidate Map review。
- 管理员能同时看清 Candidate Map、Formal Map、Release Map 的区别。
- 管理员能查看 diff review 的最小信息结构。
- 管理员显式点击后才保存 Formal Map。
- 保存 Formal Map 不自动 Build Release、不自动 Publish、不自动 set current。

本轮只做最小可验收切片，不进入 LLM lane。

## Checklist

- [x] 接入现有 source/canonical candidate backend。
- [x] 提供 Map Diff Review 最小展示。
- [x] 管理员可以查看新增 / 删除 / 变化 / 未变化 refs。
- [x] 管理员确认后才保存 Formal Map。
- [x] 保存 Formal Map 不自动 Build Release。
- [ ] 接入 LLM 字段归一化。
- [ ] 接入 LLM 关系候选。
- [ ] 接入 LLM 系统聚类。
- [ ] 提供 LLM Diff 解释。

## 输出物

- [x] 管理员 Map 构建流程说明。
- [x] Map Diff Review UI 信息结构。
- [x] Candidate / Formal / Release 区分文案。
- [x] 保存边界说明。
- [ ] LLM Diff 解释输入输出草案。

## 验收标准

- [x] 管理员能区分 Candidate Map、Formal Map、Release Map。
- [x] active / ignored / deprecated 状态在 review 中可见。
- [x] 保存 Formal Map 不自动 Build / Publish Release。
- [ ] LLM 解释只作为辅助，不自动发布知识底座。

## 本轮实现

### 入口位置

- 管理员 Review 入口位于 console Map Editor 页面。
- 项目页 Formal map workspace summary 保留跳转入口，提示管理员前往 Map Editor。
- Map Editor 中显式提供 `Build Candidate Review` 按钮，调用：
	- `POST /game/knowledge/map/candidate/from-source`

### Admin Review 信息结构

Map Editor 同时展示三块：

- Candidate Map
	- 来源：`source_canonical`
	- 字段：`candidate_source`、`is_formal_map`、`uses_existing_formal_map_as_hint`
	- warnings
	- diff_review：
		- `base_map_source`
		- `added_refs`
		- `removed_refs`
		- `changed_refs`
		- `unchanged_refs`
- Formal Map
	- 已保存正式结构
	- 允许 status-only review / save
- Release Map
	- 当前 release snapshot
	- 只读对照，不作为编辑源

### 保存边界

- Candidate Map 只是建议态，不是正式知识结构。
- 只有管理员显式点击 `Save Candidate as Formal Map` 时才调用 Formal Map save 接口。
- 保存 Formal Map 后：
	- 不自动 Build Release
	- 不自动 Publish Release
	- 不自动 set current release

### 未完成项

- 未接入 LLM 字段归一化。
- 未接入 LLM 关系候选。
- 未接入 LLM 系统聚类。
- 未接入 LLM Diff 解释。
- 未实现自动流转或自动确认。

## 禁止范围

- [x] 不在 P0 未完成前做体验优先开发。
- [x] 不让 LLM 自动确认 Formal Map。
- [x] 不自动 Save Formal Map。
- [x] 不自动 Build / Publish Release。
- [x] 不改 Release build/publish、RAG context、Workbench source write、Model Router。
- [x] 不新增 capability。
- [x] 不读取 KB、legacy retrieval、session draft、Workbench dirty state 作为 candidate 或 formal evidence。

