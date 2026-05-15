from __future__ import annotations

import json
import os
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
from ...game.cold_start_job import (
    ColdStartJobCreateResponse,
    ColdStartJobState,
    cancel_cold_start_job,
    create_or_get_cold_start_job,
    load_cold_start_job_with_stale_check,
)
from ...game.knowledge_map_candidate import (
    build_map_candidate_from_canonical_facts,
    build_map_candidate_result_from_release,
    build_map_diff_review,
    resolve_map_diff_base,
)
from ...game.knowledge_release_store import CurrentKnowledgeReleaseNotSetError
from ...game.models import CanonicalTableSchema, KnowledgeMap, KnowledgeMapCandidateResult
from ...game.config import load_project_tables_source_config
from ...game.paths import (
    get_project_bundle_root,
    get_project_canonical_tables_dir,
    get_project_current_release_path,
    get_project_formal_map_canonical_path,
    get_project_raw_table_indexes_path,
    get_project_raw_tables_dir,
    get_project_source_config_path,
    get_project_tables_source_path,
)
from ...game.source_discovery import discover_table_sources
from ..capabilities import require_capability
from ..agent_context import get_agent_for_request


router = APIRouter(prefix='/game/knowledge/map', tags=['game-knowledge-map'])


class BuildSourceCandidateRequest(BaseModel):
    use_existing_formal_map_as_hint: bool = Field(default=True)


class BuildReadinessResponse(BaseModel):
    project_root: str | None = None
    project_bundle_root: str | None = None
    source_config_exists: bool = False
    tables_config_exists: bool = False
    discovered_table_count: int = 0
    raw_table_index_count: int = 0
    canonical_table_count: int = 0
    has_formal_map: bool = False
    has_current_release: bool = False
    blocking_reason: str
    next_action: str
    raw_tables_dir: str | None = None
    canonical_tables_dir: str | None = None
    candidate_read_dir: str | None = None
    same_project_bundle: bool = False


class CandidateDiagnostics(BaseModel):
    raw_table_index_count: int
    canonical_table_count: int
    canonical_tables_dir: str
    blocking_reason: str
    next_action: str


class SourceCandidateResponse(KnowledgeMapCandidateResult):
    diagnostics: CandidateDiagnostics | None = None
    candidate_table_count: int | None = None
    candidate_refs: list[str] = Field(default_factory=list)


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


class CreateColdStartJobRequest(BaseModel):
    timeout_seconds: int = Field(default=300, ge=1, le=3600)


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


def _candidate_read_dir(project_root: Path) -> Path:
    return get_project_canonical_tables_dir(project_root)


def _count_raw_table_indexes(project_root: Path) -> int:
    raw_indexes_path = get_project_raw_table_indexes_path(project_root)
    if not raw_indexes_path.exists():
        return 0
    try:
        payload = json.loads(raw_indexes_path.read_text(encoding='utf-8'))
    except Exception:
        return 0
    tables = payload.get('tables') if isinstance(payload, dict) else None
    return len(tables) if isinstance(tables, list) else 0


def _count_valid_canonical_tables(canonical_tables_dir: Path) -> int:
    if not canonical_tables_dir.exists() or not canonical_tables_dir.is_dir():
        return 0
    count = 0
    for candidate in canonical_tables_dir.glob('*.json'):
        try:
            CanonicalTableSchema.model_validate_json(candidate.read_text(encoding='utf-8'))
        except Exception:
            continue
        count += 1
    return count


def _discover_table_count(project_root: Path, tables_config_exists: bool) -> int:
    if not tables_config_exists:
        return 0
    tables_config = load_project_tables_source_config(project_root)
    if tables_config is None:
        return 0
    discovery = discover_table_sources(project_root, tables_config)
    return sum(1 for item in discovery['table_files'] if item.get('status') == 'available')


def _is_same_project_bundle(project_bundle_root: Path, candidate_read_dir: Path) -> bool:
    bundle_root = project_bundle_root.resolve(strict=False)
    read_dir = candidate_read_dir.resolve(strict=False)
    try:
        return os.path.commonpath([str(bundle_root), str(read_dir)]) == str(bundle_root)
    except ValueError:
        return False


def _readiness_reason_and_action(
    *,
    project_root_exists: bool,
    same_project_bundle: bool,
    tables_config_exists: bool,
    discovered_table_count: int,
    raw_table_index_count: int,
    canonical_table_count: int,
    has_formal_map: bool,
    has_current_release: bool,
) -> tuple[str, str]:
    if not project_root_exists:
        return 'project_root_missing', 'set_project_root'
    if not same_project_bundle:
        return 'path_mismatch', 'inspect_candidate_read_dir'
    if not tables_config_exists:
        return 'tables_source_missing', 'configure_tables_source'
    if discovered_table_count <= 0:
        return 'no_table_sources_found', 'run_source_discovery'
    if raw_table_index_count <= 0:
        return 'no_raw_indexes', 'run_raw_index_rebuild'
    if canonical_table_count <= 0:
        return 'no_canonical_facts', 'run_canonical_rebuild'
    if not has_formal_map:
        return 'candidate_ready', 'build_candidate_from_source'
    if not has_current_release:
        return 'release_missing', 'build_release'
    return 'ready', 'ready'


