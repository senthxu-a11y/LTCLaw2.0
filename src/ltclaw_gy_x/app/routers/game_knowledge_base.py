from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Request
from pydantic import BaseModel, Field

from ...knowledge_base import KnowledgeBaseEntry, get_kb_store
from ..agent_context import get_agent_for_request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/game-knowledge-base", tags=["game-knowledge-base"])


class KbEntryIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    summary: str = Field(default="", max_length=4000)
    category: str = Field(default="general", max_length=80)
    source: str = Field(default="manual", max_length=40)
    tags: list[str] = Field(default_factory=list)
    extra: dict[str, Any] | None = None


class KbEntryUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    category: str | None = None
    source: str | None = None
    tags: list[str] | None = None
    extra: dict[str, Any] | None = None


def _serialize(entry: KnowledgeBaseEntry) -> dict[str, Any]:
    d = entry.to_dict()
    return {**d, "created_at_epoch": d.get("created_at")}


@router.get("/entries")
async def list_entries(request: Request) -> dict[str, Any]:
    workspace = await get_agent_for_request(request)
    store = get_kb_store(workspace.workspace_dir)
    items = [_serialize(e) for e in store.list_entries()]
    return {"items": items, "count": len(items)}


@router.post("/entries")
async def create_entry(request: Request, body: KbEntryIn = Body(...)) -> dict[str, Any]:
    workspace = await get_agent_for_request(request)
    store = get_kb_store(workspace.workspace_dir)
    entry = store.add(
        title=body.title,
        summary=body.summary,
        category=body.category,
        source=body.source,
        tags=body.tags,
        extra=body.extra or {},
    )
    return {"item": _serialize(entry)}


@router.patch("/entries/{entry_id}")
async def update_entry(
    entry_id: str,
    request: Request,
    body: KbEntryUpdate = Body(...),
) -> dict[str, Any]:
    workspace = await get_agent_for_request(request)
    store = get_kb_store(workspace.workspace_dir)
    payload = body.model_dump(exclude_unset=True, exclude_none=True)
    entry = store.update(entry_id, **payload)
    if entry is None:
        raise HTTPException(status_code=404, detail="entry not found")
    return {"item": _serialize(entry)}


@router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: str, request: Request) -> dict[str, Any]:
    workspace = await get_agent_for_request(request)
    store = get_kb_store(workspace.workspace_dir)
    ok = store.delete(entry_id)
    if not ok:
        raise HTTPException(status_code=404, detail="entry not found")
    return {"deleted": entry_id}


@router.post("/search")
async def search_entries(
    request: Request,
    body: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    workspace = await get_agent_for_request(request)
    store = get_kb_store(workspace.workspace_dir)
    query = str(body.get("query") or "").strip()
    top_k = int(body.get("top_k") or 10)
    category = body.get("category") or None
    mode = "legacy_kb_search"
    if not query:
        return {
            "items": [],
            "count": 0,
            "query": query,
            "mode": mode,
            "scope": "legacy",
            "semantic_role": "debug_migration_only",
            "affects_release": False,
            "affects_rag": False,
        }

    hits = store.search(query, top_k=max(1, min(top_k, 50)), category=category)
    items = []
    for entry, score in hits:
        d = _serialize(entry)
        d["score"] = round(float(score), 4)
        d["source_type"] = "kb_entry"
        d["evidence"] = {
            "kb_entry_id": entry.id,
            "path": entry.extra.get("doc_path") or entry.extra.get("path"),
            "source": entry.source,
        }
        items.append(d)
    return {
        "items": items,
        "count": len(items),
        "query": query,
        "mode": mode,
        "scope": "legacy",
        "semantic_role": "debug_migration_only",
        "affects_release": False,
        "affects_rag": False,
    }


@router.get("/stats")
async def get_stats(request: Request) -> dict[str, Any]:
    workspace = await get_agent_for_request(request)
    store = get_kb_store(workspace.workspace_dir)
    cats: dict[str, int] = {}
    for e in store.list_entries():
        cats[e.category] = cats.get(e.category, 0) + 1
    return {"size": store.size, "by_category": cats}
