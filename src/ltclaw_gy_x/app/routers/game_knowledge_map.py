from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...game.knowledge_formal_map_store import (
    FormalKnowledgeMapStoreError,
    load_formal_knowledge_map,
    save_formal_knowledge_map,
)
from ...game.knowledge_map_candidate import (
    build_map_candidate_from_canonical_facts,
    build_map_candidate_result_from_release,
    build_map_diff_review,
    resolve_map_diff_base,
)
from ...game.knowledge_release_store import CurrentKnowledgeReleaseNotSetError
from ...game.models import KnowledgeMap, KnowledgeMapCandidateResult
from ..capabilities import require_capability
from ..agent_context import get_agent_for_request


router = APIRouter(prefix='/game/knowledge/map', tags=['game-knowledge-map'])


class BuildSourceCandidateRequest(BaseModel):
    use_existing_formal_map_as_hint: bool = Field(default=True)


class FormalKnowledgeMapResponse(BaseModel):
    mode: str
    map: KnowledgeMap | None = None
    map_hash: str | None = None
    updated_at: datetime | None = None
    updated_by: str | None = None


class SaveFormalKnowledgeMapRequest(BaseModel):
    knowledge_map: KnowledgeMap | None = Field(default=None, alias='map')
    updated_by: str | None = None

    model_config = {'populate_by_name': True}


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


@router.get('/candidate', response_model=KnowledgeMapCandidateResult)
async def get_map_candidate(request: Request, release_id: str | None = None) -> KnowledgeMapCandidateResult:
    workspace = await get_agent_for_request(request)
    require_capability(request, 'knowledge.candidate.read')
    project_root = _project_root_or_400(_game_service_or_404(workspace))
    try:
        candidate = build_map_candidate_result_from_release(project_root, release_id=release_id)
    except CurrentKnowledgeReleaseNotSetError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return candidate


@router.post('/candidate/from-source', response_model=KnowledgeMapCandidateResult)
async def build_map_candidate_from_source(
    request: Request,
    body: BuildSourceCandidateRequest,
) -> KnowledgeMapCandidateResult:
    workspace = await get_agent_for_request(request)
    require_capability(request, 'knowledge.candidate.write')
    project_root = _project_root_or_400(_game_service_or_404(workspace))

    existing_formal_map = None
    if body.use_existing_formal_map_as_hint:
        record = load_formal_knowledge_map(project_root)
        if record is not None:
            existing_formal_map = record.knowledge_map

    candidate = build_map_candidate_from_canonical_facts(
        project_root,
        existing_formal_map=existing_formal_map,
    )
    if candidate.map is not None:
        diff_base, base_map_source = resolve_map_diff_base(project_root, existing_formal_map=existing_formal_map)
        candidate.diff_review = build_map_diff_review(
            diff_base,
            candidate.map,
            candidate_source=candidate.candidate_source,
            base_map_source=base_map_source,
            warnings=candidate.warnings,
        )
    return candidate


@router.get('', response_model=FormalKnowledgeMapResponse)
async def get_formal_map(request: Request) -> FormalKnowledgeMapResponse:
    workspace = await get_agent_for_request(request)
    require_capability(request, 'knowledge.map.read')
    project_root = _project_root_or_400(_game_service_or_404(workspace))
    record = load_formal_knowledge_map(project_root)
    if record is None:
        return FormalKnowledgeMapResponse(mode='no_formal_map')
    return FormalKnowledgeMapResponse(
        mode='formal_map',
        map=record.knowledge_map,
        map_hash=record.map_hash,
        updated_at=record.updated_at,
        updated_by=record.updated_by,
    )


@router.put('', response_model=FormalKnowledgeMapResponse)
async def put_formal_map(request: Request, body: SaveFormalKnowledgeMapRequest) -> FormalKnowledgeMapResponse:
    workspace = await get_agent_for_request(request)
    require_capability(request, 'knowledge.map.edit')
    project_root = _project_root_or_400(_game_service_or_404(workspace))
    if body.knowledge_map is None:
        raise HTTPException(status_code=422, detail='map is required')
    try:
        record = save_formal_knowledge_map(project_root, body.knowledge_map, updated_by=body.updated_by)
    except (FormalKnowledgeMapStoreError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return FormalKnowledgeMapResponse(
        mode='formal_map_saved',
        map=record.knowledge_map,
        map_hash=record.map_hash,
        updated_at=record.updated_at,
        updated_by=record.updated_by,
    )
