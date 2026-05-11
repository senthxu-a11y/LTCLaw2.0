# Lane E.4 Real-Data Workbench Citation Smoke Receipt

Date: 2026-05-11

## 1. Final Status

- final_status: pass
- slice_result: E.4d real-data release-map bootstrap pass

## 2. Commit Hash

- commit_hash: b2662162816441c1ec27a8b40584567bc9c3f5ea

## 3. App Port

- actual_app_port: 8093
- app_url: http://127.0.0.1:8093/game-project

## 4. Real Data Path

- requested_real_data_path: /Users/Admin/Documents/中小型游戏设计框架
- real_data_path_exists_on_disk: yes
- storage_api_local_project_directory: /Users/Admin/Documents/中小型游戏设计框架

## 5. Isolated Runtime

- isolated_working_root: /private/tmp/ltclaw-real-data-smoke
- existing_8092_instance_touched: no
- user_config_update_mode: controlled smoke precondition via PUT /api/agents/default/game/project/user_config
- user_config_update_result: pass

## 6. Project Config And Index Preconditions

- project_config_loaded: yes
- project_config_api_result: non-null
- project_config_actual_path: /private/tmp/ltclaw-real-data-smoke/game_data/projects/中小型游戏设计框架-e6db0735f447/project/config/project_config.yaml
- project_config_paths_effective:
  - 配置表/
  - .xlsx
- controlled_index_rebuild_attempted: yes
- controlled_index_rebuild_endpoint: POST /api/agents/default/game/index/rebuild
- controlled_index_rebuild_http_status: 200
- controlled_index_rebuild_result: pass
- controlled_index_rebuild_indexed_count: 18
- controlled_index_rebuild_scanned_file_count: 18
- game_index_status_result: {"configured":true,"table_count":18,"doc_count":0,"doc_chunk_count":0,"dependency_edge_count":0,"kb_entry_count":0,"code_file_count":0}
- table_count: 18
- doc_count: 0
- doc_count_zero_note: expected because no approved doc_library entries were added in this smoke slice

## 7. Code-Level Gate Confirmed Before Bootstrap

- build_from_current_indexes_effective_map_rule: build_knowledge_release_from_current_indexes first resolves a saved formal knowledge map, and only falls back to the current release map if no formal map exists
- controlling_code_paths:
  - src/ltclaw_gy_x/game/knowledge_release_service.py _resolve_effective_map_for_safe_build
  - src/ltclaw_gy_x/app/routers/game_knowledge_map.py PUT /game/knowledge/map
  - src/ltclaw_gy_x/app/routers/game_knowledge_release.py POST /game/knowledge/releases/build-from-current-indexes
  - src/ltclaw_gy_x/app/routers/game_knowledge_release.py POST /game/knowledge/releases/{release_id}/current

## 8. Formal Map Bootstrap

- formal_map_existed_before_e4d: no usable saved map was assumed for this slice
- formal_map_bootstrap_executed: yes
- formal_map_bootstrap_endpoint: PUT /api/agents/default/game/knowledge/map
- formal_map_bootstrap_result: pass
- formal_map_bootstrap_http_status: 200
- formal_map_updated_by: copilot-e4d-smoke
- formal_map_hash: sha256:86c2b53ebbca7d1808ad0d341d190f293656976bac58b7c868333d002dd4d8e7
- formal_map_payload_shape_summary:
  - top_level_fields: map, updated_by
  - map_fields: release_id, systems, tables, docs, scripts, relationships, deprecated, source_hash
  - systems_count: 0
  - docs_count: 0
  - scripts_count: 0
  - relationships_count: 0
  - deprecated_count: 0
  - table_refs_count: 18
  - per_table_ref_fields: table_id, title, source_path, source_hash, system_id=null, status=active
- formal_map_source_of_truth_for_refs: current table indexes only
- formal_map_business_explanations_added: no

## 9. Release Build

- current_release_existed_before_build: no
- controlled_release_build_executed: yes
- controlled_release_build_endpoint: POST /api/agents/default/game/knowledge/releases/build-from-current-indexes
- controlled_release_build_result: pass
- controlled_release_build_http_status: 200
- controlled_release_build_release_id: real-data-e4d-20260511-221645
- controlled_release_build_created_by: copilot-e4d-smoke
- controlled_release_build_release_dir: /private/tmp/ltclaw-real-data-smoke/game_data/projects/中小型游戏设计框架-e6db0735f447/project/releases/real-data-e4d-20260511-221645
- controlled_release_build_manifest_summary: {"table_schema_count":18,"doc_knowledge_count":0,"script_evidence_count":0,"candidate_evidence_count":0}

## 10. Current Release Pointer

- current_release_pointer_set: yes
- current_release_pointer_endpoint: POST /api/agents/default/game/knowledge/releases/real-data-e4d-20260511-221645/current
- current_release_pointer_result: pass
- current_release_pointer_http_status: 200
- current_release_id: real-data-e4d-20260511-221645
- release_status_after_pointer: {"current_present":true,"current_release_id":"real-data-e4d-20260511-221645","history_count":1}
- current_release_manifest_check: pass

## 11. Exact Blocker

- exact_blocker: none in this E.4d slice
- prior_blocker_cleared: the earlier HTTP 400 No current knowledge release is set was cleared after saving a minimal formal knowledge map and then building a release from current indexes

## 12. RAG / Workbench Scope

- rag_executed: no
- citation_smoke_executed: no
- numeric_workbench_smoke_executed: no
- reason_not_continued: this slice stopped after release-map bootstrap as requested and did not expand into final Workbench smoke pass

## 13. Controlled Smoke Write Boundary

- controlled_smoke_precondition_only: yes
- controlled_write_operations:
  - PUT /api/agents/default/game/project/user_config
  - POST /api/agents/default/game/index/rebuild
  - PUT /api/agents/default/game/knowledge/map
  - POST /api/agents/default/game/knowledge/releases/build-from-current-indexes
  - POST /api/agents/default/game/knowledge/releases/real-data-e4d-20260511-221645/current
- uncontrolled_product_write_operations: none
- automatic_publish_executed: no
- production_rollout_executed: no
- production_ready_claim_made: no

## 14. Notes

- No backend source, frontend source, API schema, provider configuration, LLM selection, or Ask schema was changed in this Lane E.4d step.
- No real table contents were written to this receipt; only counts, endpoint outcomes, release id, and payload shape summary are recorded.
- This receipt does not claim final Workbench smoke pass, ordinary RAG release writing, production rollout, or production readiness.