from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...game.knowledge_release_query import query_current_release
from ..capabilities import require_capability
from ..agent_context import get_agent_for_request


router = APIRouter(prefix='/game/knowledge', tags=['game-knowledge-query'])


class KnowledgeQueryRequest(BaseModel):
    query: str = Field(default='')
    top_k: int = Field(default=10, ge=1, le=50)
    mode: str = Field(default='hybrid')


class KnowledgeQueryResultItem(BaseModel):
    source_type: str
    source_path: str
    release_id: str
    built_at: datetime
    score: float
    title: str | None = None
    summary: str | None = None
    table_name: str | None = None
    system: str | None = None
    primary_key: str | None = None
    row_count: int | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    language: str | None = None
    kind: str | None = None


class KnowledgeQueryResponse(BaseModel):
    mode: str
    query: str
    top_k: int
    release_id: str | None = None
    built_at: datetime | None = None
    results: list[KnowledgeQueryResultItem] = Field(default_factory=list)
    count: int = 0


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


@router.post('/query', response_model=KnowledgeQueryResponse)
async def query_knowledge(request: Request, body: KnowledgeQueryRequest) -> KnowledgeQueryResponse:
    require_capability(request, 'knowledge.read')
    workspace = await get_agent_for_request(request)
    game_service = _game_service_or_404(workspace)
    payload = query_current_release(
        _project_root_or_400(game_service),
        body.query,
        top_k=body.top_k,
        mode=body.mode,
    )
    return KnowledgeQueryResponse.model_validate(payload)
