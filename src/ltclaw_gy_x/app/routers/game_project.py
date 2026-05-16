"""Game project HTTP API."""
import logging
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ltclaw_gy_x.app.agent_context import get_agent_for_request
from ltclaw_gy_x.app.capabilities import build_agent_capability_profile
from ltclaw_gy_x.app.multi_agent_manager import get_active_manager
from ltclaw_gy_x.game.config import (
    DEFAULT_TABLES_EXCLUDE_PATTERNS,
    DEFAULT_TABLES_INCLUDE_PATTERNS,
    DEFAULT_TABLES_PRIMARY_KEY_CANDIDATES,
    LocalAgentProfile,
    ensure_default_workspace_agent_profile,
    ProjectConfig,
    ProjectTablesSourceConfig,
    UserGameConfig,
    ValidationIssue,
    load_project_tables_source_config,
    load_workspace_agent_profile,
    save_project_config,
    save_project_tables_source_config,
    save_user_config,
    save_workspace_agent_profile,
    validate_project_config,
)
from ltclaw_gy_x.app.capabilities import LOCAL_CAPABILITY_CATALOG
from ltclaw_gy_x.game.paths import (
    ensure_data_workspace_layout,
    get_active_data_workspace_root,
    get_active_workspace_project_root,
    get_project_bundle_root,
    get_project_config_path,
    get_project_key,
    get_project_tables_source_path,
    get_storage_summary,
    get_workspace_config_path,
    get_workspace_pointer_path,
    load_data_workspace_config,
    save_data_workspace_config,
    set_active_data_workspace_root,
)
from ltclaw_gy_x.game.source_discovery import discover_table_sources

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/game/project", tags=["game-project"])

PROJECT_CONFIG_COMMIT_FROZEN_REASON = (
    "Project config commit is frozen in P0-01. LTClaw keeps reading legacy local project path fields, but SVN add/commit must run outside LTClaw."
)

REMOTE_PATH_PREFIXES = ("svn://", "http://", "https://", "file://")


class ProjectRootUpdateRequest(BaseModel):
    project_root: str


class WorkspaceRootUpdateRequest(BaseModel):
    workspace_root: str
    workspace_name: str | None = None
    create_if_missing: bool = False


class ProjectTablesSourceConfigRequest(BaseModel):
    roots: list[str]
    include: list[str] | None = None
    exclude: list[str] | None = None
    header_row: int = 1
    primary_key_candidates: list[str] | None = None


class WorkspaceAgentProfileRequest(BaseModel):
    display_name: str | None = None
    role: Literal["viewer", "planner", "source_writer", "admin"]
    capabilities: list[str] | None = None


def _configured_project_root_with_source(game_service) -> tuple[str | None, str | None]:
    workspace_project_root = get_active_workspace_project_root()
    if workspace_project_root is not None:
        return str(workspace_project_root), "workspace_active_project_root"
    user_root = str(getattr(game_service.user_config, "svn_local_root", "") or "").strip()
    if user_root:
        return user_root, "user_config_svn_local_root"
    project_config = getattr(game_service, "project_config", None)
    if project_config is None:
        return None, None
    configured_root = str(project_config.svn.root or "").strip()
    if configured_root and "://" not in configured_root:
        return configured_root, "project_config_svn_root"
    return None, None


def _game_service_or_404(workspace):
    svc = workspace.service_manager.services.get("game_service")
    if svc is None:
        raise HTTPException(status_code=404, detail="Game service not available")
    return svc


async def _reload_loaded_game_services(current_workspace, current_game_service) -> None:
    await current_game_service.reload_config()

    manager = get_active_manager()
    if manager is None:
        return

    for loaded_workspace in list(manager.agents.values()):
        if loaded_workspace is current_workspace:
            continue
        service_manager = getattr(loaded_workspace, "service_manager", None)
        if service_manager is None:
            continue
        loaded_game_service = service_manager.services.get("game_service")
        if loaded_game_service is None or loaded_game_service is current_game_service:
            continue
        await loaded_game_service.reload_config()


def _configured_project_root(game_service) -> str | None:
    project_root, _ = _configured_project_root_with_source(game_service)
    return project_root


