# Lane E.4 Real-Data Workbench Citation Smoke Receipt

Date: 2026-05-11

## 1. Final Status

- final_status: pass
- slice_result: E.4c real-data index path diagnosis pass

## 2. Commit Hash

- commit_hash: 15b20419d2f9dddc1027941d1d5be96aae3c0802

## 3. App Port

- actual_app_port: 8093
- app_url: http://127.0.0.1:8093/game-project

## 4. Real Data Path

- requested_real_data_path: /Users/Admin/Documents/中小型游戏设计框架
- real_data_path_exists_on_disk: yes

## 5. Project Config Fixture Setup

- project_config_yaml_added: yes
- project_config_yaml_existing_before_bootstrap: no
- project_config_yaml_actual_path: /private/tmp/ltclaw-real-data-smoke/game_data/projects/中小型游戏设计框架-e6db0735f447/project/config/project_config.yaml
- project_config_yaml_setup_mode: controlled smoke fixture setup via PUT /api/agents/default/game/project/config

## 6. Actual Local Project Directory

- storage_api_local_project_directory: /Users/Admin/Documents/中小型游戏设计框架
- page_visible_local_project_directory: /Users/Admin/Documents/中小型游戏设计框架

## 7. Project Config / Index / Release Precondition Steps

- current_release_existed_before_smoke: no
- existing_release_history_count: 0
- project_config_loaded: yes
- project_config_loaded_check_result: pass
- project_config_api_result: non-null
- project_config_validate_result: warning only
- project_config_validate_warnings_count: 1
- project_config_validate_redacted_summary: svn.root is not an SVN working copy warning only
- project_config_paths_before:
  - 配置表/**/*.csv
  - *.xlsx
- project_config_paths_after:
  - 配置表/
  - .xlsx
- controlled_index_rebuild_attempted: yes
- controlled_index_rebuild_endpoint: POST /api/agents/default/game/index/rebuild
- controlled_index_rebuild_result: pass
- controlled_index_rebuild_http_status: 200
- controlled_index_rebuild_indexed_count: 18
- controlled_index_rebuild_scanned_file_count: 18
- game_index_status_before_path_fix: {"configured":true,"table_count":0,"doc_count":0,"doc_chunk_count":0,"dependency_edge_count":0,"kb_entry_count":0,"code_file_count":0}
- game_index_status_after_rebuild_attempt: {"configured":true,"table_count":18,"doc_count":0,"doc_chunk_count":0,"dependency_edge_count":0,"kb_entry_count":0,"code_file_count":0}
- game_index_tables_before_path_fix: {"items":[],"total":0,"page":1,"size":200}
- game_index_tables_sample_after_rebuild_attempt: {"items_present":true,"total":18,"page":1,"size":200}
- controlled_release_build_happened: yes
- controlled_release_build_endpoint: POST /api/agents/default/game/knowledge/releases/build-from-current-indexes
- controlled_release_build_release_id: real-data-e4c-20260511-220307
- controlled_release_build_result: failed
- controlled_release_build_http_status: 400
- controlled_release_build_response: No current knowledge release is set
- current_release_after_attempt: none

## 8. Code-Level Diagnosis

- table_count_zero_root_cause: GameService.force_full_rescan scanned files by filters.include_ext, but GameService._handle_svn_change then filtered each relative path through GameService._path_passes_filter. That helper does plain string checks using p.startswith(rule.path) or rule.path in p instead of glob matching. The smoke fixture used glob-like patterns 配置表/**/*.csv and *.xlsx, so scanned files were accepted by include_ext but rejected before TableIndexer.index_batch, which left indexed_tables empty and table_count at 0.
- supporting_code_paths:
  - src/ltclaw_gy_x/game/service.py force_full_rescan
  - src/ltclaw_gy_x/game/service.py _path_passes_filter
  - src/ltclaw_gy_x/game/service.py _handle_svn_change
  - src/ltclaw_gy_x/game/retrieval.py get_retrieval_status
