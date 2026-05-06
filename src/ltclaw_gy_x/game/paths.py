"""
??????????

??????agent ????????????? LTCLAW ????????
????????????????????? workspace ??
"""

import hashlib
import os
from pathlib import Path

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


def get_game_data_root() -> Path:
    return _get_working_root() / "game_data"


def _get_project_store_root() -> Path:
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


def get_project_store_dir(svn_root: Path) -> Path:
    """??????: <game-data>/projects/<project-key>"""
    return _get_project_store_root() / _project_store_name(svn_root)


def get_project_data_dir(svn_root: Path) -> Path:
    """??????: <project-store>/project"""
    return get_project_store_dir(svn_root) / "project"


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
    agent_name = _agent_store_name(workspace_dir)
    if svn_root is not None:
        return get_project_store_dir(svn_root) / "agents" / agent_name
    return get_game_data_root() / "agents" / agent_name


def get_session_store_dir(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> Path:
    return get_agent_store_dir(workspace_dir, svn_root) / "sessions" / _resolve_session_name(session_id)


def get_workspace_game_dir(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> Path:
    """?????????: .../sessions/<session>/workbench"""
    return get_session_store_dir(workspace_dir, svn_root, session_id) / "workbench"


def get_chroma_dir(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> Path:
    return get_session_store_dir(workspace_dir, svn_root, session_id) / "caches" / "chroma"


def get_llm_cache_dir(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> Path:
    return get_session_store_dir(workspace_dir, svn_root, session_id) / "caches" / "llm"


def get_svn_cache_dir(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> Path:
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
    return get_session_store_dir(workspace_dir, svn_root, session_id) / "databases" / "code_index"


def get_retrieval_dir(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> Path:
    return get_session_store_dir(workspace_dir, svn_root, session_id) / "databases" / "retrieval"


def get_knowledge_base_dir(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> Path:
    return get_session_store_dir(workspace_dir, svn_root, session_id) / "databases" / "knowledge_base"


def get_storage_summary(
    workspace_dir: Path,
    svn_root: Path | None = None,
    session_id: str | None = None,
) -> dict[str, str | None]:
    workspace_dir = Path(workspace_dir)
    summary = {
        "working_root": str(_get_working_root()),
        "game_data_root": str(get_game_data_root()),
        "workspace_dir": str(workspace_dir),
        "user_config_path": str(get_user_config_path()),
        "legacy_user_config_path": str(get_legacy_user_config_path()),
        "svn_root": str(svn_root) if svn_root is not None else None,
        "project_store_dir": str(get_project_store_dir(svn_root)) if svn_root is not None else None,
        "project_config_path": str(get_project_config_path(svn_root)) if svn_root is not None else None,
        "project_index_dir": str(get_index_dir(svn_root)) if svn_root is not None else None,
        "agent_store_dir": str(get_agent_store_dir(workspace_dir, svn_root)),
        "session_store_dir": str(get_session_store_dir(workspace_dir, svn_root, session_id)),
        "workbench_dir": str(get_workspace_game_dir(workspace_dir, svn_root, session_id)),
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