def _project_root_path(project_root: str | None) -> Path | None:
    if not project_root:
        return None
    return Path(str(project_root).replace("\\", "/")).expanduser()


def _effective_tables_config(project_root: Path | None) -> ProjectTablesSourceConfig:
    if project_root is None or not project_root.exists():
        return ProjectTablesSourceConfig()
    return load_project_tables_source_config(project_root) or ProjectTablesSourceConfig()


def _build_readiness(project_root: str | None, project_root_exists: bool, tables_config: ProjectTablesSourceConfig) -> dict:
    if not project_root:
        return {
            "blocking_reason": "project_root_not_configured",
            "next_action": "set_project_root",
        }
    if not project_root_exists:
        return {
            "blocking_reason": "project_root_missing",
            "next_action": "set_project_root",
        }
    if not tables_config.roots:
        return {
            "blocking_reason": "no_table_sources_found",
            "next_action": "configure_tables_source",
        }
    return {
        "blocking_reason": None,
        "next_action": "ready_for_discovery",
    }


def _serialize_tables_config(tables_config: ProjectTablesSourceConfig) -> dict:
    return {
        "roots": list(tables_config.roots),
        "include": list(tables_config.include),
        "exclude": list(tables_config.exclude),
        "header_row": tables_config.header_row,
        "primary_key_candidates": list(tables_config.primary_key_candidates),
    }


def _build_setup_status(game_service) -> dict:
    project_root, project_root_source = _configured_project_root_with_source(game_service)
    project_root_path = _project_root_path(project_root)
    project_root_exists = bool(project_root_path and project_root_path.exists())
    tables_config = _effective_tables_config(project_root_path)
    active_workspace_root = get_active_data_workspace_root()
    workspace_config = load_data_workspace_config(active_workspace_root) if active_workspace_root is not None else None
    active_workspace_project_root = None
    if workspace_config is not None:
        active_workspace_project_root = workspace_config.get("active_project_root")
    if active_workspace_project_root is None:
        resolved_workspace_project_root = get_active_workspace_project_root()
        if resolved_workspace_project_root is not None:
            active_workspace_project_root = str(resolved_workspace_project_root)
    user_config_svn_local_root = str(getattr(game_service.user_config, "svn_local_root", "") or "").strip() or None
    project_config = getattr(game_service, "project_config", None)
    project_config_svn_root = None
    if project_config is not None:
        configured_root = str(project_config.svn.root or "").strip()
        project_config_svn_root = configured_root or None
    return {
        "active_workspace_root": str(active_workspace_root) if active_workspace_root is not None else None,
        "active_workspace_project_root": active_workspace_project_root,
        "workspace_pointer_path": str(get_workspace_pointer_path()),
        "workspace_config_path": str(get_workspace_config_path(active_workspace_root)) if active_workspace_root is not None else None,
        "workspace_name": workspace_config.get("workspace_name") if workspace_config is not None else None,
        "active_workspace_project_key": workspace_config.get("active_project_key") if workspace_config is not None else None,
        "project_root": project_root,
        "project_root_source": project_root_source,
        "user_config_svn_local_root": user_config_svn_local_root,
        "project_config_svn_root": project_config_svn_root,
        "project_root_exists": project_root_exists,
        "project_bundle_root": str(get_project_bundle_root(project_root_path)) if project_root_path is not None else None,
        "project_key": get_project_key(project_root_path) if project_root_path is not None else None,
        "tables_config": _serialize_tables_config(tables_config),
        "discovery": {
            "status": "not_scanned",
            "discovered_table_count": 0,
            "available_table_count": 0,
            "unsupported_table_count": 0,
            "excluded_table_count": 0,
            "error_count": 0,
        },
        "build_readiness": _build_readiness(project_root, project_root_exists, tables_config),
    }


def _current_tables_config_or_default(game_service) -> ProjectTablesSourceConfig:
    return _effective_tables_config(_project_root_path(_configured_project_root(game_service)))


