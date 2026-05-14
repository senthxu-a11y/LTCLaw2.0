# -*- coding: utf-8 -*-
"""Game change proposal HTTP API endpoints."""
from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from ...app.agent_context import get_agent_for_request
from ...app.capabilities import require_capability
from ...app.approvals.service import get_approval_service
from ...app.workspace.workspace import Workspace
from ...game.change_proposal import (
    ChangeOp,
    ChangeProposal,
    InvalidProposalState,
)
from ...security.tool_guard.approval import ApprovalDecision

logger = logging.getLogger(__name__)


def _apply_approval_required() -> bool:
    val = os.environ.get("QWENPAW_GAME_APPLY_REQUIRE_APPROVAL", "")
    return val.strip().lower() in ("1", "true", "yes", "on")


def _apply_approval_timeout() -> float:
    raw = os.environ.get("QWENPAW_GAME_APPLY_APPROVAL_TIMEOUT", "300")
    try:
        return max(5.0, float(raw))
    except (TypeError, ValueError):
        return 300.0


class ChangeProposalCreate(BaseModel):
    title: str
    description: str = ""
    ops: list[dict[str, Any]]


router = APIRouter(prefix="/game/change", tags=["game-change"])

SVN_CHANGE_FROZEN_REASON = (
    "SVN commit/revert is frozen in P0-01. Apply and dry-run remain available, but SVN operations must be handled outside LTClaw."
)


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
    request: Request,
    workspace: Workspace = Depends(get_agent_for_request),
):
    require_capability(request, "workbench.test.export")
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


async def _maybe_request_apply_approval(
    workspace: Workspace,
    proposal: ChangeProposal,
) -> None:
    """Gate proposal apply behind an approval if env flag is on.

    Enable via env ``QWENPAW_GAME_APPLY_REQUIRE_APPROVAL=true``.
    Times out at ``QWENPAW_GAME_APPLY_APPROVAL_TIMEOUT`` seconds (default 300).
    """
    if not _apply_approval_required():
        return
    svc = get_approval_service()
    timeout_s = _apply_approval_timeout()
    op_count = len(proposal.ops)
    summary = (
        f"apply proposal {proposal.id} ({op_count} ops): "
        f"{proposal.title or '(untitled)'}"
    )
    pending = await svc.create_generic_pending(
        agent_id=workspace.agent_id,
        title=f"Apply proposal: {proposal.title or proposal.id}",
        summary=summary,
        severity="high",
        kind="game.proposal.apply",
        timeout_seconds=timeout_s,
        extra={
            "proposal_id": proposal.id,
            "ops_count": op_count,
            "description": (proposal.description or "")[:500],
        },
    )
    logger.info(
        "Game apply approval requested: request_id=%s proposal=%s ops=%d "
        "timeout=%.0fs",
        pending.request_id[:8],
        proposal.id,
        op_count,
        timeout_s,
    )
    decision = await svc.wait_for_approval(pending.request_id, timeout_s)
    if decision == ApprovalDecision.APPROVED:
        return
    if decision == ApprovalDecision.TIMEOUT:
        raise HTTPException(
            status_code=408,
            detail=(
                "Approval not granted within "
                f"{int(timeout_s)}s; resolve via /approval and retry"
            ),
        )
    # DENIED or anything else
    raise HTTPException(status_code=403, detail="Apply denied by reviewer")


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
    await _maybe_request_apply_approval(workspace, proposal)
    try:
        result = await applier.apply(proposal)
        updated = await store.update(
            proposal.model_copy(
                update={"status": "applied", "applied_revision": None, "error": None}
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
    raise HTTPException(
        status_code=409,
        detail={"disabled": True, "reason": SVN_CHANGE_FROZEN_REASON, "proposal_id": proposal_id},
    )


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
    raise HTTPException(
        status_code=409,
        detail={"disabled": True, "reason": SVN_CHANGE_FROZEN_REASON, "proposal_id": proposal_id},
    )