def _build_readiness_payload(project_root: Path | None) -> BuildReadinessResponse:
    if project_root is None or not project_root.exists():
        return BuildReadinessResponse(
            project_root=str(project_root) if project_root is not None else None,
            blocking_reason='project_root_missing',
            next_action='set_project_root',
        )

    project_bundle_root = get_project_bundle_root(project_root)
    source_config_exists = get_project_source_config_path(project_root).exists()
    tables_config_exists = get_project_tables_source_path(project_root).exists()
    discovered_table_count = _discover_table_count(project_root, tables_config_exists)
    raw_table_index_count = _count_raw_table_indexes(project_root)
    raw_tables_dir = get_project_raw_tables_dir(project_root)
    canonical_tables_dir = get_project_canonical_tables_dir(project_root)
    canonical_table_count = _count_valid_canonical_tables(canonical_tables_dir)
    has_formal_map = get_project_formal_map_canonical_path(project_root).exists()
    has_current_release = get_project_current_release_path(project_root).exists()
    candidate_read_dir = _candidate_read_dir(project_root)
    same_project_bundle = _is_same_project_bundle(project_bundle_root, candidate_read_dir)
    blocking_reason, next_action = _readiness_reason_and_action(
        project_root_exists=True,
        same_project_bundle=same_project_bundle,
        tables_config_exists=tables_config_exists,
        discovered_table_count=discovered_table_count,
        raw_table_index_count=raw_table_index_count,
        canonical_table_count=canonical_table_count,
        has_formal_map=has_formal_map,
        has_current_release=has_current_release,
    )
    return BuildReadinessResponse(
        project_root=str(project_root),
        project_bundle_root=str(project_bundle_root),
        source_config_exists=source_config_exists,
        tables_config_exists=tables_config_exists,
        discovered_table_count=discovered_table_count,
        raw_table_index_count=raw_table_index_count,
        canonical_table_count=canonical_table_count,
        has_formal_map=has_formal_map,
        has_current_release=has_current_release,
        blocking_reason=blocking_reason,
        next_action=next_action,
        raw_tables_dir=str(raw_tables_dir),
        canonical_tables_dir=str(canonical_tables_dir),
        candidate_read_dir=str(candidate_read_dir),
        same_project_bundle=same_project_bundle,
    )


def _candidate_refs(candidate_map: KnowledgeMap | None) -> list[str]:
    if candidate_map is None:
        return []
    refs = [f'table:{table.table_id}' for table in candidate_map.tables]
    refs.extend(f'doc:{doc.doc_id}' for doc in candidate_map.docs)
    refs.extend(f'script:{script.script_id}' for script in candidate_map.scripts)
    refs.extend(f'system:{system.system_id}' for system in candidate_map.systems)
    return sorted(refs)


def _serialize_source_candidate_response(
    candidate: KnowledgeMapCandidateResult,
    *,
    diagnostics: CandidateDiagnostics | None = None,
) -> SourceCandidateResponse:
    return SourceCandidateResponse(
        **candidate.model_dump(mode='json'),
        diagnostics=diagnostics,
        candidate_table_count=(len(candidate.map.tables) if candidate.map is not None else None),
        candidate_refs=_candidate_refs(candidate.map),
    )


@router.get('/build-readiness', response_model=BuildReadinessResponse)
async def get_build_readiness(request: Request) -> BuildReadinessResponse:
    workspace = await get_agent_for_request(request)
    require_capability(request, 'knowledge.candidate.read')
    project_root = _project_root_or_none(_game_service_or_404(workspace))
    return _build_readiness_payload(project_root)


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


@router.post('/candidate/from-source', response_model=SourceCandidateResponse)
async def build_map_candidate_from_source(
    request: Request,
    body: BuildSourceCandidateRequest,
) -> SourceCandidateResponse:
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
    if candidate.mode == 'no_canonical_facts':
        readiness = _build_readiness_payload(project_root)
        diagnostics = CandidateDiagnostics(
            raw_table_index_count=readiness.raw_table_index_count,
            canonical_table_count=readiness.canonical_table_count,
            canonical_tables_dir=readiness.canonical_tables_dir or '',
            blocking_reason=readiness.blocking_reason,
            next_action=readiness.next_action,
        )
        return _serialize_source_candidate_response(candidate, diagnostics=diagnostics)
    if candidate.map is not None:
        diff_base, base_map_source = resolve_map_diff_base(project_root, existing_formal_map=existing_formal_map)
        candidate.diff_review = build_map_diff_review(
            diff_base,
            candidate.map,
            candidate_source=candidate.candidate_source,
            base_map_source=base_map_source,
            warnings=candidate.warnings,
        )
    return _serialize_source_candidate_response(candidate)


@router.post('/cold-start-jobs', response_model=ColdStartJobCreateResponse)
async def create_cold_start_job(request: Request, body: CreateColdStartJobRequest) -> ColdStartJobCreateResponse:
    workspace = await get_agent_for_request(request)
    require_capability(request, 'knowledge.candidate.write')
    project_root = _project_root_or_400(_game_service_or_404(workspace))
    job, reused_existing = create_or_get_cold_start_job(project_root, timeout_seconds=body.timeout_seconds)
    return ColdStartJobCreateResponse(reused_existing=reused_existing, job=job)


@router.get('/cold-start-jobs/{job_id}', response_model=ColdStartJobState)
async def get_cold_start_job(request: Request, job_id: str) -> ColdStartJobState:
    workspace = await get_agent_for_request(request)
    require_capability(request, 'knowledge.candidate.read')
    project_root = _project_root_or_400(_game_service_or_404(workspace))
    job = load_cold_start_job_with_stale_check(project_root, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail='Cold-start job not found')
    return job


@router.post('/cold-start-jobs/{job_id}/cancel', response_model=ColdStartJobState)
async def cancel_cold_start_job_route(request: Request, job_id: str) -> ColdStartJobState:
    workspace = await get_agent_for_request(request)
    require_capability(request, 'knowledge.candidate.write')
    project_root = _project_root_or_400(_game_service_or_404(workspace))
    job = cancel_cold_start_job(project_root, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail='Cold-start job not found')
    return job


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
