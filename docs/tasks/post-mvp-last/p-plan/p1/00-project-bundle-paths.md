# P1-00 Project Bundle 与路径收口

来源：总规划书 Phase 1、4.1、4.2、20 技术雷区 12。

## 目标

P1-00 只定义 project bundle 的路径规范入口，并把现有 paths helper 收口成后续任务可复用的约定。

本轮边界如下：

- 不改 Release、RAG、Workbench、Model Router、capability 语义。
- 不做自动迁移、不删除、不移动用户旧数据。
- 不把 P1-01、P1-02 的后续业务迁移写成已完成。

## 已完成收口

当前已在 `src/ltclaw_gy_x/game/paths.py` 中补齐 project key、project bundle root、project-level artifact、agent/session/audit/admin 的规范 helper，并保持既有公开接口兼容。

本轮“完成”的含义仅限于：

- 路径规范已定义。
- helper 已可定位 project-level 正式产物路径。
- storage summary 已能暴露 project bundle、legacy index、agent/session/runtime 等关键路径。

本轮“不包含”的事项：

- 不把 Release artifacts 迁到新 helper 的业务写入链路。
- 不把 RAG context、Map Router、Workbench source write 改成新路径写入。
- 不处理 overlap governance、正式迁移脚本或管理员 UI。

## Project Key 规则

- canonical project root：`Path(project_root).expanduser().resolve(strict=False)`
- key 生成：`safe basename + '-' + sha256(canonical path)[:12]`
- safe basename 使用现有安全化规则，只保留字母、数字、`-`、`_`，其余字符替换为 `-`
- 该规则与既有 project store 命名保持一致，因此不会破坏旧 project store 定位稳定性

对应 helper：`get_project_key(project_root)`

## Project Bundle Root 解析规则

- 优先读取 `LTCLAW_GAME_PROJECTS_DIR`
- 未设置时 fallback 到 `working_root/game_data/projects`
- bundle root 形式：`<projects-root>/<project-key>`

对应 helper：`get_project_bundle_root(project_root)`

## 当前兼容层

总规划推荐的长期 project bundle 形态是直接在 `bundle_root` 下放置 `project.json`、`source_config.yaml`、`sources/`、`indexes/`、`maps/`、`releases/`、`rag/`、`runtime/` 等项目级正式产物。

当前实现为了兼容 P0 已验收链路，project-level artifacts 仍落在兼容层 `get_project_bundle_project_dir(project_root)`，即：

- `bundle_root/project`

因此当前 helper 的 project-level 目标路径是“规范命名 + 兼容落点”，不是“已经完成迁移”。后续若要把 project-level artifacts 从 `bundle_root/project` 迁到 `bundle_root`，必须在明确 slice 中显式处理，不能静默移动旧数据。

## 路径 Helper 映射表

### Project Metadata

- `get_project_manifest_path` -> `bundle_root/project/project.json`
- `get_project_source_config_path` -> `bundle_root/project/source_config.yaml`

### Sources

- `get_project_sources_dir` -> `bundle_root/project/sources/`
- `get_project_docs_source_path` -> `bundle_root/project/sources/docs.yaml`
- `get_project_tables_source_path` -> `bundle_root/project/sources/tables.yaml`
- `get_project_scripts_source_path` -> `bundle_root/project/sources/scripts.yaml`

### Indexes

- `get_project_indexes_dir` -> `bundle_root/project/indexes/`
- `get_project_raw_indexes_dir` -> `bundle_root/project/indexes/raw/`
- `get_project_raw_docs_dir` -> `bundle_root/project/indexes/raw/docs/`
- `get_project_raw_tables_dir` -> `bundle_root/project/indexes/raw/tables/`
- `get_project_raw_scripts_dir` -> `bundle_root/project/indexes/raw/scripts/`
- `get_project_canonical_indexes_dir` -> `bundle_root/project/indexes/canonical/`
- `get_project_canonical_docs_dir` -> `bundle_root/project/indexes/canonical/docs/`
- `get_project_canonical_tables_dir` -> `bundle_root/project/indexes/canonical/tables/`
- `get_project_canonical_scripts_dir` -> `bundle_root/project/indexes/canonical/scripts/`

### Maps

- `get_project_maps_dir` -> `bundle_root/project/maps/`
- `get_project_candidate_maps_dir` -> `bundle_root/project/maps/candidate/`
- `get_project_candidate_map_path` -> `bundle_root/project/maps/candidate/latest.json`
- `get_project_candidate_map_history_dir` -> `bundle_root/project/maps/candidate/history/`
- `get_project_formal_maps_dir` -> `bundle_root/project/maps/formal/`
- `get_project_formal_map_canonical_path` -> `bundle_root/project/maps/formal/formal_map.json`
- `get_project_formal_map_history_path` -> `bundle_root/project/maps/formal/formal_map.history.jsonl`
- `get_project_map_diffs_dir` -> `bundle_root/project/maps/diffs/`
- `get_project_latest_map_diff_path` -> `bundle_root/project/maps/diffs/latest_diff.json`

