"""
??????????

??????agent ????????????? LTCLAW ????????
????????????????????? workspace ??
"""

import hashlib
import os
from pathlib import Path

import yaml

from ..constant import WORKING_DIR


_GAME_PROJECTS_DIR_ENV_VARS = (
    "LTCLAW_GAME_PROJECTS_DIR",
    "QWENPAW_GAME_PROJECTS_DIR",
    "COPAW_GAME_PROJECTS_DIR",
)

_WORKING_DIR_ENV_VARS = (
    "LTCLAW_WORKING_DIR",
    "QWENPAW_WORKING_DIR",
    "COPAW_WORKING_DIR",
)

_DEFAULT_SESSION_NAME = "default"
_DEFAULT_WORKSPACE_NAME = "LTClaw Workspace"
_UNSET = object()
_DEFAULT_WORKSPACE_STORAGE = {
    "projects_dir": "projects",
    "agents_dir": "agents",
    "sessions_dir": "sessions",
    "audit_dir": "audit",
    "cache_dir": "cache",
}


def _get_first_env_path(env_names: tuple[str, ...]) -> Path | None:
    for env_name in env_names:
        env_value = os.environ.get(env_name)
        if env_value:
            return Path(env_value).expanduser()
    return None


def _sanitize_path_component(value: str, default: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in str(value or ""))
    return safe.strip("-") or default


def _get_working_root() -> Path:
    configured_root = _get_first_env_path(_WORKING_DIR_ENV_VARS)
    if configured_root is not None:
        return configured_root
    return Path(WORKING_DIR)


def _normalize_local_path(value: str | os.PathLike[str] | None) -> Path | None:
    if value is None:
        return None
    candidate = str(value).strip()
    if not candidate:
        return None
    return Path(candidate.replace("\\", "/")).expanduser()


