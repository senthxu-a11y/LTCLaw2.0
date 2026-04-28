# -*- coding: utf-8 -*-
"""Game SVN HTTP API endpoints for sync status and real-time logs."""
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from sse_starlette import EventSourceResponse

from ...app.agent_context import get_agent_for_request
from ...app.workspace.workspace import Workspace


router = APIRouter(prefix="/game/svn", tags=["game-svn"])


def _service(workspace: Workspace):
    svc = workspace.service_manager.services.get("game_service")
    if svc is None:
        raise HTTPException(status_code=404, detail="Game service not available")
    return svc


@router.get("/status")
async def get_svn_status(workspace: Workspace = Depends(get_agent_for_request)):
    game_service = _service(workspace)
    if not game_service.configured:
        return {
            "configured": False,
            "current_rev": None,
            "last_polled_at": None,
            "next_poll_at": None,
            "running": False,
            "my_role": game_service.user_config.my_role,
        }

    svn_watcher = getattr(game_service, "svn_watcher", None)
    if svn_watcher is not None:
        status = svn_watcher.get_status() if hasattr(svn_watcher, "get_status") else getattr(svn_watcher, "status", {})
        if isinstance(status, dict):
            status = dict(status)
            status["configured"] = True
            return status

    svn_info = {}
    if game_service.svn:
        try:
            svn_info = await game_service.svn.info()
        except Exception:
            pass
    return {
        "configured": True,
        "current_rev": svn_info.get("revision") if isinstance(svn_info, dict) else None,
        "last_polled_at": None,
        "next_poll_at": None,
        "running": False,
        "my_role": game_service.user_config.my_role,
    }


@router.post("/sync")
async def trigger_sync(workspace: Workspace = Depends(get_agent_for_request)):
    game_service = _service(workspace)
    if not game_service.configured:
        raise HTTPException(status_code=400, detail="Game service not configured")
    if game_service.user_config.my_role != "maintainer":
        raise HTTPException(status_code=409, detail="not maintainer, sync skipped")
    svn_watcher = getattr(game_service, "svn_watcher", None)
    if svn_watcher is None:
        raise HTTPException(status_code=400, detail="SVN watcher not available")
    changeset = await svn_watcher.trigger_now()
    if hasattr(changeset, "model_dump"):
        return changeset.model_dump(mode="json")
    return changeset


@router.get("/log/recent")
async def get_recent_logs(
    limit: int = Query(200, ge=1, le=1000),
    workspace: Workspace = Depends(get_agent_for_request),
):
    game_service = _service(workspace)
    log_bus = getattr(game_service, "_log_bus_buffer", []) or []
    recent = log_bus[-limit:]
    return {"logs": recent, "count": len(recent)}


@router.get("/log/stream")
async def stream_logs(workspace: Workspace = Depends(get_agent_for_request)):
    game_service = _service(workspace)

    async def log_generator():
        if not hasattr(game_service, "_log_bus_buffer"):
            game_service._log_bus_buffer = []
            game_service._log_subscribers = []
        subscriber_queue: asyncio.Queue = asyncio.Queue()
        game_service._log_subscribers.append(subscriber_queue)
        try:
            for log_entry in (game_service._log_bus_buffer or [])[-50:]:
                yield {"event": "log", "data": log_entry}
            while True:
                try:
                    log_entry = await asyncio.wait_for(subscriber_queue.get(), timeout=30.0)
                    yield {"event": "log", "data": log_entry}
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": {"ts": asyncio.get_event_loop().time()}}
        except asyncio.CancelledError:
            pass
        finally:
            if subscriber_queue in game_service._log_subscribers:
                game_service._log_subscribers.remove(subscriber_queue)

    return EventSourceResponse(log_generator())