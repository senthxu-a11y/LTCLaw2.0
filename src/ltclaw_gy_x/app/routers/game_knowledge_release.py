from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...game.knowledge_release_service import (
    KnowledgeProjectRootNotFoundError,
    KnowledgeReleasePrerequisiteError,
    build_knowledge_release,
    build_knowledge_release_from_current_indexes,
)
from ...game.knowledge_release_store import (
    CurrentKnowledgeReleaseNotSetError,
    KnowledgeReleaseNotFoundError,
    get_current_release,
    list_releases,
    load_manifest,
    set_current_release,
)
from ...game.models import (
    CodeFileIndex,
    DocIndex,
    KnowledgeDocRef,
    KnowledgeIndexArtifact,
    KnowledgeManifest,
    KnowledgeMap,
    KnowledgeReleasePointer,
    TableIndex,
)
from ..agent_context import get_agent_for_request


router = APIRouter(prefix='/game/knowledge/releases', tags=['game-knowledge-release'])


class BuildKnowledgeReleaseRequest(BaseModel):
    release_id: str = Field(description='Knowledge release id')
    knowledge_map: KnowledgeMap
    table_indexes: list[TableIndex] = Field(default_factory=list)
    doc_indexes: list[DocIndex] = Field(default_factory=list)
    code_indexes: list[CodeFileIndex] = Field(default_factory=list)
    knowledge_docs: list[KnowledgeDocRef] = Field(default_factory=list)
    created_by: str | None = Field(default=None)
    created_at: datetime | None = Field(default=None)
    release_notes: str = Field(default='')


class BuildKnowledgeReleaseResponse(BaseModel):
    release_dir: str
    manifest: KnowledgeManifest
    knowledge_map: KnowledgeMap
    artifacts: dict[str, KnowledgeIndexArtifact]


class BuildKnowledgeReleaseFromCurrentIndexesRequest(BaseModel):
    release_id: str = Field(description='Knowledge release id')
    release_notes: str = Field(default='')
    candidate_ids: list[str] = Field(default_factory=list)
    created_by: str | None = Field(default=None)
    created_at: datetime | None = Field(default=None)


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


@router.post('/build', response_model=BuildKnowledgeReleaseResponse)
async def build_release(request: Request, body: BuildKnowledgeReleaseRequest) -> BuildKnowledgeReleaseResponse:
    workspace = await get_agent_for_request(request)
    game_service = _game_service_or_404(workspace)
    project_root = _project_root_or_400(game_service)

    try:
        result = build_knowledge_release(
            project_root,
            body.release_id,
            body.knowledge_map,
            table_indexes=body.table_indexes,
            doc_indexes=body.doc_indexes,
            code_indexes=body.code_indexes,
            knowledge_docs=body.knowledge_docs,
            created_by=body.created_by,
            created_at=body.created_at,
            release_notes=body.release_notes,
        )
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except KnowledgeProjectRootNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return BuildKnowledgeReleaseResponse(
        release_dir=str(result.release_dir),
        manifest=result.manifest,
        knowledge_map=result.knowledge_map,
        artifacts=result.artifacts,
    )


@router.post('/build-from-current-indexes', response_model=BuildKnowledgeReleaseResponse)
async def build_release_from_current_indexes(
    request: Request,
    body: BuildKnowledgeReleaseFromCurrentIndexesRequest,
) -> BuildKnowledgeReleaseResponse:
    workspace = await get_agent_for_request(request)
    game_service = _game_service_or_404(workspace)
    project_root = _project_root_or_400(game_service)

    try:
        result = build_knowledge_release_from_current_indexes(
            project_root,
            getattr(workspace, 'workspace_dir', None) or project_root,
            body.release_id,
            candidate_ids=body.candidate_ids,
            created_by=body.created_by,
            created_at=body.created_at,
            release_notes=body.release_notes,
        )
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except KnowledgeProjectRootNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (KnowledgeReleasePrerequisiteError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return BuildKnowledgeReleaseResponse(
        release_dir=str(result.release_dir),
        manifest=result.manifest,
        knowledge_map=result.knowledge_map,
        artifacts=result.artifacts,
    )


@router.get('', response_model=list[KnowledgeManifest])
async def list_release_manifests(request: Request) -> list[KnowledgeManifest]:
    workspace = await get_agent_for_request(request)
    game_service = _game_service_or_404(workspace)
    return list_releases(_project_root_or_400(game_service))


@router.get('/current', response_model=KnowledgeManifest)
async def get_current_release_manifest(request: Request) -> KnowledgeManifest:
    workspace = await get_agent_for_request(request)
    game_service = _game_service_or_404(workspace)
    try:
        return get_current_release(_project_root_or_400(game_service))
    except CurrentKnowledgeReleaseNotSetError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except KnowledgeReleaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post('/{release_id}/current', response_model=KnowledgeReleasePointer)
async def set_current_release_manifest(release_id: str, request: Request) -> KnowledgeReleasePointer:
    workspace = await get_agent_for_request(request)
    game_service = _game_service_or_404(workspace)
    try:
        return set_current_release(_project_root_or_400(game_service), release_id)
    except KnowledgeReleaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/{release_id}/manifest', response_model=KnowledgeManifest)
async def get_release_manifest(release_id: str, request: Request) -> KnowledgeManifest:
    workspace = await get_agent_for_request(request)
    game_service = _game_service_or_404(workspace)
    try:
        return load_manifest(_project_root_or_400(game_service), release_id)
    except KnowledgeReleaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc