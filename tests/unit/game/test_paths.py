import hashlib
from pathlib import Path

from ltclaw_gy_x.game.paths import (
    get_agent_profile_path,
    get_agent_session_proposals_dir,
    get_agent_session_ui_state_path,
    get_agent_store_dir,
    get_agent_workbench_writeback_audit_path,
    get_current_release_path,
    get_knowledge_releases_dir,
    get_legacy_index_dir,
    get_project_admin_dir,
    get_project_bundle_project_dir,
    get_project_bundle_root,
    get_project_candidate_map_history_dir,
    get_project_candidate_map_path,
    get_project_canonical_doc_facts_path,
    get_project_canonical_docs_dir,
    get_project_canonical_script_facts_path,
    get_project_canonical_scripts_dir,
    get_project_canonical_table_schema_path,
    get_project_canonical_tables_dir,
    get_project_current_release_path,
    get_project_docs_source_path,
    get_project_formal_map_canonical_path,
    get_project_formal_map_history_path,
    get_project_key,
    get_project_latest_map_diff_path,
    get_project_manifest_path,
    get_project_rag_citation_index_path,
    get_project_rag_context_index_path,
    get_project_rag_keyword_dir,
    get_project_rag_map_route_cache_path,
    get_project_rag_status_path,
    get_project_rag_vector_dir,
    get_project_release_dir,
    get_project_runtime_build_jobs_dir,
    get_project_runtime_llm_cache_dir,
    get_project_runtime_logs_dir,
    get_project_runtime_temp_dir,
    get_project_scripts_source_path,
    get_project_source_config_path,
    get_project_store_dir,
    get_project_tables_source_path,
    get_storage_summary,
    get_workspace_game_dir,
)


def test_project_key_is_stable_for_canonical_project_root(tmp_path):
    project_root = tmp_path / "projects" / "demo project"
    project_root.mkdir(parents=True)
    alias_root = project_root.parent / "demo project" / ".." / "demo project"

    canonical = str(project_root.resolve(strict=False))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]

    assert get_project_key(project_root) == f"demo-project-{digest}"
    assert get_project_key(alias_root) == get_project_key(project_root)
    assert get_project_store_dir(alias_root) == get_project_store_dir(project_root)


def test_project_bundle_root_uses_projects_dir_override(monkeypatch, tmp_path):
    project_root = tmp_path / "svn-root"
    project_root.mkdir()
    custom_projects_dir = tmp_path / "bundle-root"
    monkeypatch.setenv("LTCLAW_GAME_PROJECTS_DIR", str(custom_projects_dir))

    bundle_root = get_project_bundle_root(project_root)

    assert bundle_root == custom_projects_dir / get_project_key(project_root)
    assert get_project_bundle_project_dir(project_root) == bundle_root / "project"


def test_project_bundle_root_falls_back_to_working_game_data(monkeypatch, tmp_path):
    project_root = tmp_path / "svn-root"
    project_root.mkdir()
    working_root = tmp_path / "working-root"
    monkeypatch.setenv("LTCLAW_WORKING_DIR", str(working_root))

    assert get_project_bundle_root(project_root) == (
        working_root / "game_data" / "projects" / get_project_key(project_root)
    )


def test_project_level_helpers_map_to_project_bundle_paths(monkeypatch, tmp_path):
    working_root = tmp_path / "working-root"
    project_root = tmp_path / "svn-root"
    monkeypatch.setenv("LTCLAW_WORKING_DIR", str(working_root))
    project_root.mkdir()

    project_dir = get_project_bundle_project_dir(project_root)

    assert get_project_manifest_path(project_root) == project_dir / "project.json"
    assert get_project_source_config_path(project_root) == project_dir / "source_config.yaml"
    assert get_project_docs_source_path(project_root) == project_dir / "sources" / "docs.yaml"
    assert get_project_tables_source_path(project_root) == project_dir / "sources" / "tables.yaml"
    assert get_project_scripts_source_path(project_root) == project_dir / "sources" / "scripts.yaml"
    assert get_project_candidate_map_path(project_root) == project_dir / "maps" / "candidate" / "latest.json"
    assert get_project_candidate_map_history_dir(project_root) == project_dir / "maps" / "candidate" / "history"
    assert get_project_formal_map_canonical_path(project_root) == project_dir / "maps" / "formal" / "formal_map.json"
    assert get_project_formal_map_history_path(project_root) == (
        project_dir / "maps" / "formal" / "formal_map.history.jsonl"
    )
    assert get_project_latest_map_diff_path(project_root) == project_dir / "maps" / "diffs" / "latest_diff.json"
    assert get_knowledge_releases_dir(project_root) == project_dir / "releases"
    assert get_current_release_path(project_root) == project_dir / "releases" / "current.json"
    assert get_project_current_release_path(project_root) == get_current_release_path(project_root)
    assert get_project_release_dir(project_root, "release 001") == project_dir / "releases" / "release-001"
    assert get_project_rag_context_index_path(project_root) == project_dir / "rag" / "current" / "context_index.jsonl"
    assert get_project_rag_citation_index_path(project_root) == project_dir / "rag" / "current" / "citation_index.jsonl"
    assert get_project_rag_map_route_cache_path(project_root) == project_dir / "rag" / "current" / "map_route_cache.jsonl"
    assert get_project_canonical_tables_dir(project_root) == project_dir / "indexes" / "canonical" / "tables"
    assert get_project_canonical_docs_dir(project_root) == project_dir / "indexes" / "canonical" / "docs"
    assert get_project_canonical_scripts_dir(project_root) == project_dir / "indexes" / "canonical" / "scripts"
    assert get_project_canonical_table_schema_path(project_root, "Hero Table") == (
        project_dir / "indexes" / "canonical" / "tables" / "Hero-Table.json"
    )
    assert get_project_canonical_doc_facts_path(project_root, "combat doc") == (
        project_dir / "indexes" / "canonical" / "docs" / "combat-doc.json"
    )
    assert get_project_canonical_script_facts_path(project_root, "Combat/Resolver") == (
        project_dir / "indexes" / "canonical" / "scripts" / "Combat-Resolver.json"
    )
    assert get_project_rag_vector_dir(project_root) == project_dir / "rag" / "vector"
    assert get_project_rag_keyword_dir(project_root) == project_dir / "rag" / "keyword"
    assert get_project_rag_status_path(project_root) == project_dir / "rag" / "status.json"
    assert get_project_runtime_llm_cache_dir(project_root) == project_dir / "runtime" / "llm_cache"
    assert get_project_runtime_build_jobs_dir(project_root) == project_dir / "runtime" / "build_jobs"
    assert get_project_runtime_temp_dir(project_root) == project_dir / "runtime" / "temp"
    assert get_project_runtime_logs_dir(project_root) == project_dir / "runtime" / "logs"
    assert get_project_admin_dir(project_root) == get_project_bundle_root(project_root) / "admin"


