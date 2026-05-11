# Lane E.4 Real-Data Workbench Citation Smoke Receipt

Date: 2026-05-11

## 1. Final Status

- final_status: pass
- slice_result: E.4 final real-data Workbench citation smoke pass

## 2. Commit Hash

- commit_hash: 12d17fb7188bffc00fb2b1a7986f981c1a003137

## 3. App Port

- actual_app_port: 8093
- app_url: http://127.0.0.1:8093/game-project
- isolated_working_root: /private/tmp/ltclaw-real-data-smoke
- startup_note: a fresh 8093 launch attempt returned address already in use, so this smoke reused the existing isolated 8093 instance instead of rebuilding any precondition

## 4. Real Data Path

- requested_real_data_path: /Users/Admin/Documents/中小型游戏设计框架
- storage_api_local_project_directory: /Users/Admin/Documents/中小型游戏设计框架
- real_data_path_exists_on_disk: yes

## 5. Current Release Preconditions

- release_status_precheck_result: pass
- current_release_required_for_this_slice: yes
- current_release_rebuild_attempted: no
- current_release_bootstrap_attempted: no
- current_release_id: real-data-e4d-20260511-221645
- index_status_precheck_result: pass
- table_count: 18
- doc_count: 0
- doc_count_zero_note: expected because no approved doc_library entries were added

## 6. RAG Smoke Question

- rag_question_used: DaShenScore 表主要包含什么内容？请只根据引用片段回答。
- fallback_questions_not_needed:
  - Item 表主要包含什么内容？请只根据引用片段回答。
  - EquipEnhance 表主要包含什么内容？请只根据引用片段回答。
  - 商城系统里主要配置了什么内容？请只根据引用片段回答。

## 7. RAG Result

- rag_answer_endpoint: POST /api/agents/default/game/knowledge/rag/answer
- rag_http_status: 200
- rag_mode: answer
- rag_release_id: real-data-e4d-20260511-221645
- rag_citation_count: 2
- rag_warnings: []
- rag_answer_result: pass

## 8. Selected Citation / Workbench Target

- selected_citation_id: citation-001
- selected_citation_source_type: table_schema
- selected_citation_source_path: 配置表/DaShenScore.csv
- selected_citation_artifact_path: indexes/table_schema.jsonl
- selected_citation_title: DaShenScore
- selected_citation_row: 4
- selected_workbench_target_table: DaShenScore
- selected_workbench_target_available: yes

## 9. Clicked NumericWorkbench URL

- citation_open_in_workbench_clicked: yes
- clicked_numeric_workbench_url: http://127.0.0.1:8093/numeric-workbench?table=DaShenScore&from=rag-citation&citationId=citation-001&citationTitle=DaShenScore&citationSource=%E9%85%8D%E7%BD%AE%E8%A1%A8%2FDaShenScore.csv&row=4&session=wbs_mp1aoj79_uqlbmg&tableId=DaShenScore&rowId=4
- url_has_table_param: yes
- url_has_from_rag_citation: yes
- url_has_row_param: yes

## 10. Citation Context Hint Result

- citation_context_hint_result: pass
- citation_context_hint_title: Opened from a RAG citation
- citation_context_hint_table: DaShenScore
- citation_context_hint_row: 4
- citation_context_hint_citation_id: citation-001
- citation_context_hint_source_summary: Citation: DaShenScore (配置表/DaShenScore.csv)

## 11. Draft-Only / Dry-Run / No Automatic Publish Copy Result

- draft_only_copy_result: pass
- draft_only_copy_summary: Draft-only dry-run workspace. It does not publish automatically or write formal knowledge release.
- citation_boundary_copy_result: pass
- citation_boundary_copy_summary: Use this as inspection context only. Any changes remain draft-only dry-run work and do not publish automatically.

## 12. No Auto Draft Result

- no_auto_draft_result: pass
- ui_pending_save_count_after_open: 0
- save_action_clicked: no
- delete_action_clicked: no
- workbench_opened_as_inspection_context_only: yes

## 13. No Release / Formal Map / Test Plan / Workbench Draft Write Result

- no_release_write_result: pass
- no_formal_map_write_result: pass
- no_test_plan_write_result: pass
- no_workbench_draft_write_result: pass
- release_status_after_smoke: unchanged current release remains real-data-e4d-20260511-221645 with history_count=1
- formal_map_after_smoke: unchanged map_hash remains sha256:86c2b53ebbca7d1808ad0d341d190f293656976bac58b7c868333d002dd4d8e7
- proposals_dir_listing_after_smoke: empty
- pending_dir_exists_after_smoke: no
- workbench_dir_listing_after_smoke: tables/
- notes_on_write_boundary: This slice performed only read-side RAG and UI inspection. No build-release endpoint, no formal-map save endpoint, no test-plan export, no proposal generation, and no workbench save action were executed in this final smoke.

## 14. Exact Blocker

- exact_blocker: none

## 15. Notes

- This slice intentionally did not repeat index diagnosis or release bootstrap.
- If current release had been missing, the run would have stopped as blocked; that contingency was not triggered.
- No backend source, frontend source, API schema, provider or LLM selection was changed.
- No production rollout claim is made by this receipt.
- No production ready claim is made by this receipt.