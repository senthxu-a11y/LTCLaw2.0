from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request

from ...game.knowledge_release_candidate_store import (
    KnowledgeReleaseCandidateRecordError,
    KnowledgeReleaseCandidateValidationError,
    append_release_candidate,
    list_release_candidates,
)
from ...game.models import ReleaseCandidate
from ..agent_context import get_agent_for_request
from ..capabilities import require_capability


router = APIRouter(prefix='/game/knowledge/release-candidates', tags=['game-knowledge-release-candidates'])


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


@router.post('', response_model=ReleaseCandidate)
async def create_release_candidate(request: Request, body: ReleaseCandidate) -> ReleaseCandidate:
    require_capability(request, 'knowledge.candidate.write')
    workspace = await get_agent_for_request(request)
    game_service = _game_service_or_404(workspace)
    try:
        return append_release_candidate(_project_root_or_400(game_service), body)
    except KnowledgeReleaseCandidateValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('', response_model=list[ReleaseCandidate])
async def get_release_candidates(
    request: Request,
    status: str | None = Query(default=None),
    selected: bool | None = Query(default=None),
    test_plan_id: str | None = Query(default=None),
) -> list[ReleaseCandidate]:
    require_capability(request, 'knowledge.candidate.read')
    workspace = await get_agent_for_request(request)
    game_service = _game_service_or_404(workspace)
    try:
        return list_release_candidates(
            _project_root_or_400(game_service),
            status=status,
            selected=selected,
            test_plan_id=test_plan_id,
        )
    except KnowledgeReleaseCandidateValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KnowledgeReleaseCandidateRecordError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
