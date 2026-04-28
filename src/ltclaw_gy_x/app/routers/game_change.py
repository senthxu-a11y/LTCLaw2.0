# -*- coding: utf-8 -*-
"""Game change proposal HTTP API endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...app.agent_context import get_agent_for_request
from ...app.workspace.workspace import Workspace
from ...game.change_proposal import (
    ChangeOp,
    ChangeProposal,
    InvalidProposalState,
)


class ChangeProposalCreate(BaseModel):
    title: str
    description: str = ""
    ops: list[dict[str, Any]]


router = APIRouter(prefix="/game/change", tags=["game-change"])


def _service(workspace: Workspace):
    svc = workspace.service_manager.services.get("game_service")
    if svc is None:
        raise HTTPException(status_code=404, detail="Game service not available")
    return svc


def _require_maintainer(svc) -> None:
    if svc.user_config.my_role != "maintainer":
        raise HTTPException(status_code=403, detail="Only maintainers can perform this action")


def _proposal_store(svc):
    store = getattr(svc, "proposal_store", None)
    if store is None:
        raise HTTPException(status_code=404, detail="Proposal store not available")
    return store


async def _proposal_or_404(store, proposal_id: str) -> ChangeProposal:
    proposal = await store.get(proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail=f"Proposal '{proposal_id}' not found")
    return proposal


def _relative_changed_files(svc, proposal: ChangeProposal) -> list[str]:
    applier = getattr(svc, "change_applier", None)
    if applier is None:
        raise HTTPException(status_code=412, detail="Change applier not available")
    grouped = applier._group_ops_by_file(proposal.ops)
    return [
        str(path.relative_to(applier.svn_root)).replace("\\", "/")
        for path in grouped.keys()
    ]


@router.post("/proposals")
async def create_proposal(
    body: ChangeProposalCreate,
    workspace: Workspace = Depends(get_agent_for_request),
):
    svc = _service(workspace)
    store = _proposal_store(svc)
    proposal = ChangeProposal(
        title=body.title,
        description=body.description,
        ops=[ChangeOp.model_validate(op) for op in body.ops],
        status="draft",
    )
    created = await store.create(proposal)
    return created.model_dump(mode="json")


@router.get("/proposals")
async def list_proposals(
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    workspace: Workspace = Depends(get_agent_for_request),
):
    svc = _service(workspace)
    store = _proposal_store(svc)
    proposals = await store.list(status=status, limit=limit)
    return [proposal.model_dump(mode="json") for proposal in proposals]


@router.get("/proposals/{proposal_id}")
async def get_proposal(
    proposal_id: str,
    workspace: Workspace = Depends(get_agent_for_request),
):
    svc = _service(workspace)
    store = _proposal_store(svc)
    proposal = await _proposal_or_404(store, proposal_id)
    return proposal.model_dump(mode="json")


@router.post("/proposals/{proposal_id}/dry_run")
async def dry_run_proposal(
    proposal_id: str,
    workspace: Workspace = Depends(get_agent_for_request),
):
    svc = _service(workspace)
    store = _proposal_store(svc)
    proposal = await _proposal_or_404(store, proposal_id)
    applier = getattr(svc, "change_applier", None)
    if applier is None:
        raise HTTPException(status_code=412, detail="Change applier not available")
    return await applier.dry_run(proposal)


@router.post("/proposals/{proposal_id}/approve")
async def approve_proposal(
    proposal_id: str,
    workspace: Workspace = Depends(get_agent_for_request),
):
    svc = _service(workspace)
    _require_maintainer(svc)
    store = _proposal_store(svc)
    proposal = await _proposal_or_404(store, proposal_id)
    try:
        updated = await store.update(proposal.model_copy(update={"status": "approved"}))
    except InvalidProposalState as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return updated.model_dump(mode="json")


@router.post("/proposals/{proposal_id}/apply")
async def apply_proposal(
    proposal_id: str,
    workspace: Workspace = Depends(get_agent_for_request),
):
    svc = _service(workspace)
    _require_maintainer(svc)
    store = _proposal_store(svc)
    proposal = await _proposal_or_404(store, proposal_id)
    applier = getattr(svc, "change_applier", None)
    if applier is None:
        raise HTTPException(status_code=412, detail="Change applier not available")
    try:
        result = await applier.apply(proposal)
        revision = None
        if svc.svn is not None:
            try:
                revision = (await svc.svn.info()).get("revision")
            except Exception:
                revision = None
        updated = await store.update(
            proposal.model_copy(
                update={"status": "applied", "applied_revision": revision, "error": None}
            )
        )
    except InvalidProposalState as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"proposal": updated.model_dump(mode="json"), "apply_result": result}


@router.post("/proposals/{proposal_id}/commit")
async def commit_proposal(
    proposal_id: str,
    workspace: Workspace = Depends(get_agent_for_request),
):
    svc = _service(workspace)
    _require_maintainer(svc)
    store = _proposal_store(svc)
    proposal = await _proposal_or_404(store, proposal_id)
    committer = getattr(svc, "svn_committer", None)
    if committer is None:
        raise HTTPException(status_code=412, detail="SVN committer not available")
    try:
        changed_files = _relative_changed_files(svc, proposal)
        revision = await committer.commit_proposal(proposal, changed_files)
        updated = await store.update(
            proposal.model_copy(
                update={"status": "committed", "commit_revision": revision, "error": None}
            )
        )
    except InvalidProposalState as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return updated.model_dump(mode="json")


@router.post("/proposals/{proposal_id}/reject")
async def reject_proposal(
    proposal_id: str,
    workspace: Workspace = Depends(get_agent_for_request),
):
    svc = _service(workspace)
    _require_maintainer(svc)
    store = _proposal_store(svc)
    proposal = await _proposal_or_404(store, proposal_id)
    try:
        updated = await store.update(proposal.model_copy(update={"status": "rejected"}))
    except InvalidProposalState as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return updated.model_dump(mode="json")


@router.post("/proposals/{proposal_id}/revert")
async def revert_proposal(
    proposal_id: str,
    workspace: Workspace = Depends(get_agent_for_request),
):
    svc = _service(workspace)
    _require_maintainer(svc)
    store = _proposal_store(svc)
    proposal = await _proposal_or_404(store, proposal_id)
    committer = getattr(svc, "svn_committer", None)
    if committer is None:
        raise HTTPException(status_code=412, detail="SVN committer not available")
    try:
        paths = [committer.svn_root / path for path in _relative_changed_files(svc, proposal)]
        await committer.revert_local_changes(paths)
        updated = await store.update(proposal.model_copy(update={"status": "reverted"}))
    except InvalidProposalState as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return updated.model_dump(mode="json")
