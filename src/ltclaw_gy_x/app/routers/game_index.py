# -*- coding: utf-8 -*-
"""Game index HTTP API endpoints."""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...app.agent_context import get_agent_for_request
from ...app.workspace.workspace import Workspace
from ...game.models import FieldPatch, FieldInfo


class QueryRequest(BaseModel):
    q: str
    mode: str = "auto"


router = APIRouter(prefix="/game/index", tags=["game-index"])


def _get(workspace: Workspace):
    svc = workspace.service_manager.services.get("game_service")
    if svc is None:
        raise HTTPException(status_code=404, detail="Game service not available")
    qr = getattr(svc, "query_router", None)
    if qr is None:
        raise HTTPException(status_code=404, detail="Query router not available")
    return svc, qr


@router.get("/systems")
async def list_systems(workspace: Workspace = Depends(get_agent_for_request)):
    _, qr = _get(workspace)
    return await qr.list_systems()


@router.get("/tables")
async def list_tables(
    system: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    workspace: Workspace = Depends(get_agent_for_request),
):
    _, qr = _get(workspace)
    return await qr.list_tables(system=system, query=query, page=page, size=size)


@router.get("/tables/{name}")
async def get_table(name: str, workspace: Workspace = Depends(get_agent_for_request)):
    _, qr = _get(workspace)
    table = await qr.get_table(name)
    if not table:
        raise HTTPException(status_code=404, detail=f"Table '{name}' not found")
    return table.model_dump(mode="json")


@router.patch("/tables/{table}/fields/{field}")
async def patch_field(
    table: str,
    field: str,
    patch: FieldPatch,
    workspace: Workspace = Depends(get_agent_for_request),
):
    svc, qr = _get(workspace)
    if patch.confidence == "confirmed" and svc.user_config.my_role != "maintainer":
        raise HTTPException(status_code=403, detail="Only maintainers can confirm fields")
    updated = await qr.patch_field(table, field, patch)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Field '{field}' not found in table '{table}'")
    return updated.model_dump(mode="json")


@router.get("/dependencies/{table}")
async def get_dependencies(table: str, workspace: Workspace = Depends(get_agent_for_request)):
    _, qr = _get(workspace)
    return await qr.dependencies_of(table)


@router.get("/find_field")
async def find_field(
    name: str = Query(..., description="Field name to search for"),
    workspace: Workspace = Depends(get_agent_for_request),
):
    _, qr = _get(workspace)
    results = await qr.find_field(name)
    return [
        {"table": table, "field": field.model_dump(mode="json")}
        for table, field in results
    ]


@router.post("/query")
async def query(request: QueryRequest, workspace: Workspace = Depends(get_agent_for_request)):
    _, qr = _get(workspace)
    return await qr.query(request.q, request.mode)