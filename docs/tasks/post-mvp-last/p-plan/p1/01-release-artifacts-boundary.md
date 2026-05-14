# P1-01 Release 与 Release Artifacts 收口

来源：总规划书 Phase 7、3.6、3.7、19.3.6。

## 目标

P1-01 把 Release 收口为 Formal Map 与 project-owned current indexes 的快照，并把 Release Artifacts 固定为正式证据仓库。

本轮边界如下：

- 不改 RAG context、Map Router、Workbench source write、Model Router、capability。
- 不进入 P1-02 overlap 治理。
- 不做 P2 canonical facts / canonical schema 建设。
- 不迁移旧 release 目录。

## Release 输入边界

Release 的正式输入只允许来自以下 project-owned 数据：

- saved Formal Map snapshot
- current table indexes
- current code/script indexes
- Formal Map doc refs 派生的 doc snapshot
- 显式选择且 accepted、selected for build 的 release candidates

当前实现中，build-from-current-indexes 的服务端读取路径只包含：

- `load_formal_knowledge_map(project_root)`
- `get_current_release_map(project_root)`，仅在显式 bootstrap 模式下作为临时 map 回退
- `get_table_indexes_path(project_root)`
- `get_code_index_dir(workspace_dir, project_root)`
- `list_release_candidates(project_root)`，且仅在显式传入 `candidate_ids` 时选择 accepted + selected candidate

明确禁止作为 Release 输入的来源：

- legacy KB
- legacy retrieval
- session/private approved docs
- Draft Overlay
- 普通 Proposal
- workbench dirty state

## Strict / Bootstrap 行为

### Strict Mode

- 默认模式
- 必须存在 saved Formal Map
- 若不存在 Formal Map，build fail-closed，错误为 `Strict release build requires a saved formal knowledge map`
- strict release 的 manifest 记录：
	- `build_mode = strict`
	- `status = ready`
	- `map_source = formal_map` 或 direct build 的 `provided`
	- `warnings = []`

### Bootstrap Mode

- 只能通过 build-from-current-indexes 的显式参数 `bootstrap = true` 启用
- 若存在 Formal Map，则仍优先使用 Formal Map，不降级为 bootstrap snapshot
- 若不存在 Formal Map，允许以下回退：
	- 优先使用 current release 的 `map.json` 作为临时 snapshot
	- 若 current release 也不存在，则从 current table indexes + current code indexes 生成临时 map
- bootstrap build 必须返回可见 warning，并写入 manifest metadata：
	- `build_mode = bootstrap`
	- `status = bootstrap_warning`
	- `map_source = current_release` 或 `bootstrap_current_indexes`
	- `warnings` 明确声明“这不是管理员审定的 Formal Map”

## Release Artifacts Contract

Release artifacts 的相对路径固定为：

- `manifest.json`
- `map.json`
- `indexes/table_schema.jsonl`
- `indexes/doc_knowledge.jsonl`
- `indexes/script_evidence.jsonl`
- `indexes/candidate_evidence.jsonl`

contract 说明：

- `manifest.json` 记录 `release_id`、`created_by`、`created_at`、`project_root_hash`、`source_snapshot_hash`、`map_hash`
- `manifest.json` 记录 `build_mode`、`status`、`map_source`、`warnings`
- `manifest.json.indexes` 对四类 artifact 全部保留稳定键位，并记录每项 `path`、`hash`、`count`
- `map.json` 必须是本次 release snapshot，且 `release_id` 与 manifest 一致
- `candidate_evidence.jsonl` 只允许写入显式选择且 accepted + selected_for_build 的 candidates
- 若没有 candidate payload，可不落盘 `candidate_evidence.jsonl`，但 manifest 中 `candidate_evidence` 条目仍必须存在，且语义稳定为 `count = 0`

## Build / Publish / Rollback 边界

- Build Release 默认不自动 set current，不自动 publish
- `set_current_release` 只切换 current pointer，不 rebuild、不改 artifacts
- Set current / rollback 必须通过显式 publish action 触发，沿用 `knowledge.publish` gate
- RAG current 与 current release pointer 的读取关系保持不变；本任务不改 RAG context 行为

## 当前实现状态

- 已完成：strict mode fail-closed
- 已完成：bootstrap 必须显式启用，且 warning/status 对外可见
- 已完成：Release artifacts contract 固定为四类 indexes + candidate evidence
- 已完成：Build 不自动 publish / 不自动 set current
- 已完成：`bundle_root/project` 兼容层继续保留，不移动 release 根目录
- 未完成：P2 canonical docs / canonical schema 的正式建设
- 未完成：P1-02 overlap 治理

## 禁止范围

- 不让 Release 读取 KB / retrieval / Draft Overlay / 普通 Proposal
- 不把 candidate-from-release 提升为 Formal Map 重建主路径
- 不改变 RAG context 的 map-gated 逻辑
- 不迁移旧 release 目录

