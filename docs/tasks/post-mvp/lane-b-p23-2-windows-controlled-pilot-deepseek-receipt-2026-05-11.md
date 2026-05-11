# Lane B P23.2 Windows Controlled Pilot DeepSeek Receipt (2026-05-11)

## 1. Final Status

- final_status: pass
- production_rollout: no
- production_ready: no
- not production rollout: confirmed
- not production ready: confirmed

## 2. Environment And Baseline

- commit_hash: 05d72b4fdd11d45d210c48de14a4e4abdd462d04
- windows_version: Microsoft Windows NT 10.0.26200.0
- local_project_directory: E:\工作\资料\腾讯内部资料\中小型游戏设计框架
- current_release_id_before: win-op-r1-1778393517
- current_release_id_after: win-op-r1-1778393517
- provider_model: future_external / deepseek-chat
- env_var_name_used: LTCLAW_RAG_API_KEY
- qwenpaw_rag_api_key_used_for_provider_secret: no
- no_secret_written: confirmed

## 3. Step 1 Secret Injection Gate

- env_var_name: LTCLAW_RAG_API_KEY
- exists: true
- length_gt_20: true
- starts_with_sk: true
- header_starts_with_bearer_sk: true
- header_length_gt_env_length: true
- qwenpaw_env_present: false
- result: pass

## 4. Step 2 Startup And Baseline Checks

- startup_command: E:\LTclaw2.0\.venv\Scripts\ltclaw.exe app --host 127.0.0.1 --port 8092
- runtime_env_vars_in_server_process:
  - LTCLAW_RAG_API_KEY
  - QWENPAW_WORKING_DIR=C:\ltclaw-data-backed
  - QWENPAW_CONSOLE_STATIC_DIR=E:\LTclaw2.0\console\dist
- health_status: 200
- project_config_status: 200
- release_status_status: 200
- current_release_id_exists: true
- external_provider_config_before_run_is_null: true

## 5. No-Write Baseline Snapshot

- release_current_id: win-op-r1-1778393517
- release_history_count: 2
- release_list_count: 2
- release_ids:
  - win-op-r1-1778393517
  - win-op-r2-1778393517
- formal_map_summary:
  - mode: formal_map
  - map_hash: sha256:2367db1b2bdfa6cb534bac678321bca907f5579e64e5f66bcd8c2103402ba187
  - updated_at: 2026-05-10T06:11:28.248538Z
  - updated_by: windows-operator-validation-restore
  - table_count: 18
- test_plan_count: 1
- test_plan_ids:
  - win-plan-1778393619
- workbench_draft_count: 8
- workbench_draft_ids:
  - 65e2e3f0739b410aa6a22d27a2999268
  - e9d6f4ecdfb64a6f8637f352fd25c84d
  - d041786ed80340c9a0611202183001b8
  - 127eb530f119477b809ba7b5cdc74736
  - 9442edfd57984c0f9ccf3f5097059d8f
  - 2d23b586221a4f1281582544559eb307
  - 9d56259d534040bd89fcebbaf5b7f643
  - e778c722f0eb43b8ba46abd1334ab9fc
- project_config_external_provider_config: null
- app_health:
  - status: healthy
  - mode: daemon_thread
  - runner: ready

## 6. Backend-Owned DeepSeek Config Save And Readback

- put_status: 200
- external_provider_config_non_null: true
- model_name: deepseek-chat
- base_url: https://api.deepseek.com/chat/completions
- env.api_key_env_var: LTCLAW_RAG_API_KEY
- standalone_api_key_field_present: false
- qwenpaw_rag_api_key_present_in_readback: false
- real_key_value_present_in_readback: false
- result: pass

## 7. Controlled Scenarios

### Scenario 1

- scenario: Table purpose
- http_status: 200
- mode: answer
- citation_count: 1
- warnings: []
- result: pass

### Scenario 2

- scenario: Field meaning
- http_status: 200
- mode: answer
- citation_count: 1
- warnings: []
- result: pass

### Scenario 3

- scenario: Planner comparison
- http_status: 200
- mode: answer
- citation_count: 1
- warnings: []
- result: pass

### Scenario 4

- scenario: Workbench safety boundary
- http_status: 200
- mode: answer
- citation_count: 2
- warnings: []
- publish_or_save_claim_detected: false
- result: pass

### Scenario 5

- scenario: Unknown or insufficient context
- http_status: 200
- mode: insufficient_context
- citation_count: 0
- warnings:
  - External provider adapter skeleton returned an invalid response.
  - Model client output was not grounded in the provided context.
- fabricated_citation_detected: false
- result: pass

## 8. Request-Owned Field Ignore Result

- every_scenario_sent_negative_fields:
  - provider=request-provider
  - model=request-model
  - api_key=request-owned-negative-field
- request_owned_provider_model_api_key_ignored_result: pass
- secret_present_in_response: false
- raw_provider_error_present_in_response: false

## 9. No-Write After Snapshot

- release_current_id_after: win-op-r1-1778393517
- release_history_count_after: 2
- release_list_count_after: 2
- formal_map_after_hash: sha256:2367db1b2bdfa6cb534bac678321bca907f5579e64e5f66bcd8c2103402ba187
- test_plan_count_after: 1
- workbench_draft_count_after: 8
- release_no_write_result: pass
- formal_map_no_write_result: pass
- test_plans_no_write_result: pass
- workbench_drafts_no_write_result: pass

## 10. Kill Switch

- put_transport_enabled_false_status: 200
- readback_transport_enabled: false
- post_kill_switch_probe_http_status: 200
- post_kill_switch_probe_mode: insufficient_context
- post_kill_switch_probe_citation_count: 0
- post_kill_switch_probe_warnings:
  - External provider adapter skeleton transport is not connected.
  - Model client output was not grounded in the provided context.
- real_provider_success_answer_after_kill_switch: false
- kill_switch_result: pass

## 11. Cleanup

- put_external_provider_config_null_status: 200
- external_provider_config_null_before_restart: true
- removed_LTCLAW_RAG_API_KEY_from_restart_session: yes
- removed_QWENPAW_RAG_API_KEY_from_restart_session: yes
- restarted_ltclaw_without_secret: yes
- post_cleanup_health_status: 200
- post_cleanup_project_config_status: 200
- post_cleanup_external_provider_config_is_null: true
- post_cleanup_release_status_status: 200
- post_cleanup_current_release_id: win-op-r1-1778393517
- cleanup_result: pass

## 12. Boundary Confirmation

- not_production_rollout: confirmed
- not_production_ready: confirmed
- no_src_console_tests_edits: confirmed
- no_ask_schema_change: confirmed
- no_frontend_provider_ui_change: confirmed
- no active-model integration change: confirmed
- no simple router integration change: confirmed
- no_ordinary_rag_write_to_release_or_formal_knowledge: confirmed