def _validate_local_project_root(project_root: str) -> Path:
    candidate = str(project_root or "").strip()
    if not candidate:
        raise HTTPException(status_code=400, detail="project_root must not be empty")
    lowered = candidate.lower()
    if lowered.startswith(REMOTE_PATH_PREFIXES) or "://" in candidate:
        raise HTTPException(status_code=400, detail="project_root must be a local filesystem path")
    path = Path(candidate.replace("\\", "/")).expanduser()
    if not path.exists():
        raise HTTPException(status_code=400, detail=f"project_root does not exist: {path}")
    return path


def _sanitize_string_list(values: list[str] | None, default: list[str] | None = None) -> list[str]:
    if values is None:
        return list(default or [])
    return [value.strip() for value in values if str(value).strip()]


def _current_agent_id(request: Request, workspace) -> str:
    return getattr(request.state, 'agent_id', getattr(workspace, 'agent_id', 'default'))


def _workspace_agent_profile_payload(request: Request, workspace, game_service) -> dict:
    agent_id = _current_agent_id(request, workspace)
    workspace_profile = load_workspace_agent_profile(agent_id)
    local_profile = workspace_profile or game_service.user_config.agent_profiles.get(agent_id)
    capability_profile = build_agent_capability_profile(
        agent_id=agent_id,
        display_name=agent_id,
        local_profile=local_profile,
        legacy_my_role=game_service.user_config.my_role,
    )
    effective_profile = workspace_profile or LocalAgentProfile(
        agent_id=agent_id,
        display_name=capability_profile.display_name,
        role=capability_profile.role,
        capabilities=list(local_profile.capabilities) if isinstance(local_profile, LocalAgentProfile) else [],
    )
    return {
        'agent_id': effective_profile.agent_id,
        'display_name': effective_profile.display_name,
        'role': effective_profile.role,
        'capabilities': list(effective_profile.capabilities),
    }


def _sanitize_capability_tokens(values: list[str] | None) -> list[str]:
    allowed = set(LOCAL_CAPABILITY_CATALOG)
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        token = str(value or '').strip()
        if not token or token in seen or token not in allowed:
            continue
        seen.add(token)
        normalized.append(token)
    return normalized


def _capability_status_payload(request: Request, workspace, game_service) -> dict:
    agent_id = _current_agent_id(request, workspace)
    workspace_profile = load_workspace_agent_profile(agent_id)
    local_profile = workspace_profile or game_service.user_config.agent_profiles.get(agent_id)
    capability_profile = build_agent_capability_profile(
        agent_id=agent_id,
        display_name=agent_id,
        local_profile=local_profile,
        legacy_my_role=game_service.user_config.my_role,
    )
    capability_source = (
        'workspace.agents'
        if workspace_profile is not None
        else 'game_user_config.agent_profiles'
        if local_profile is not None
        else 'game_user_config.my_role'
    )
    capabilities = list(capability_profile.capabilities)
    capability_set = set(capabilities)

    def _has(capability: str) -> bool:
        return '*' in capability_set or capability in capability_set

    storage_summary = get_storage_summary(Path(getattr(workspace, 'workspace_dir', '.')))
    required_capabilities = [
        'knowledge.read',
        'knowledge.build',
        'knowledge.publish',
        'knowledge.map.read',
        'knowledge.map.edit',
        'knowledge.candidate.read',
        'knowledge.candidate.write',
        'workbench.read',
        'workbench.test.write',
        'workbench.test.export',
        'workbench.source.write',
    ]
    missing_required_capabilities = [] if '*' in capability_set else [
        item for item in required_capabilities if item not in capability_set
    ]

    return {
        'agent_id': agent_id,
        'role': capability_profile.role,
        'capabilities': capabilities,
        'capability_source': capability_source,
        'is_legacy_role_fallback': workspace_profile is None and local_profile is None,
        'missing_required_capabilities': missing_required_capabilities,
        'required_for_cold_start': {
            'knowledge.candidate.read': _has('knowledge.candidate.read'),
            'knowledge.candidate.write': _has('knowledge.candidate.write'),
        },
        'required_for_formal_map': {
            'knowledge.map.read': _has('knowledge.map.read'),
            'knowledge.map.edit': _has('knowledge.map.edit'),
        },
        'required_for_release': {
            'knowledge.read': _has('knowledge.read'),
            'knowledge.build': _has('knowledge.build'),
            'knowledge.publish': _has('knowledge.publish'),
        },
        'config_paths': {
            'user_config_path': storage_summary['user_config_path'],
            'legacy_user_config_path': storage_summary['legacy_user_config_path'],
        },
    }


