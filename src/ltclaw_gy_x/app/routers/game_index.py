# -*- coding: utf-8 -*-
"""Game index HTTP API endpoints."""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...app.agent_context import get_agent_for_request
from ...app.workspace.workspace import Workspace
from ...game.models import FieldPatch, FieldInfo
from ...game.retrieval import get_retrieval_status


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


@router.get("/status")
async def get_index_status(
    rebuild_doc_index: bool = Query(False),
    workspace: Workspace = Depends(get_agent_for_request),
):
    svc, _ = _get(workspace)
    if not getattr(svc, "configured", False):
        return {"configured": False}
    return {
        "configured": True,
        "formal_knowledge": {
            "source": "current_release",
            "status_endpoint": "/game/knowledge/releases/status",
            "legacy_retrieval_included": False,
        },
        "legacy_retrieval": get_retrieval_status(svc, rebuild_doc_index=rebuild_doc_index),
    }

@router.get("/tables/{name}/rows")
async def get_table_rows(
    name: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    workspace: Workspace = Depends(get_agent_for_request),
):
    """Return paginated raw rows of a table for the workbench grid view."""
    svc, _ = _get(workspace)
    applier = getattr(svc, "change_applier", None)
    if applier is None:
        raise HTTPException(status_code=412, detail="Project config not loaded")
    try:
        return await __import__("asyncio").to_thread(applier.read_rows, name, offset, limit)
    except Exception as exc:  # ApplyError or file errors
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/rebuild")
async def rebuild_index(workspace: Workspace = Depends(get_agent_for_request)):
    svc, _ = _get(workspace)
    if svc.user_config.my_role != "maintainer":
        raise HTTPException(status_code=403, detail="Only maintainers can rebuild index")
    if svc.project_config is None:
        raise HTTPException(status_code=412, detail="Project config not loaded")
    try:
        return await svc.force_full_rescan()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/impact")
async def reverse_impact(
    table: str = Query(..., description="????"),
    field: Optional[str] = Query(None, description="?????????????????"),
    max_depth: int = Query(3, ge=1, le=6, description="??????"),
    workspace: Workspace = Depends(get_agent_for_request),
):
    """?????????????????/????? NumericWorkbench ????????

    ???DependencyEdge(from_table.from_field ? to_table.to_field) ??
    `from_table` ????? `from_field` ?? `to_table.to_field`?
    ????? `to_table` ????????? `from_table` ???????
    ???????????????????? BFS ???
    """
    svc, _ = _get(workspace)
    committer = getattr(svc, "index_committer", None)
    if committer is None:
        raise HTTPException(status_code=412, detail="Index committer not available")
    try:
        dep = committer.load_dependency_graph()
    except Exception:
        dep = None
    if dep is None:
        return {"target": {"table": table, "field": field}, "impacts": [], "tables": [], "total": 0}

    # ????to_table -> [edge]
    by_to: dict[str, list] = {}
    for e in getattr(dep, "edges", []) or []:
        by_to.setdefault(e.to_table, []).append(e)

    seen: set[tuple[str, str]] = set()
    impacts: list[dict] = []
    # BFS ???(table, field|None, depth, path_str)
    queue: list[tuple[str, Optional[str], int, list[str]]] = [
        (table, field, 0, [f"{table}{('.' + field) if field else ''}"])
    ]
    while queue:
        cur_table, cur_field, depth, path = queue.pop(0)
        if depth >= max_depth:
            continue
        for edge in by_to.get(cur_table, []):
            if cur_field is not None and edge.to_field != cur_field:
                continue
            key = (edge.from_table, edge.from_field)
            if key in seen:
                continue
            seen.add(key)
            conf = getattr(edge.confidence, "value", str(edge.confidence))
            impacts.append({
                "from_table": edge.from_table,
                "from_field": edge.from_field,
                "to_table": edge.to_table,
                "to_field": edge.to_field,
                "confidence": conf,
                "inferred_by": edge.inferred_by,
                "depth": depth + 1,
                "path": path + [f"{edge.from_table}.{edge.from_field}"],
            })
            queue.append((edge.from_table, None, depth + 1, path + [f"{edge.from_table}.{edge.from_field}"]))

    affected_tables = sorted({i["from_table"] for i in impacts})
    return {
        "target": {"table": table, "field": field},
        "max_depth": max_depth,
        "tables": affected_tables,
        "impacts": impacts,
        "total": len(impacts),
    }
