# P2-01 Map-first Candidate 与 Map Diff Review

来源：总规划书 Phase 4、18.10、3.4、3.5。

## 目标

P2-01 明确 Candidate Map、Formal Map、Release `map.json` 的分层关系，并补齐 source/canonical-based candidate 的最小后端合同与 diff review 纯函数。

本轮边界如下：

- Candidate Map 只能是建议态，不是正式知识结构。
- Formal Map 仍是唯一正式项目知识结构。
- Release `map.json` 仍只是 Formal Map 的发布快照。
- 不自动 Save Formal Map。
- 不自动 Build Release。
- 不做管理员完整 UI。
- 不做 LLM 候选。

## Map-first Contract

### Formal Map

- 唯一正式项目知识结构。
- 由管理员显式保存。
- 可被后续 Release build 读取，但 Save Formal Map 与 Build Release 仍是两个显式动作。
- 不存全文、不存完整表格、不存完整代码。

### Candidate Map

- 仅是建议态，用于 review，不是正式结构。
- 必须返回 `is_formal_map = false`。
- 来源标记：
	- `candidate_source = release_snapshot`
	- `candidate_source = source_canonical`
- 可带：
	- `source_release_id`
	- `uses_existing_formal_map_as_hint`
	- `warnings`

### Release `map.json`

- 是 Formal Map 的 release snapshot。
- 不代表 Candidate Map 已被确认。
- 仍用于已发布版本的只读消费，不承担管理员编辑语义。

## Candidate 来源拆分

### candidate-from-release

- 保留现有 `GET /game/knowledge/map/candidate` 兼容入口。
- 响应中明确标记：
	- `candidate_source = release_snapshot`
	- `is_formal_map = false`
	- `source_release_id = <release-id>`
- 该路径只用于 review current release snapshot 的兼容能力。
- 它不是管理员更新 Map 的主重建路径。

### candidate-from-source

- 新增明确入口 `POST /game/knowledge/map/candidate/from-source`。
- 输入只允许来自 P2-00 canonical facts：
	- canonical table schemas
	- canonical doc facts
	- canonical script facts
- 不读取 Release artifacts 作为 candidate 主输入。
- 不读取 KB / retrieval / session draft / workbench dirty state。
- 若 canonical facts 缺失，返回 `mode = no_canonical_facts` 或空 candidate，不回退到 release snapshot。

## Existing Formal Map 作为 Hint

- Existing Formal Map 只能作为 hint。
- 当前最小实现允许：
	- 复用已有 `system_id`
	- 复用已有 `title`
	- 复用已有 `status`
	- 在 refs 仍存在时 carry over 现有 relationships 作为 review hint
- Existing Formal Map 不能隐式带回 source/canonical 中不存在的 refs。
- 若 formal-map 中的旧 refs 在 canonical candidate 中不存在，只能跳过并发出 warning，不能静默保留。

## Map Diff Review 合同

Map Diff Review 是 review 辅助结构，不写文件、不保存 Formal Map、不触发 Release。

输出 shape：

- `base_map_source`: `formal_map` / `current_release` / `none`
- `candidate_source`: `release_snapshot` / `source_canonical`
- `added_refs`
- `removed_refs`
- `changed_refs`
- `unchanged_refs`
- `warnings`

diff 仅比较 refs 与轻量 metadata，不读取全文、不读取完整表格、不读取完整代码。

Map refs 类型：

- `system:<id>`
- `table:<id>`
- `doc:<id>`
- `script:<id>`
- `relationship:<id>`

## 状态语义

- `active`：正式可用
- `ignored`：管理员明确忽略，不进入正式 evidence
- `deprecated`：历史保留但不作为新证据入口

## 路由与 Capability

- `GET /game/knowledge/map/candidate`
	- 语义：candidate-from-release
	- capability：`knowledge.candidate.read`
- `POST /game/knowledge/map/candidate/from-source`
	- 语义：build source/canonical candidate for review
	- capability：`knowledge.candidate.write`
- Formal Map 读写接口保留：
	- read：`knowledge.map.read`
	- save：`knowledge.map.edit`

本轮不新增 capability，也不改变其权限语义。

## 当前完成状态

- 已完成：release-based candidate 明确标记为 `release_snapshot`。
- 已完成：source/canonical-based candidate 的最小后端合同与 builder。
- 已完成：Existing Formal Map 仅作为 hint。
- 已完成：Map Diff Review 纯函数与输出 shape。
- 未完成：管理员完整 UI。
- 未完成：LLM 关系候选。
- 未完成：自动 Save Formal Map 或自动 Build Release。

## 禁止范围

- 不用一个 `/candidate` 同时承载加载、更新、重建三种语义。
- 不让 candidate-from-release 成为主要重建路径。
- 不把 Candidate Map 写入 Formal Map store。
- 不让 diff review 读取全文、完整表格或完整代码。
- 不把 Formal Map 做成全文、完整表数据或完整代码仓库。

