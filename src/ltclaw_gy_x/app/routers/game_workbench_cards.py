"""SSE-backed HTTP API for workbench cards."""
from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from ..agent_context import get_agent_for_request
from ..workbench_cards import (
    CARD_KINDS,
    WorkbenchCard,
    get_broker,
    publish_card,
)

router = APIRouter(tags=["workbench-cards"])


class WorkbenchCardCreate(BaseModel):
    kind: str
    title: str
    summary: str = ""
    id: Optional[str] = None
    href: Optional[str] = None
    payload: Optional[dict[str, Any]] = None


def _serialize(card: WorkbenchCard) -> dict[str, Any]:
    return {
        "id": card.id,
        "agentId": card.agent_id,
        "kind": card.kind,
        "title": card.title,
        "summary": card.summary,
        "href": card.href,
        "payload": card.payload or {},
        "createdAt": int(card.created_at * 1000),
    }


@router.get("/workbench-cards")
async def list_cards(request: Request, limit: int = 50):
    workspace = await get_agent_for_request(request)
    broker = get_broker(workspace.agent_id)
    items = [_serialize(c) for c in broker.list_recent(limit)]
    return {"items": items, "count": len(items)}


@router.post("/workbench-cards")
async def post_card(request: Request, body: WorkbenchCardCreate):
    workspace = await get_agent_for_request(request)
    if body.kind not in CARD_KINDS:
        return {"ok": False, "error": f"unknown kind: {body.kind}"}
    card = publish_card(
        agent_id=workspace.agent_id,
        kind=body.kind,
        title=body.title,
        summary=body.summary or "",
        card_id=body.id,
        href=body.href,
        payload=body.payload,
    )
    return {"ok": True, "item": _serialize(card)}


@router.get("/workbench-cards/stream")
async def stream_cards(request: Request):
    workspace = await get_agent_for_request(request)
    broker = get_broker(workspace.agent_id)

    async def _gen():
        queue = broker.subscribe()
        try:
            for c in broker.list_recent():
                yield {"event": "card", "data": json.dumps(_serialize(c), ensure_ascii=False)}
            while True:
                if await request.is_disconnected():
                    break
                try:
                    card = await asyncio.wait_for(queue.get(), timeout=20.0)
                    yield {"event": "card", "data": json.dumps(_serialize(card), ensure_ascii=False)}
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": "1"}
        finally:
            broker.unsubscribe(queue)

    return EventSourceResponse(_gen())