def test_legacy_index_helper_is_preserved(tmp_path):
    project_root = tmp_path / "svn-root"
    project_root.mkdir()

    assert get_legacy_index_dir(project_root) == project_root / ".ltclaw_index"


def test_agent_and_session_helpers_stay_under_agent_session_layers(monkeypatch, tmp_path):
    working_root = tmp_path / "working-root"
    workspace_dir = tmp_path / "workspace" / "agent alpha"
    project_root = tmp_path / "svn-root"
    monkeypatch.setenv("LTCLAW_WORKING_DIR", str(working_root))
    workspace_dir.mkdir(parents=True)
    project_root.mkdir()

    agent_dir = get_agent_store_dir(workspace_dir, project_root)
    workbench_dir = get_workspace_game_dir(workspace_dir, project_root, session_id="chat 42")
    proposals_dir = get_agent_session_proposals_dir(workspace_dir, project_root, session_id="chat 42")
    ui_state_path = get_agent_session_ui_state_path(workspace_dir, project_root, session_id="chat 42")

    assert agent_dir == get_project_bundle_root(project_root) / "agents" / "agent-alpha"
    assert get_agent_profile_path(workspace_dir, project_root) == agent_dir / "profile.yaml"
    assert get_agent_workbench_writeback_audit_path(workspace_dir, project_root) == (
        agent_dir / "audit" / "workbench_writeback.jsonl"
    )
    assert workbench_dir == agent_dir / "sessions" / "chat-42" / "workbench"
    assert proposals_dir == agent_dir / "sessions" / "chat-42" / "proposals"
    assert ui_state_path == agent_dir / "sessions" / "chat-42" / "ui_state.json"
    assert project_root.name not in workbench_dir.parts[-3:]


def test_storage_summary_includes_bundle_legacy_and_runtime_paths(monkeypatch, tmp_path):
    working_root = tmp_path / "working-root"
    workspace_dir = tmp_path / "workspace" / "agent alpha"
    project_root = tmp_path / "svn-root"
    monkeypatch.setenv("LTCLAW_WORKING_DIR", str(working_root))
    workspace_dir.mkdir(parents=True)
    project_root.mkdir()

    summary = get_storage_summary(workspace_dir, svn_root=project_root, session_id="chat 42")

    assert summary["project_key"] == get_project_key(project_root)
    assert summary["project_bundle_root"] == str(get_project_bundle_root(project_root))
    assert summary["project_source_config_path"] == str(get_project_source_config_path(project_root))
    assert summary["legacy_index_dir"] == str(get_legacy_index_dir(project_root))
    assert summary["project_runtime_dir"] == str(get_project_bundle_project_dir(project_root) / "runtime")
    assert summary["project_admin_dir"] == str(get_project_admin_dir(project_root))
    assert summary["agent_store_dir"] == str(get_agent_store_dir(workspace_dir, project_root))
    assert summary["agent_profile_path"] == str(get_agent_profile_path(workspace_dir, project_root))
    assert summary["session_store_dir"].endswith("agents/agent-alpha/sessions/chat-42")
    assert summary["workbench_dir"].endswith("agents/agent-alpha/sessions/chat-42/workbench")
    assert summary["agent_session_proposals_dir"].endswith("agents/agent-alpha/sessions/chat-42/proposals")
    assert summary["agent_session_ui_state_path"].endswith("agents/agent-alpha/sessions/chat-42/ui_state.json")