### Releases

- `get_project_releases_dir` -> `bundle_root/project/releases/`
- `get_project_current_release_path` -> `bundle_root/project/releases/current.json`
- `get_project_release_dir` -> `bundle_root/project/releases/<release-id>/`
- 兼容公开接口仍保留：`get_knowledge_releases_dir`、`get_current_release_path`、`get_release_dir`

### RAG

- `get_project_rag_dir` -> `bundle_root/project/rag/`
- `get_project_current_rag_dir` -> `bundle_root/project/rag/current/`
- `get_project_rag_context_index_path` -> `bundle_root/project/rag/current/context_index.jsonl`
- `get_project_rag_citation_index_path` -> `bundle_root/project/rag/current/citation_index.jsonl`
- `get_project_rag_map_route_cache_path` -> `bundle_root/project/rag/current/map_route_cache.jsonl`
- `get_project_rag_vector_dir` -> `bundle_root/project/rag/vector/`
- `get_project_rag_keyword_dir` -> `bundle_root/project/rag/keyword/`
- `get_project_rag_status_path` -> `bundle_root/project/rag/status.json`

### Runtime

- `get_project_runtime_dir` -> `bundle_root/project/runtime/`
- `get_project_runtime_llm_cache_dir` -> `bundle_root/project/runtime/llm_cache/`
- `get_project_runtime_build_jobs_dir` -> `bundle_root/project/runtime/build_jobs/`
- `get_project_runtime_temp_dir` -> `bundle_root/project/runtime/temp/`
- `get_project_runtime_logs_dir` -> `bundle_root/project/runtime/logs/`

### Agents / Session / Audit

- `get_agent_store_dir` -> `bundle_root/agents/<agent-id>/`
- `get_agent_profile_path` -> `bundle_root/agents/<agent-id>/profile.yaml`
- `get_agent_audit_dir` -> `bundle_root/agents/<agent-id>/audit/`
- `get_agent_workbench_writeback_audit_path` -> `bundle_root/agents/<agent-id>/audit/workbench_writeback.jsonl`
- `get_session_store_dir` / `get_agent_session_dir` -> `bundle_root/agents/<agent-id>/sessions/<session-id>/`
- `get_agent_session_workbench_dir` / `get_workspace_game_dir` -> `bundle_root/agents/<agent-id>/sessions/<session-id>/workbench`
- `get_agent_session_proposals_dir` -> `bundle_root/agents/<agent-id>/sessions/<session-id>/proposals`
- `get_agent_session_ui_state_path` -> `bundle_root/agents/<agent-id>/sessions/<session-id>/ui_state.json`

### Admin Placeholder

- `get_project_admin_dir` -> `bundle_root/admin/`

当前 `admin/` 仅为占位路径 helper，不代表 MCP 工具池或管理员页面已实现。

## Legacy 兼容策略

- `get_legacy_index_dir(project_root)` 保留为 `project_root/.ltclaw_index`
- `get_project_store_dir`、`get_project_data_dir`、`get_index_dir`、`get_tables_dir`、`get_docs_dir`、`get_workspace_game_dir`、`get_agent_store_dir`、`get_session_store_dir`、`get_storage_summary` 等旧接口继续保留
- 旧路径在本轮仅用于兼容读取或给出迁移提示
- 本轮不自动删除旧目录，不自动移动旧数据，不静默重写 legacy 布局

## 迁移策略

- P1-00 只定义规范和 helper，不做业务迁移
- 后续新写入应逐步接入 project bundle helper，但必须由明确 slice 分批实施
- 旧路径迁移留给后续显式任务，必须可审计、可回退、可人工确认
- 管理员路径摘要依赖 `get_storage_summary` 暴露 `project_key`、`project_bundle_root`、`legacy_index_dir`、`project_runtime_dir`、`project_admin_dir`、agent/session 关键路径

## 当前验收状态

- 已完成：project key 规则、project bundle root 规则、兼容层说明、project-level helper、agent/session/audit/admin helper、legacy helper 保留、storage summary 关键路径暴露
- 已完成：文档明确记录 `bundle_root/project` 是当前兼容层，而非最终迁移完成态
- 未完成：Release artifacts 的业务写入迁移
- 未完成：RAG context 与 Map Router 的业务接线迁移
- 未完成：Workbench source write 正式收口迁移
- 未完成：管理员 UI、迁移脚本、P1-01、P1-02 范围内事项

## 禁止范围

- 不直接把现有 `paths.py` 全量替换成新布局
- 不自动迁移用户数据而不保留回退方案
- 不把 project-level 正式产物与 agent/session 私有状态混用
- 不在 P1-00 中改变业务逻辑，只做路径规范 slice