@router.get("/config", response_model=Optional[ProjectConfig])
async def get_project_config(workspace=Depends(get_agent_for_request)):
    return _game_service_or_404(workspace).project_config


@router.get("/setup-status")
async def get_project_setup_status(workspace=Depends(get_agent_for_request)):
    game_service = _game_service_or_404(workspace)
    return _build_setup_status(game_service)


@router.get('/capability-status')
async def get_project_capability_status(request: Request, workspace=Depends(get_agent_for_request)):
    game_service = _game_service_or_404(workspace)
    return _capability_status_payload(request, workspace, game_service)


@router.get('/agent-profile')
async def get_workspace_agent_profile_status(request: Request, workspace=Depends(get_agent_for_request)):
    game_service = _game_service_or_404(workspace)
    return _workspace_agent_profile_payload(request, workspace, game_service)


@router.put('/agent-profile')
async def save_workspace_agent_profile_status(
    body: WorkspaceAgentProfileRequest,
    request: Request,
    workspace=Depends(get_agent_for_request),
):
    game_service = _game_service_or_404(workspace)
    agent_id = _current_agent_id(request, workspace)
    profile = LocalAgentProfile(
        agent_id=agent_id,
        display_name=str(body.display_name or '').strip() or agent_id,
        role=body.role,
        capabilities=_sanitize_capability_tokens(body.capabilities),
    )
    save_workspace_agent_profile(profile)
    return {
        'profile': _workspace_agent_profile_payload(request, workspace, game_service),
        'capability_status': _capability_status_payload(request, workspace, game_service),
    }


@router.get('/workspace-root')
async def get_workspace_root_status(workspace=Depends(get_agent_for_request)):
    game_service = _game_service_or_404(workspace)
    active_workspace_root = get_active_data_workspace_root()
    workspace_config = load_data_workspace_config(active_workspace_root) if active_workspace_root is not None else None
    active_workspace_project_root = None
    if workspace_config is not None:
        active_workspace_project_root = workspace_config.get('active_project_root')
    if active_workspace_project_root is None:
        resolved_workspace_project_root = get_active_workspace_project_root()
        if resolved_workspace_project_root is not None:
            active_workspace_project_root = str(resolved_workspace_project_root)
    return {
        'active_workspace_root': str(active_workspace_root) if active_workspace_root is not None else None,
        'active_workspace_project_root': active_workspace_project_root,
        'workspace_pointer_path': str(get_workspace_pointer_path()),
        'workspace_config_path': str(get_workspace_config_path(active_workspace_root)) if active_workspace_root is not None else None,
        'workspace_name': workspace_config.get('workspace_name') if workspace_config is not None else None,
        'active_project_key': workspace_config.get('active_project_key') if workspace_config is not None else None,
        'project_root': _configured_project_root(game_service),
    }


@router.put('/workspace-root')
async def save_workspace_root(
    request: WorkspaceRootUpdateRequest,
    workspace=Depends(get_agent_for_request),
):
    game_service = _game_service_or_404(workspace)
    workspace_root_value = str(request.workspace_root or '').strip()
    if not workspace_root_value:
        raise HTTPException(status_code=400, detail='workspace_root must not be empty')
    workspace_root = Path(workspace_root_value.replace('\\', '/')).expanduser()
    if workspace_root.exists() and not workspace_root.is_dir():
        raise HTTPException(status_code=400, detail=f'workspace_root is not a directory: {workspace_root}')
    if not workspace_root.exists() and not request.create_if_missing:
        raise HTTPException(status_code=400, detail=f'workspace_root does not exist: {workspace_root}')
    project_root = _project_root_path(_configured_project_root(game_service))
    project_key = get_project_key(project_root) if project_root is not None else None
    active_workspace_root = set_active_data_workspace_root(
        workspace_root,
        workspace_name=request.workspace_name,
        active_project_key=project_key,
        active_project_root=str(project_root) if project_root is not None else _configured_project_root(game_service),
    )
    ensure_data_workspace_layout(
        active_workspace_root,
        workspace_name=request.workspace_name,
        active_project_key=project_key,
        active_project_root=str(project_root) if project_root is not None else _configured_project_root(game_service),
    )
    ensure_default_workspace_agent_profile(game_service.user_config.my_role, workspace_root=active_workspace_root)
    await _reload_loaded_game_services(workspace, game_service)
    workspace_config = load_data_workspace_config(active_workspace_root)
    return {
        'active_workspace_root': str(active_workspace_root),
        'workspace_pointer_path': str(get_workspace_pointer_path()),
        'workspace_config_path': str(get_workspace_config_path(active_workspace_root)),
        'workspace_name': workspace_config.get('workspace_name'),
        'active_project_key': workspace_config.get('active_project_key'),
        'setup_status': _build_setup_status(game_service),
    }