- doc_count_zero_note: doc_count remained 0 because retrieval.py only counts approved doc_library entries for doc/template semantics; this slice did not add doc rules or approved docs.

## 9. Smoke Questions

- planned_questions:
  - 商城系统里主要配置了什么内容？请只根据引用片段回答。
  - 属性规划里主要包含什么字段？请只根据引用片段回答。
  - 经济规划里有哪些配置项？请只根据引用片段回答。
  - 随机掉落表描述了什么？请只根据引用片段回答。
  - DaShenScore 表主要包含什么内容？请只根据引用片段回答。
  - Item 表主要包含什么内容？请只根据引用片段回答。
- executed_smoke_question: no RAG executed in E.4c by request

## 10. RAG Mode / Citation Count / Warnings

- rag_response_mode: not executed in this E.4c diagnosis slice
- citation_count: not executed in this E.4c diagnosis slice
- warnings: not executed in this E.4c diagnosis slice

## 11. Selected Citation / Workbench Target

- selected_citation_source_path: not executed because no citation was returned
- selected_citation_row: not executed because no citation was returned
- selected_workbench_target_table: not executed because no citation was returned

## 12. Clicked NumericWorkbench URL

- numeric_workbench_url: not executed because citation-to-workbench smoke could not start

## 13. Citation Context Hint Result

- citation_context_hint_result: not executed because citation-to-workbench smoke could not start

## 14. Draft-Only / Dry-Run / No Automatic Publish Copy

- boundary_copy_result: not executed because NumericWorkbench smoke could not start

## 15. No Auto Draft Result

- auto_create_draft_result: not executed because NumericWorkbench smoke could not start

## 16. No Publish / No Formal Knowledge Write Result

- no_publish_result: pass
- no_formal_knowledge_write_result: pass
- notes_on_write_boundary: During this diagnosis run, no current release pointer was set, no formal map was saved, no test plan was written, and no workbench draft was created. The only controlled write operations were the smoke fixture project config setup, the controlled index rebuild, and the attempted controlled precondition release build, which failed and did not create a usable current release.

## 17. Supporting Observations

- game_project_page_open_result: pass
- real_data_file_names_checked:
  - 商城系统.xlsx
  - 属性规划.xlsx
  - 经济规划.xlsx
  - 随机掉落.xlsx
  - 配置表/DaShenScore.csv
  - 配置表/EquipEnhance.csv
  - 配置表/Item.csv
  - 配置表/Stage.csv
- game_index_status_result: {"configured":true,"table_count":18,"doc_count":0,"doc_chunk_count":0,"dependency_edge_count":0,"kb_entry_count":0,"code_file_count":0}
- game_index_tables_sample_result: {"items_present":true,"total":18,"page":1,"size":200}
- release_status_result: {"current":null,"previous":null,"history":[]}
- page_current_release_banner: not rechecked in E.4c diagnosis slice
- page_candidate_map_state: not rechecked in E.4c diagnosis slice

## 18. Exact Blocker

- exact_blocker: The index path diagnosis itself passed after the smoke fixture path rules were changed to values that match GameService._path_passes_filter, and rebuild now produces table_count=18. The remaining blocker moved downstream to controlled release build: build_knowledge_release_from_current_indexes resolves its effective map from either a saved formal knowledge map or an existing current release map, and with neither present it still fails with HTTP 400 "No current knowledge release is set". This E.4c slice did not expand into formal map authoring, so current release was not established.

## 19. Notes

- This run used an isolated working root: /private/tmp/ltclaw-real-data-smoke.
- The existing 8092 instance was left untouched.
- The default agent user_config was updated in the isolated working root to point at the requested real data path.
- The controlled project config fixture was written to the isolated project store path, not into the source repository.
- No RAG execution was performed in this E.4c diagnosis slice.
- No usable controlled release build was completed in this continuation run.
- No backend source, frontend source, API schema, provider schema, or Ask schema was changed in this Lane E.4 step.
- No production rollout or production ready claim is made by this receipt.