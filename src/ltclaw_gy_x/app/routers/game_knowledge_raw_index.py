from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...game.config import ProjectTablesSourceConfig, load_project_tables_source_config
from ...game.raw_index_rebuild import rebuild_raw_table_indexes
from ..agent_context import get_agent_for_request
from ..capabilities import require_capability


router = APIRouter(prefix='/game/knowledge/raw-index', tags=['game-knowledge-raw-index'])


class RawIndexRebuildRequest(BaseModel):
    scope: str = Field(default='tables')
    rule_only: bool = Field(default=True)


class RawIndexRebuildTableSummary(BaseModel):
    table_id: str
    source_path: str
    row_count: int
    field_count: int
    primary_key: str


class RawIndexRebuildError(BaseModel):
    source_path: str | None = None
    error: str


class RawIndexRebuildResponse(BaseModel):
    success: bool
    raw_table_index_count: int
    indexed_tables: list[RawIndexRebuildTableSummary] = Field(default_factory=list)
    errors: list[RawIndexRebuildError] = Field(default_factory=list)
    next_action: str


def _game_service_or_404(workspace):
    svc = getattr(workspace, 'game_service', None)
    if svc is None and hasattr(workspace, 'service_manager'):
        svc = workspace.service_manager.services.get('game_service')
    if svc is None:
        raise HTTPException(status_code=404, detail='Game service not available')
    return svc


def _project_root_or_none(game_service) -> Path | None:
    runtime_root = getattr(game_service, '_runtime_svn_root', None)
    if callable(runtime_root):
        root = runtime_root()
        if root is not None:
            return Path(root)

    user_config = getattr(game_service, 'user_config', None)
    local_root = getattr(user_config, 'svn_local_root', None)
    if local_root:
        return Path(local_root).expanduser()

    project_config = getattr(game_service, 'project_config', None)
    svn_config = getattr(project_config, 'svn', None)
    project_root = getattr(svn_config, 'root', None)
    if project_root and '://' not in str(project_root):
        return Path(project_root).expanduser()
    return None


def _serialize_response(payload: dict) -> RawIndexRebuildResponse:
    return RawIndexRebuildResponse(
        success=payload['success'],
        raw_table_index_count=payload['raw_table_index_count'],
        indexed_tables=[RawIndexRebuildTableSummary(**item) for item in payload['indexed_tables']],
        errors=[RawIndexRebuildError(**item) for item in payload['errors']],
        next_action=payload['next_action'],
    )


@router.post('/rebuild', response_model=RawIndexRebuildResponse)
async def rebuild_raw_index(request: Request, body: RawIndexRebuildRequest) -> RawIndexRebuildResponse:
    if body.scope != 'tables':
        raise HTTPException(status_code=400, detail='Only scope=tables is supported')
    if not body.rule_only:
        raise HTTPException(status_code=400, detail='Only rule_only=true is supported')

    workspace = await get_agent_for_request(request)
    require_capability(request, 'knowledge.build')
    game_service = _game_service_or_404(workspace)
    project_root = _project_root_or_none(game_service)
    tables_config = (
        load_project_tables_source_config(project_root)
        if project_root is not None and project_root.exists()
        else ProjectTablesSourceConfig()
    )
    payload = await rebuild_raw_table_indexes(project_root, tables_config)
    return _serialize_response(payload)