def _read_yaml_mapping(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass
    return {}


def _write_yaml_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with open(temp_path, "w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, allow_unicode=True, sort_keys=False)
    temp_path.replace(path)


def get_workspace_pointer_path() -> Path:
    return get_user_config_dir() / "workspace_pointer.yaml"


def get_active_data_workspace_root() -> Path | None:
    pointer = _read_yaml_mapping(get_workspace_pointer_path())
    return _normalize_local_path(pointer.get("active_workspace_root"))


def get_workspace_config_path(workspace_root: Path) -> Path:
    return Path(workspace_root).expanduser() / "workspace.yaml"


def _default_workspace_config(
    *,
    workspace_name: str | None = None,
    active_project_key: str | None = None,
    active_project_root: str | None = None,
) -> dict:
    return {
        "schema_version": "workspace.v1",
        "workspace_name": str(workspace_name or _DEFAULT_WORKSPACE_NAME),
        "active_project_key": active_project_key,
        "active_project_root": active_project_root,
        "storage": dict(_DEFAULT_WORKSPACE_STORAGE),
    }


def load_data_workspace_config(workspace_root: Path) -> dict:
    config = _read_yaml_mapping(get_workspace_config_path(workspace_root))
    if not config:
        return _default_workspace_config()
    storage = config.get("storage") if isinstance(config.get("storage"), dict) else {}
    merged_storage = {**_DEFAULT_WORKSPACE_STORAGE, **storage}
    return {
        "schema_version": config.get("schema_version") or "workspace.v1",
        "workspace_name": config.get("workspace_name") or _DEFAULT_WORKSPACE_NAME,
        "active_project_key": config.get("active_project_key"),
        "active_project_root": str(config.get("active_project_root") or "").strip() or None,
        "storage": merged_storage,
    }


def save_data_workspace_config(
    workspace_root: Path,
    *,
    workspace_name: str | None = None,
    active_project_key: str | None | object = _UNSET,
    active_project_root: str | os.PathLike[str] | None | object = _UNSET,
) -> dict:
    workspace_root = Path(workspace_root).expanduser()
    existing = load_data_workspace_config(workspace_root)
    next_active_project_root = existing.get("active_project_root")
    if active_project_root is not _UNSET:
        normalized_active_project_root = _normalize_local_path(active_project_root)
        next_active_project_root = (
            str(normalized_active_project_root)
            if normalized_active_project_root is not None
            else None
        )
    payload = {
        "schema_version": "workspace.v1",
        "workspace_name": workspace_name or existing.get("workspace_name") or _DEFAULT_WORKSPACE_NAME,
        "active_project_key": (
            existing.get("active_project_key")
            if active_project_key is _UNSET
            else active_project_key
        ),
        "active_project_root": next_active_project_root,
        "storage": dict(existing.get("storage") or _DEFAULT_WORKSPACE_STORAGE),
    }
    _write_yaml_atomic(get_workspace_config_path(workspace_root), payload)
    return payload


def get_active_workspace_project_root() -> Path | None:
    workspace_root = get_active_data_workspace_root()
    if workspace_root is None:
        return None
    workspace_config = load_data_workspace_config(workspace_root)
    return _normalize_local_path(workspace_config.get("active_project_root"))


def get_workspace_projects_dir(workspace_root: Path) -> Path:
    config = load_data_workspace_config(workspace_root)
    return Path(workspace_root).expanduser() / str(config["storage"].get("projects_dir") or "projects")


def get_workspace_agents_dir(workspace_root: Path) -> Path:
    config = load_data_workspace_config(workspace_root)
    return Path(workspace_root).expanduser() / str(config["storage"].get("agents_dir") or "agents")


def get_workspace_sessions_dir(workspace_root: Path) -> Path:
    config = load_data_workspace_config(workspace_root)
    return Path(workspace_root).expanduser() / str(config["storage"].get("sessions_dir") or "sessions")


def get_workspace_audit_dir(workspace_root: Path) -> Path:
    config = load_data_workspace_config(workspace_root)
    return Path(workspace_root).expanduser() / str(config["storage"].get("audit_dir") or "audit")


def get_workspace_cache_dir(workspace_root: Path) -> Path:
    config = load_data_workspace_config(workspace_root)
    return Path(workspace_root).expanduser() / str(config["storage"].get("cache_dir") or "cache")


def get_workspace_project_bundle_root(workspace_root: Path, project_root: Path) -> Path:
    return get_workspace_projects_dir(workspace_root) / get_project_key(project_root)


def get_workspace_agent_profile_path(agent_id: str, workspace_root: Path) -> Path:
    safe_agent_id = _sanitize_path_component(agent_id, "default")
    return get_workspace_agents_dir(workspace_root) / f"{safe_agent_id}.yaml"


def ensure_data_workspace_layout(
    workspace_root: Path,
    *,
    workspace_name: str | None = None,
    active_project_key: str | None | object = _UNSET,
    active_project_root: str | os.PathLike[str] | None | object = _UNSET,
) -> dict:
    workspace_root = Path(workspace_root).expanduser()
    workspace_root.mkdir(parents=True, exist_ok=True)
    config = save_data_workspace_config(
        workspace_root,
        workspace_name=workspace_name,
        active_project_key=active_project_key,
        active_project_root=active_project_root,
    )
    get_workspace_projects_dir(workspace_root).mkdir(parents=True, exist_ok=True)
    get_workspace_agents_dir(workspace_root).mkdir(parents=True, exist_ok=True)
    get_workspace_sessions_dir(workspace_root).mkdir(parents=True, exist_ok=True)
    get_workspace_audit_dir(workspace_root).mkdir(parents=True, exist_ok=True)
    get_workspace_cache_dir(workspace_root).mkdir(parents=True, exist_ok=True)
    return config


def set_active_data_workspace_root(
    path: str | os.PathLike[str],
    *,
    workspace_name: str | None = None,
    active_project_key: str | None | object = _UNSET,
    active_project_root: str | os.PathLike[str] | None | object = _UNSET,
) -> Path:
    workspace_root = _normalize_local_path(path)
    if workspace_root is None:
        raise ValueError("workspace_root must not be empty")
    ensure_data_workspace_layout(
        workspace_root,
        workspace_name=workspace_name,
        active_project_key=active_project_key,
        active_project_root=active_project_root,
    )
    _write_yaml_atomic(
        get_workspace_pointer_path(),
        {"active_workspace_root": str(workspace_root)},
    )
    return workspace_root


def _active_workspace_root() -> Path | None:
    return get_active_data_workspace_root()


def _resolve_agent_id(workspace_dir: Path) -> str:
    try:
        from ..app.agent_context import get_current_agent_id

        agent_id = get_current_agent_id()
        if agent_id:
            return _sanitize_path_component(agent_id, "default")
    except Exception:
        pass
    return _sanitize_path_component(Path(workspace_dir).name, "default")


def _project_cache_key(svn_root: Path | None) -> str:
    if svn_root is None:
        return "unbound"
    return get_project_key(svn_root)


def get_game_data_root() -> Path:
    return _get_working_root() / "game_data"


def _get_project_store_root() -> Path:
    workspace_root = _active_workspace_root()
    if workspace_root is not None:
        return get_workspace_projects_dir(workspace_root)
    configured_root = _get_first_env_path(_GAME_PROJECTS_DIR_ENV_VARS)
    if configured_root:
        return configured_root
    return get_game_data_root() / "projects"


def _project_store_name(svn_root: Path) -> str:
    canonical = str(svn_root.expanduser().resolve(strict=False))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
    base_name = svn_root.expanduser().resolve(strict=False).name or "project"
    safe_name = _sanitize_path_component(base_name, "project")
    return f"{safe_name}-{digest}"


def _agent_store_name(workspace_dir: Path) -> str:
    return _sanitize_path_component(Path(workspace_dir).name, "agent")


def _resolve_session_name(session_id: str | None = None) -> str:
    if session_id:
        return _sanitize_path_component(session_id, _DEFAULT_SESSION_NAME)
    try:
        from ..app.agent_context import get_current_root_session_id, get_current_session_id
        current = get_current_root_session_id() or get_current_session_id()
        if current:
            return _sanitize_path_component(current, _DEFAULT_SESSION_NAME)
    except Exception:
        pass
    return _DEFAULT_SESSION_NAME


def get_legacy_index_dir(svn_root: Path) -> Path:
    """?????: <svn>/.ltclaw_index"""
    return svn_root / ".ltclaw_index"


def get_project_key(project_root: Path) -> str:
    return _project_store_name(Path(project_root))


def get_project_bundle_root(project_root: Path) -> Path:
    workspace_root = _active_workspace_root()
    if workspace_root is not None:
        return get_workspace_project_bundle_root(workspace_root, project_root)
    return _get_project_store_root() / get_project_key(project_root)


def get_project_bundle_project_dir(project_root: Path) -> Path:
    """Current compatibility location for project-level artifacts."""
    return get_project_bundle_root(project_root) / "project"


def _get_configured_maprag_bundle_root() -> Path | None:
    try:
        from .config import load_user_config

        cfg = load_user_config()
        raw = getattr(cfg, "maprag_bundle_root", None)
        if raw and str(raw).strip():
            return Path(str(raw).strip()).expanduser()
    except Exception:
        return None
    return None


def get_project_maprag_root(project_root: Path) -> Path:
    configured = _get_configured_maprag_bundle_root()
    if configured is not None:
        return configured
    return get_project_bundle_project_dir(project_root)


def get_project_store_dir(svn_root: Path) -> Path:
    """??????: <game-data>/projects/<project-key>"""
    return get_project_bundle_root(svn_root)


def get_project_data_dir(svn_root: Path) -> Path:
    """??????: <project-store>/project"""
    return get_project_bundle_project_dir(svn_root)


def get_project_manifest_path(project_root: Path) -> Path:
    return get_project_bundle_project_dir(project_root) / "project.json"


def get_project_source_config_path(project_root: Path) -> Path:
    return get_project_bundle_project_dir(project_root) / "source_config.yaml"


def get_project_sources_dir(project_root: Path) -> Path:
    return get_project_bundle_project_dir(project_root) / "sources"


def get_project_docs_source_path(project_root: Path) -> Path:
    return get_project_sources_dir(project_root) / "docs.yaml"


def get_project_tables_source_path(project_root: Path) -> Path:
    return get_project_sources_dir(project_root) / "tables.yaml"


def get_project_scripts_source_path(project_root: Path) -> Path:
    return get_project_sources_dir(project_root) / "scripts.yaml"


def get_project_indexes_dir(project_root: Path) -> Path:
    return get_project_bundle_project_dir(project_root) / "indexes"


def get_project_raw_indexes_dir(project_root: Path) -> Path:
    return get_project_indexes_dir(project_root) / "raw"


def get_project_raw_docs_dir(project_root: Path) -> Path:
    return get_project_raw_indexes_dir(project_root) / "docs"


def get_project_raw_tables_dir(project_root: Path) -> Path:
    return get_project_raw_indexes_dir(project_root) / "tables"


def get_project_raw_table_indexes_path(project_root: Path) -> Path:
    return get_project_raw_indexes_dir(project_root) / "table_indexes.json"


def get_project_raw_table_index_path(project_root: Path, table_id: str) -> Path:
    return get_project_raw_tables_dir(project_root) / f"{_sanitize_path_component(table_id, 'table')}.json"


def get_project_raw_scripts_dir(project_root: Path) -> Path:
    return get_project_raw_indexes_dir(project_root) / "scripts"


def get_project_canonical_indexes_dir(project_root: Path) -> Path:
    return get_project_indexes_dir(project_root) / "canonical"


def get_project_canonical_docs_dir(project_root: Path) -> Path:
    return get_project_canonical_indexes_dir(project_root) / "docs"


def get_project_canonical_tables_dir(project_root: Path) -> Path:
    return get_project_canonical_indexes_dir(project_root) / "tables"


def get_project_canonical_scripts_dir(project_root: Path) -> Path:
    return get_project_canonical_indexes_dir(project_root) / "scripts"


def get_project_canonical_table_schema_path(project_root: Path, table_id: str) -> Path:
    return get_project_canonical_tables_dir(project_root) / f"{_sanitize_path_component(table_id, 'table')}.json"


def get_project_canonical_doc_facts_path(project_root: Path, doc_id: str) -> Path:
    return get_project_canonical_docs_dir(project_root) / f"{_sanitize_path_component(doc_id, 'doc')}.json"


def get_project_canonical_script_facts_path(project_root: Path, script_id: str) -> Path:
    return get_project_canonical_scripts_dir(project_root) / f"{_sanitize_path_component(script_id, 'script')}.json"


def get_project_maps_dir(project_root: Path) -> Path:
    return get_project_maprag_root(project_root) / "maps"


def get_project_candidate_maps_dir(project_root: Path) -> Path:
    return get_project_maps_dir(project_root) / "candidate"


def get_project_candidate_map_path(project_root: Path) -> Path:
    return get_project_candidate_maps_dir(project_root) / "latest.json"


def get_project_candidate_map_history_dir(project_root: Path) -> Path:
    return get_project_candidate_maps_dir(project_root) / "history"


def get_project_formal_maps_dir(project_root: Path) -> Path:
    return get_project_maps_dir(project_root) / "formal"


def get_project_formal_map_canonical_path(project_root: Path) -> Path:
    return get_project_formal_maps_dir(project_root) / "formal_map.json"


def get_project_formal_map_history_path(project_root: Path) -> Path:
    return get_project_formal_maps_dir(project_root) / "formal_map.history.jsonl"


def get_project_map_diffs_dir(project_root: Path) -> Path:
    return get_project_maps_dir(project_root) / "diffs"


def get_project_latest_map_diff_path(project_root: Path) -> Path:
    return get_project_map_diffs_dir(project_root) / "latest_diff.json"


def get_project_releases_dir(project_root: Path) -> Path:
    return get_project_maprag_root(project_root) / "releases"


def get_project_current_release_path(project_root: Path) -> Path:
    return get_project_releases_dir(project_root) / "current.json"


def get_project_release_dir(project_root: Path, release_id: str) -> Path:
    release_name = _sanitize_path_component(str(release_id or ""), "release")
    return get_project_releases_dir(project_root) / release_name


def get_project_rag_dir(project_root: Path) -> Path:
    return get_project_maprag_root(project_root) / "rag"


def get_project_current_rag_dir(project_root: Path) -> Path:
    return get_project_rag_dir(project_root) / "current"


def get_project_rag_context_index_path(project_root: Path) -> Path:
    return get_project_current_rag_dir(project_root) / "context_index.jsonl"


def get_project_rag_citation_index_path(project_root: Path) -> Path:
    return get_project_current_rag_dir(project_root) / "citation_index.jsonl"


def get_project_rag_map_route_cache_path(project_root: Path) -> Path:
    return get_project_current_rag_dir(project_root) / "map_route_cache.jsonl"


def get_project_rag_vector_dir(project_root: Path) -> Path:
    return get_project_rag_dir(project_root) / "vector"


def get_project_rag_keyword_dir(project_root: Path) -> Path:
    return get_project_rag_dir(project_root) / "keyword"


def get_project_rag_status_path(project_root: Path) -> Path:
    return get_project_rag_dir(project_root) / "status.json"


def get_project_runtime_dir(project_root: Path) -> Path:
    return get_project_bundle_project_dir(project_root) / "runtime"


def get_project_runtime_llm_cache_dir(project_root: Path) -> Path:
    return get_project_runtime_dir(project_root) / "llm_cache"


def get_project_runtime_build_jobs_dir(project_root: Path) -> Path:
    return get_project_runtime_dir(project_root) / "build_jobs"


def get_project_runtime_build_job_path(project_root: Path, job_id: str) -> Path:
    safe_job_id = _sanitize_path_component(str(job_id or ""), "job")
    return get_project_runtime_build_jobs_dir(project_root) / f"{safe_job_id}.json"


def get_project_runtime_temp_dir(project_root: Path) -> Path:
    return get_project_runtime_dir(project_root) / "temp"


def get_project_runtime_logs_dir(project_root: Path) -> Path:
    return get_project_runtime_dir(project_root) / "logs"


def get_project_admin_dir(project_root: Path) -> Path:
    return get_project_bundle_root(project_root) / "admin"


def get_project_config_dir(svn_root: Path) -> Path:
    return get_project_data_dir(svn_root) / "config"


def get_index_dir(svn_root: Path) -> Path:
    """??????: <project-store>/project/indexes"""
    return get_project_data_dir(svn_root) / "indexes"


def get_tables_dir(svn_root: Path) -> Path:
    return get_index_dir(svn_root) / "tables"


def get_docs_dir(svn_root: Path) -> Path:
    return get_index_dir(svn_root) / "docs"


def get_project_config_path(svn_root: Path) -> Path:
    return get_project_config_dir(svn_root) / "project_config.yaml"


def get_legacy_project_config_path(svn_root: Path) -> Path:
    return get_legacy_index_dir(svn_root) / "project_config.yaml"


def get_dependency_graph_path(svn_root: Path) -> Path:
    return get_index_dir(svn_root) / "dependency_graph.json"


def get_table_indexes_path(svn_root: Path) -> Path:
    return get_index_dir(svn_root) / "table_indexes.json"


def get_registry_path(svn_root: Path) -> Path:
    return get_index_dir(svn_root) / "registry.json"


def get_user_config_dir() -> Path:
    return get_game_data_root() / "user"


def get_user_config_path() -> Path:
    """???????: <working>/game_data/user/game_user.yaml"""
    return get_user_config_dir() / "game_user.yaml"


def get_legacy_user_config_path() -> Path:
    """???????: <working>/game_user.yaml"""
    return _get_working_root() / "game_user.yaml"


def get_agent_store_dir(workspace_dir: Path, svn_root: Path | None = None) -> Path:
    workspace_root = _active_workspace_root()
    agent_id = _resolve_agent_id(workspace_dir)
    if workspace_root is not None:
        return get_workspace_agents_dir(workspace_root) / agent_id
    agent_name = _agent_store_name(workspace_dir)
    if svn_root is not None:
        return get_project_store_dir(svn_root) / "agents" / agent_name
    return get_game_data_root() / "agents" / agent_name


def get_agent_profile_path(workspace_dir: Path, svn_root: Path | None = None) -> Path:
    workspace_root = _active_workspace_root()
    if workspace_root is not None:
        return get_workspace_agent_profile_path(_resolve_agent_id(workspace_dir), workspace_root)
    return get_agent_store_dir(workspace_dir, svn_root) / "profile.yaml"


def get_agent_audit_dir(workspace_dir: Path, svn_root: Path | None = None) -> Path:
    workspace_root = _active_workspace_root()
    if workspace_root is not None:
        return get_workspace_audit_dir(workspace_root)
    return get_agent_store_dir(workspace_dir, svn_root) / "audit"


def get_agent_workbench_writeback_audit_path(
    workspace_dir: Path,
    svn_root: Path | None = None,
) -> Path:
    return get_agent_audit_dir(workspace_dir, svn_root) / "workbench_writeback.jsonl"


def get_session_store_dir(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> Path:
    workspace_root = _active_workspace_root()
    if workspace_root is not None:
        return (
            get_workspace_sessions_dir(workspace_root)
            / _resolve_agent_id(workspace_dir)
            / _resolve_session_name(session_id)
        )
    return get_agent_store_dir(workspace_dir, svn_root) / "sessions" / _resolve_session_name(session_id)


def get_agent_session_dir(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> Path:
    return get_session_store_dir(workspace_dir, svn_root, session_id)


def get_agent_session_workbench_dir(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> Path:
    return get_agent_session_dir(workspace_dir, svn_root, session_id) / "workbench"


def get_agent_session_proposals_dir(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> Path:
    return get_agent_session_dir(workspace_dir, svn_root, session_id) / "proposals"


def get_agent_session_ui_state_path(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> Path:
    return get_agent_session_dir(workspace_dir, svn_root, session_id) / "ui_state.json"


def get_workspace_game_dir(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> Path:
    """?????????: .../sessions/<session>/workbench"""
    return get_agent_session_workbench_dir(workspace_dir, svn_root, session_id)


def get_chroma_dir(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> Path:
    workspace_root = _active_workspace_root()
    if workspace_root is not None:
        return get_workspace_cache_dir(workspace_root) / "retrieval" / _project_cache_key(svn_root) / "chroma"
    return get_session_store_dir(workspace_dir, svn_root, session_id) / "caches" / "chroma"


def get_llm_cache_dir(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> Path:
    workspace_root = _active_workspace_root()
    if workspace_root is not None:
        return get_workspace_cache_dir(workspace_root) / "llm" / _project_cache_key(svn_root)
    return get_session_store_dir(workspace_dir, svn_root, session_id) / "caches" / "llm"


def get_svn_cache_dir(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> Path:
    workspace_root = _active_workspace_root()
    if workspace_root is not None:
        return get_workspace_cache_dir(workspace_root) / "temp" / "svn" / _project_cache_key(svn_root)
    return get_session_store_dir(workspace_dir, svn_root, session_id) / "caches" / "svn"


def get_proposals_dir(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> Path:
    return get_session_store_dir(workspace_dir, svn_root, session_id) / "tools" / "proposals"


def get_code_index_dir(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> Path:
    workspace_root = _active_workspace_root()
    if workspace_root is not None and svn_root is not None:
        return get_project_runtime_dir(svn_root) / "code_index"
    if workspace_root is not None:
        return get_workspace_cache_dir(workspace_root) / "temp" / "code_index" / _project_cache_key(svn_root)
    return get_session_store_dir(workspace_dir, svn_root, session_id) / "databases" / "code_index"


def get_retrieval_dir(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> Path:
    workspace_root = _active_workspace_root()
    if workspace_root is not None:
        return get_workspace_cache_dir(workspace_root) / "retrieval" / _project_cache_key(svn_root)
    return get_session_store_dir(workspace_dir, svn_root, session_id) / "databases" / "retrieval"


def get_knowledge_base_dir(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> Path:
    workspace_root = _active_workspace_root()
    if workspace_root is not None and svn_root is not None:
        return get_project_rag_dir(svn_root) / "knowledge_base"
    if workspace_root is not None:
        return get_workspace_cache_dir(workspace_root) / "retrieval" / _project_cache_key(svn_root) / "knowledge_base"
    return get_session_store_dir(workspace_dir, svn_root, session_id) / "databases" / "knowledge_base"


def get_knowledge_working_dir(project_root: Path) -> Path:
    return get_project_maprag_root(Path(project_root)) / "working"


def get_knowledge_releases_dir(project_root: Path) -> Path:
    return get_project_releases_dir(Path(project_root))


def get_current_release_path(project_root: Path) -> Path:
    return get_project_current_release_path(project_root)


def get_release_dir(project_root: Path, release_id: str) -> Path:
    return get_project_release_dir(project_root, release_id)


def get_pending_test_plans_path(project_root: Path) -> Path:
    return get_project_data_dir(Path(project_root)) / "pending" / "test_plans.jsonl"


def get_release_candidates_path(project_root: Path) -> Path:
    return get_project_data_dir(Path(project_root)) / "pending" / "release_candidates.jsonl"


def get_formal_map_path(project_root: Path) -> Path:
    return get_knowledge_working_dir(project_root) / "formal_map.json"


def get_storage_summary(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> dict[str, str | None]:
    workspace_dir = Path(workspace_dir)
    active_workspace_root = _active_workspace_root()
    workspace_config_path = str(get_workspace_config_path(active_workspace_root)) if active_workspace_root is not None else None
    workspace_config = load_data_workspace_config(active_workspace_root) if active_workspace_root is not None else None
    summary = {
        "working_root": str(_get_working_root()),
        "game_data_root": str(get_game_data_root()),
        "workspace_dir": str(workspace_dir),
        "active_workspace_root": str(active_workspace_root) if active_workspace_root is not None else None,
        "active_workspace_project_root": workspace_config.get("active_project_root") if workspace_config is not None else None,
        "workspace_pointer_path": str(get_workspace_pointer_path()),
        "workspace_config_path": workspace_config_path,
        "workspace_name": workspace_config.get("workspace_name") if workspace_config is not None else None,
        "workspace_projects_dir": str(get_workspace_projects_dir(active_workspace_root)) if active_workspace_root is not None else None,
        "workspace_agents_dir": str(get_workspace_agents_dir(active_workspace_root)) if active_workspace_root is not None else None,
        "workspace_sessions_dir": str(get_workspace_sessions_dir(active_workspace_root)) if active_workspace_root is not None else None,
        "workspace_audit_dir": str(get_workspace_audit_dir(active_workspace_root)) if active_workspace_root is not None else None,
        "workspace_cache_dir": str(get_workspace_cache_dir(active_workspace_root)) if active_workspace_root is not None else None,
        "current_agent_id": _resolve_agent_id(workspace_dir),
        "user_config_path": str(get_user_config_path()),
        "legacy_user_config_path": str(get_legacy_user_config_path()),
        "svn_root": str(svn_root) if svn_root is not None else None,
        "project_key": get_project_key(svn_root) if svn_root is not None else None,
        "project_store_dir": str(get_project_store_dir(svn_root)) if svn_root is not None else None,
        "project_bundle_root": str(get_project_bundle_root(svn_root)) if svn_root is not None else None,
        "project_data_dir": str(get_project_data_dir(svn_root)) if svn_root is not None else None,
        "project_source_config_path": str(get_project_source_config_path(svn_root)) if svn_root is not None else None,
        "legacy_index_dir": str(get_legacy_index_dir(svn_root)) if svn_root is not None else None,
        "project_config_path": str(get_project_config_path(svn_root)) if svn_root is not None else None,
        "project_index_dir": str(get_index_dir(svn_root)) if svn_root is not None else None,
        "project_runtime_dir": str(get_project_runtime_dir(svn_root)) if svn_root is not None else None,
        "project_admin_dir": str(get_project_admin_dir(svn_root)) if svn_root is not None else None,
        "agent_store_dir": str(get_agent_store_dir(workspace_dir, svn_root)),
        "agent_profile_path": str(get_agent_profile_path(workspace_dir, svn_root)),
        "agent_audit_dir": str(get_agent_audit_dir(workspace_dir, svn_root)),
        "session_store_dir": str(get_session_store_dir(workspace_dir, svn_root, session_id)),
        "workbench_dir": str(get_workspace_game_dir(workspace_dir, svn_root, session_id)),
        "agent_session_proposals_dir": str(get_agent_session_proposals_dir(workspace_dir, svn_root, session_id)),
        "agent_session_ui_state_path": str(get_agent_session_ui_state_path(workspace_dir, svn_root, session_id)),
        "chroma_dir": str(get_chroma_dir(workspace_dir, svn_root, session_id)),
        "llm_cache_dir": str(get_llm_cache_dir(workspace_dir, svn_root, session_id)),
        "svn_cache_dir": str(get_svn_cache_dir(workspace_dir, svn_root, session_id)),
        "proposals_dir": str(get_proposals_dir(workspace_dir, svn_root, session_id)),
        "code_index_dir": str(get_code_index_dir(workspace_dir, svn_root, session_id)),
        "retrieval_dir": str(get_retrieval_dir(workspace_dir, svn_root, session_id)),
        "knowledge_base_dir": str(get_knowledge_base_dir(workspace_dir, svn_root, session_id)),
        "session_name": _resolve_session_name(session_id),
    }
    return summary