@router.put("/root")
async def save_project_root(
    request: ProjectRootUpdateRequest,
    workspace=Depends(get_agent_for_request),
):
    game_service = _game_service_or_404(workspace)
    project_root = _validate_local_project_root(request.project_root)
    user_config = game_service.user_config
    user_config.svn_local_root = str(project_root)
    save_user_config(user_config)
    active_workspace_root = get_active_data_workspace_root()
    if active_workspace_root is not None:
        save_data_workspace_config(
            active_workspace_root,
            active_project_key=get_project_key(project_root),
            active_project_root=str(project_root),
        )
        ensure_default_workspace_agent_profile(user_config.my_role, workspace_root=active_workspace_root)
    await _reload_loaded_game_services(workspace, game_service)
    return {
        "project_key": get_project_key(project_root),
        "project_bundle_root": str(get_project_bundle_root(project_root)),
        "setup_status": _build_setup_status(game_service),
    }


@router.put("/sources/tables")
async def save_project_tables_source(
    request: ProjectTablesSourceConfigRequest,
    workspace=Depends(get_agent_for_request),
):
    game_service = _game_service_or_404(workspace)
    project_root = _project_root_path(_configured_project_root(game_service))
    if project_root is None:
        raise HTTPException(status_code=400, detail="project_root must be configured before saving table sources")
    if not project_root.exists():
        raise HTTPException(status_code=400, detail=f"project_root does not exist: {project_root}")
    roots = _sanitize_string_list(request.roots)
    if not roots:
        raise HTTPException(status_code=400, detail="roots must not be empty")
    if request.header_row < 1:
        raise HTTPException(status_code=400, detail="header_row must be greater than or equal to 1")
    tables_config = ProjectTablesSourceConfig(
        roots=roots,
        include=_sanitize_string_list(request.include, DEFAULT_TABLES_INCLUDE_PATTERNS),
        exclude=_sanitize_string_list(request.exclude, DEFAULT_TABLES_EXCLUDE_PATTERNS),
        header_row=request.header_row,
        primary_key_candidates=_sanitize_string_list(
            request.primary_key_candidates,
            DEFAULT_TABLES_PRIMARY_KEY_CANDIDATES,
        ),
    )
    save_project_tables_source_config(project_root, tables_config)
    await _reload_loaded_game_services(workspace, game_service)
    return {
        "effective_config": _serialize_tables_config(tables_config),
        "setup_status": _build_setup_status(game_service),
        "config_path": str(get_project_tables_source_path(project_root)),
    }


@router.post("/sources/discover")
async def discover_project_table_sources(workspace=Depends(get_agent_for_request)):
    game_service = _game_service_or_404(workspace)
    project_root = _project_root_path(_configured_project_root(game_service))
    tables_config = _current_tables_config_or_default(game_service)
    return discover_table_sources(project_root, tables_config)


