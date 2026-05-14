from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from ...game.knowledge_test_plan_store import (
    KnowledgeTestPlanRecordError,
    KnowledgeTestPlanValidationError,
    append_test_plan,
    list_test_plans,
)
from ...game.models import WorkbenchTestPlan
from ..agent_context import get_agent_for_request
from ..capabilities import require_capability


router = APIRouter(prefix='/game/knowledge/test-plans', tags=['game-knowledge-test-plans'])


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


@router.post('', response_model=WorkbenchTestPlan)
async def create_test_plan(request: Request, body: WorkbenchTestPlan) -> WorkbenchTestPlan:
    workspace = await get_agent_for_request(request)
    require_capability(request, 'workbench.test.write')
    game_service = _game_service_or_404(workspace)
    try:
        return append_test_plan(_project_root_or_400(game_service), body)
    except KnowledgeTestPlanValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('', response_model=list[WorkbenchTestPlan])
async def get_test_plans(request: Request) -> list[WorkbenchTestPlan]:
    workspace = await get_agent_for_request(request)
    require_capability(request, 'workbench.read')
    game_service = _game_service_or_404(workspace)
    try:
        return list_test_plans(_project_root_or_400(game_service))
    except KnowledgeTestPlanRecordError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
