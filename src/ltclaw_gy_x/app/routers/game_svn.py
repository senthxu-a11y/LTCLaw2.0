# -*- coding: utf-8 -*-
"""Game SVN HTTP API endpoints for sync status and real-time logs."""
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from sse_starlette import EventSourceResponse

from ...app.agent_context import get_agent_for_request
from ...app.workspace.workspace import Workspace


router = APIRouter(prefix="/game/svn", tags=["game-svn"])

SVN_FROZEN_REASON = (
    "SVN runtime is frozen in P0-01. Run update/commit/checks outside LTClaw and keep using the local project root here."
)


def _service(workspace: Workspace):
    svc = workspace.service_manager.services.get("game_service")
    if svc is None:
        raise HTTPException(status_code=404, detail="Game service not available")
    return svc


@router.get("/status")
async def get_svn_status(workspace: Workspace = Depends(get_agent_for_request)):
    game_service = _service(workspace)
    return {
        "configured": bool(game_service.configured),
        "disabled": True,
        "reason": SVN_FROZEN_REASON,
        "current_rev": None,
        "last_polled_at": None,
        "next_poll_at": None,
        "running": False,
        "my_role": game_service.user_config.my_role,
        "watch_paths": [],
        "stats": {"check_count": 0, "change_count": 0, "error_count": 0},
    }


@router.post("/sync")
async def trigger_sync(workspace: Workspace = Depends(get_agent_for_request)):
    game_service = _service(workspace)
    raise HTTPException(
        status_code=409,
        detail={
            "disabled": True,
            "reason": SVN_FROZEN_REASON,
            "configured": bool(game_service.configured),
        },
    )


@router.get("/log/recent")
async def get_recent_logs(
    limit: int = Query(200, ge=1, le=1000),
    workspace: Workspace = Depends(get_agent_for_request),
):
    game_service = _service(workspace)
    log_bus = getattr(game_service, "_log_bus_buffer", []) or []
    recent = log_bus[-limit:]
    return {"logs": recent, "count": len(recent)}


@router.get("/changes/recent")
async def get_recent_changes(
    limit: int = Query(20, ge=1, le=100),
    workspace: Workspace = Depends(get_agent_for_request),
):
    game_service = _service(workspace)
    buffer = list(getattr(game_service, "_recent_changes_buffer", []) or [])
    if buffer:
        return {"changes": buffer[:limit], "count": len(buffer[:limit]), "source": "buffer"}
    committer = getattr(game_service, "index_committer", None)
    if committer is not None:
        try:
            last = committer.load_changeset()
        except Exception:
            last = None
        if last is not None:
            entry = last.model_dump(mode="json") if hasattr(last, "model_dump") else dict(last)
            entry.setdefault("revision", entry.get("to_rev"))
            return {"changes": [entry], "count": 1, "source": "persisted"}
    return {"changes": [], "count": 0, "source": "empty"}


@router.get("/log/stream")
async def stream_logs(workspace: Workspace = Depends(get_agent_for_request)):
    game_service = _service(workspace)

    async def log_generator():
        try:
            yield {
                "event": "disabled",
                "data": {
                    "disabled": True,
                    "reason": SVN_FROZEN_REASON,
                    "configured": bool(game_service.configured),
                },
            }
        except asyncio.CancelledError:
            pass

    return EventSourceResponse(log_generator())