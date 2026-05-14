from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...game.canonical_facts_committer import CanonicalCommitError, CanonicalFactsCommitter
from ..agent_context import get_agent_for_request
from ..capabilities import require_capability


router = APIRouter(prefix='/game/knowledge/canonical', tags=['game-knowledge-canonical'])


class CanonicalRebuildRequest(BaseModel):
    scope: str = Field(default='tables')
    rule_only: bool = Field(default=True)
    force: bool = Field(default=False)


class CanonicalRebuildError(BaseModel):
    raw_index_file: str
    error: str
    table_id: str | None = None


class CanonicalRebuildResponse(BaseModel):
    success: bool
    raw_table_index_count: int
    canonical_table_count: int
    written: list[str] = Field(default_factory=list)
    errors: list[CanonicalRebuildError] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    next_action: str


def _game_service_or_404(workspace):
    svc = getattr(workspace, 'game_service', None)
    if svc is None and hasattr(workspace, 'service_manager'):
        svc = workspace.service_manager.services.get('game_service')
    if svc is None:
        raise HTTPException(status_code=404, detail='Game service not available')
    return svc


def _project_root_or_400(game_service) -> Path:
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

    raise HTTPException(status_code=400, detail='Local project directory not configured')


def _serialize_errors(errors: list[CanonicalCommitError]) -> list[CanonicalRebuildError]:
    return [
        CanonicalRebuildError(
            raw_index_file=item.raw_index_file,
            table_id=item.table_id,
            error=item.error,
        )
        for item in errors
    ]


@router.post('/rebuild', response_model=CanonicalRebuildResponse)
async def rebuild_canonical(request: Request, body: CanonicalRebuildRequest) -> CanonicalRebuildResponse:
    if body.scope != 'tables':
        raise HTTPException(status_code=400, detail='Only scope=tables is supported')
    if not body.rule_only:
        raise HTTPException(status_code=400, detail='Only rule_only=true is supported')

    workspace = await get_agent_for_request(request)
    require_capability(request, 'knowledge.build')
    game_service = _game_service_or_404(workspace)
    project_root = _project_root_or_400(game_service)

    result = CanonicalFactsCommitter(project_root).rebuild_tables(force=body.force)
    return CanonicalRebuildResponse(
        success=not result.errors,
        raw_table_index_count=result.raw_table_index_count,
        canonical_table_count=result.canonical_table_count,
        written=result.written,
        errors=_serialize_errors(result.errors),
        warnings=result.warnings,
        next_action='build_candidate_from_source',
    )