@router.put("/config")
async def save_project_config_api(config: ProjectConfig, workspace=Depends(get_agent_for_request)):
    game_service = _game_service_or_404(workspace)
    user_config = game_service.user_config
    # SVN working copy path: prefer user_config.svn_local_root, fallback to config.svn.root
    svn_local_root = user_config.svn_local_root or config.svn.root
    if not svn_local_root:
        raise HTTPException(
            status_code=400,
            detail="\u672a\u914d\u7f6eSVN\u5de5\u4f5c\u526f\u672c\u8def\u5f84\uff1a\u8bf7\u5728\u201c\u672c\u5730\u5de5\u4f5c\u526f\u672c\u8def\u5f84\u201d\u586b\u5199\u5df2checkout\u7684\u672c\u5730\u76ee\u5f55"
        )
    svn_root = Path(svn_local_root)
    if not svn_root.exists():
        raise HTTPException(
            status_code=400,
            detail=f"\u672c\u5730\u5de5\u4f5c\u526f\u672c\u8def\u5f84\u4e0d\u5b58\u5728: {svn_root}\uff0c\u8bf7\u5148\u8fd0\u884c svn checkout"
        )
    issues = validate_project_config(config)
    errors = [i for i in issues if i.severity == "error"]
    if errors:
        msgs = [f"{i.path}: {i.message}" for i in errors]
        raise HTTPException(status_code=400, detail=f"\u914d\u7f6e\u9a8c\u8bc1\u5931\u8d25: {'; '.join(msgs)}")
    save_project_config(svn_root, config)
    if not user_config.svn_local_root:
        user_config.svn_local_root = str(svn_root)
        save_user_config(user_config)
    await game_service.reload_config()
    return {"message": "\u914d\u7f6e\u4fdd\u5b58\u6210\u529f"}


@router.post("/config/commit")
async def commit_project_config(
    commit_request: dict = None,
    workspace=Depends(get_agent_for_request),
):
    game_service = _game_service_or_404(workspace)
    user_config = game_service.user_config
    config_exists = False
    if user_config.svn_local_root:
        config_exists = get_project_config_path(Path(user_config.svn_local_root)).exists()
    raise HTTPException(
        status_code=409,
        detail={
            "disabled": True,
            "reason": PROJECT_CONFIG_COMMIT_FROZEN_REASON,
            "config_exists": config_exists,
        },
    )


@router.get("/user_config", response_model=UserGameConfig)
async def get_user_config(workspace=Depends(get_agent_for_request)):
    return _game_service_or_404(workspace).user_config


@router.put("/user_config")
async def save_user_config_api(config: UserGameConfig, workspace=Depends(get_agent_for_request)):
    save_user_config(config)
    game_service = _game_service_or_404(workspace)
    await game_service.reload_config()
    return {"message": "\u7528\u6237\u914d\u7f6e\u4fdd\u5b58\u6210\u529f"}


@router.get("/validate", response_model=list[ValidationIssue])
async def validate_config(workspace=Depends(get_agent_for_request)):
    game_service = _game_service_or_404(workspace)
    project_config = game_service.project_config
    if project_config is None:
        return []
    return validate_project_config(project_config)


@router.get("/storage")
async def get_storage_summary_api(workspace=Depends(get_agent_for_request)):
    game_service = _game_service_or_404(workspace)
    svn_root = None
    svn_local_root = getattr(game_service.user_config, "svn_local_root", None)
    if svn_local_root:
        candidate = Path(svn_local_root).expanduser()
        if candidate.exists():
            svn_root = candidate
    elif game_service.project_config is not None:
        configured_root = str(game_service.project_config.svn.root or "").strip()
        if configured_root and "://" not in configured_root:
            candidate = Path(configured_root).expanduser()
            if candidate.exists():
                svn_root = candidate
    workspace_dir = Path(getattr(workspace, "workspace_dir", "."))
    return get_storage_summary(workspace_dir, svn_root=svn_root)


@router.delete("/config")
async def delete_project_config(workspace=Depends(get_agent_for_request)):
    game_service = _game_service_or_404(workspace)
    user_config = game_service.user_config
    if user_config.my_role != "maintainer":
        raise HTTPException(status_code=403, detail="Only maintainers can delete project config")
    if not user_config.svn_local_root:
        raise HTTPException(status_code=400, detail="SVN root not configured")
    svn_root = Path(user_config.svn_local_root)
    config_path = get_project_config_path(svn_root)
    if config_path.exists():
        config_path.unlink()
    await game_service.reload_config()
    return {"message": "\u9879\u76ee\u914d\u7f6e\u5df2\u5220\u9664"}