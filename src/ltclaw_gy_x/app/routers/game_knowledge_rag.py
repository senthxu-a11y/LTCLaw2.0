from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...game.knowledge_rag_answer import (
    RagAnswerConfigGenerationChangedError,
    build_rag_answer_with_service_config,
)
from ...game.knowledge_rag_context import build_current_release_context
from ..capabilities import require_capability
from ..agent_context import get_agent_for_request


router = APIRouter(prefix='/game/knowledge/rag', tags=['game-knowledge-rag'])

_CONFIG_RELOAD_SETTLING_WARNING = (
    'RAG answer config changed repeatedly during request. External transport was skipped until reload settles.'
)


class RagRequest(BaseModel):
    query: str = Field(default='')
    max_chunks: int = Field(default=8, ge=1, le=20)
    max_chars: int = Field(default=12000, ge=1000, le=50000)
    focus_refs: list[str] = Field(default_factory=list)


class RagContextResponse(BaseModel):
    mode: str
    query: str
    release_id: str | None = None
    built_at: datetime | None = None
    chunks: list[dict[str, Any]] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    allowed_refs: list[str] = Field(default_factory=list)
    map_hash: str | None = None
    map_source_hash: str | None = None
    reason: str | None = None


class RagAnswerResponse(BaseModel):
    mode: str
    answer: str = ''
    release_id: str | None = None
    citations: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


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


def _config_generation(game_service) -> int:
    try:
        return int(getattr(game_service, 'config_generation', 0) or 0)
    except Exception:
        return 0


def _build_answer_context(game_service, body: RagRequest) -> dict[str, Any]:
    kwargs = {
        'max_chunks': body.max_chunks,
        'max_chars': body.max_chars,
    }
    if body.focus_refs:
        kwargs['focus_refs'] = body.focus_refs
    return build_current_release_context(_project_root_or_400(game_service), body.query, **kwargs)


def _settle_answer_context(game_service, body: RagRequest) -> tuple[dict[str, Any], int | None]:
    generation_before = _config_generation(game_service)
    context = _build_answer_context(game_service, body)
    generation_after = _config_generation(game_service)
    if generation_after == generation_before:
        return context, generation_after

    context = _build_answer_context(game_service, body)
    generation_after_reread = _config_generation(game_service)
    if generation_after_reread != generation_after:
        return context, None

    return context, generation_after_reread


def _fail_closed_answer(context: dict[str, Any]) -> RagAnswerResponse:
    return RagAnswerResponse(
        mode='insufficient_context',
        answer='',
        release_id=context.get('release_id'),
        citations=[],
        warnings=[_CONFIG_RELOAD_SETTLING_WARNING],
    )


@router.post('/context', response_model=RagContextResponse)
async def rag_context(request: Request, body: RagRequest) -> RagContextResponse:
    workspace = await get_agent_for_request(request)
    require_capability(request, 'knowledge.read')
    kwargs = {
        'max_chunks': body.max_chunks,
        'max_chars': body.max_chars,
    }
    if body.focus_refs:
        kwargs['focus_refs'] = body.focus_refs
    payload = build_current_release_context(_project_root_or_400(_game_service_or_404(workspace)), body.query, **kwargs)
    return RagContextResponse.model_validate(payload)


@router.post('/answer', response_model=RagAnswerResponse)
async def rag_answer(request: Request, body: RagRequest) -> RagAnswerResponse:
    workspace = await get_agent_for_request(request)
    require_capability(request, 'knowledge.read')
    game_service = _game_service_or_404(workspace)

    context, expected_generation = _settle_answer_context(game_service, body)
    if expected_generation is None:
        return _fail_closed_answer(context)

    try:
        payload = build_rag_answer_with_service_config(
            body.query,
            context,
            game_service,
            expected_generation=expected_generation,
        )
    except RagAnswerConfigGenerationChangedError:
        context, expected_generation = _settle_answer_context(game_service, body)
        if expected_generation is None:
            return _fail_closed_answer(context)
        try:
            payload = build_rag_answer_with_service_config(
                body.query,
                context,
                game_service,
                expected_generation=expected_generation,
            )
        except RagAnswerConfigGenerationChangedError:
            return _fail_closed_answer(context)

    return RagAnswerResponse.model_validate(payload)
