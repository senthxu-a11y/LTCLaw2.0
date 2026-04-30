# -*- coding: utf-8 -*-
"""Game development tools for AI agent.

These tools delegate to the per-workspace GameService (registered as the
``game_service`` entry on the workspace ServiceManager). Each tool resolves
the active workspace via the agent context ContextVar plus the module-level
MultiAgentManager singleton accessor.
"""

from typing import Any, Dict, List

from ...app.agent_context import get_current_agent_id
from ...app.multi_agent_manager import get_active_manager
from ...game.change_proposal import ChangeOp, ChangeProposal


async def _get_game_service():
    """Return (game_service, error_payload). One of them is always None."""
    agent_id = get_current_agent_id()
    if not agent_id:
        return None, {"error": "No agent context available"}
    manager = get_active_manager()
    if manager is None:
        return None, {"error": "MultiAgentManager not initialised"}
    try:
        workspace = await manager.get_agent(agent_id)
    except Exception as e:  # noqa: BLE001
        return None, {"error": f"Workspace lookup failed: {e}"}
    sm = getattr(workspace, "service_manager", None)
    services = getattr(sm, "services", {}) if sm else {}
    service = services.get("game_service")
    if service is None:
        return None, {"error": "Game service not registered for this workspace"}
    if not getattr(service, "configured", False):
        return None, {"error": "Game service not configured (missing project config?)"}
    return service, None


async def game_query_tables(query: str, mode: str = "auto") -> Dict[str, Any]:
    """Search tables/fields/systems by keyword. Query can be table name,
    field name, or natural-language description."""
    service, err = await _get_game_service()
    if err:
        return err
    router = getattr(service, "query_router", None)
    if router is None:
        return {"error": "Query router not available"}
    try:
        return await router.query(query, mode)
    except Exception as e:  # noqa: BLE001
        return {"error": f"Query failed: {e}"}


async def game_describe_field(table: str, field: str) -> Dict[str, Any]:
    """Describe a single field within a table (AI summary, references)."""
    service, err = await _get_game_service()
    if err:
        return err
    router = getattr(service, "query_router", None)
    if router is None:
        return {"error": "Query router not available"}
    try:
        table_index = await router.get_table(table)
    except Exception as e:  # noqa: BLE001
        return {"error": f"Failed to load table: {e}"}
    if not table_index:
        return {"error": f"Table '{table}' not found"}
    target = None
    for f in getattr(table_index, "fields", []) or []:
        if getattr(f, "name", None) == field:
            target = f
            break
    if target is None:
        return {"error": f"Field '{field}' not found in table '{table}'"}
    return {
        "table": table,
        "field": target.model_dump(mode="json"),
        "table_summary": getattr(table_index, "ai_summary", None),
        "row_count": getattr(table_index, "row_count", None),
    }


async def game_table_dependencies(table: str) -> Dict[str, Any]:
    """List upstream and downstream dependencies of a table."""
    service, err = await _get_game_service()
    if err:
        return err
    router = getattr(service, "query_router", None)
    if router is None:
        return {"error": "Query router not available"}
    try:
        deps = await router.dependencies_of(table)
    except Exception as e:  # noqa: BLE001
        return {"error": f"Dependencies query failed: {e}"}
    return {"table": table, "dependencies": deps}


async def game_reverse_impact(
    table: str,
    field: str = "",
    max_depth: int = 3,
) -> Dict[str, Any]:
    """Analyse downstream impact of changing a table/field via reverse BFS over
    the dependency graph.

    Args:
        table: target table that would be modified.
        field: optional target field; empty string = whole table.
        max_depth: BFS depth cap (default 3).

    Returns:
        {"target": {...}, "tables": [...], "impacts": [...], "total": n}
        Each impact item has {from_table, from_field, to_table, to_field,
        confidence, depth, path}.
    """
    service, err = await _get_game_service()
    if err:
        return err
    committer = getattr(service, "index_committer", None)
    if committer is None:
        return {"error": "Index committer not available"}
    try:
        dep = committer.load_dependency_graph()
    except Exception as e:  # noqa: BLE001
        return {"error": f"Dependency graph load failed: {e}"}
    if dep is None:
        return {"target": {"table": table, "field": field or None}, "impacts": [], "tables": [], "total": 0}

    by_to: Dict[str, list] = {}
    for e in getattr(dep, "edges", []) or []:
        by_to.setdefault(e.to_table, []).append(e)

    field_filter = field or None
    seen: set = set()
    impacts: list = []
    queue: list = [(table, field_filter, 0, [f"{table}{('.' + field_filter) if field_filter else ''}"])]
    while queue:
        cur_table, cur_field, depth, path = queue.pop(0)
        if depth >= max(1, min(max_depth, 6)):
            continue
        for edge in by_to.get(cur_table, []):
            if cur_field is not None and edge.to_field != cur_field:
                continue
            key = (edge.from_table, edge.from_field)
            if key in seen:
                continue
            seen.add(key)
            conf = getattr(edge.confidence, "value", str(edge.confidence))
            new_path = path + [f"{edge.from_table}.{edge.from_field}"]
            impacts.append({
                "from_table": edge.from_table,
                "from_field": edge.from_field,
                "to_table": edge.to_table,
                "to_field": edge.to_field,
                "confidence": conf,
                "depth": depth + 1,
                "path": new_path,
            })
            queue.append((edge.from_table, None, depth + 1, new_path))

    return {
        "target": {"table": table, "field": field or None},
        "max_depth": max_depth,
        "tables": sorted({i["from_table"] for i in impacts}),
        "impacts": impacts,
        "total": len(impacts),
    }


async def game_search_knowledge(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search the design knowledge base. Phase-2 stub: returns empty list."""
    return []


async def game_list_systems() -> List[Dict[str, Any]]:
    """List system groups and their table counts."""
    service, err = await _get_game_service()
    if err:
        return [err]
    router = getattr(service, "query_router", None)
    if router is None:
        return [{"error": "Query router not available"}]
    try:
        systems = await router.list_systems()
    except Exception as e:  # noqa: BLE001
        return [{"error": f"List systems failed: {e}"}]
    if not systems:
        return []
    return [s.model_dump(mode="json") if hasattr(s, "model_dump") else dict(s) for s in systems]


async def game_propose_change(
    title: str,
    description: str,
    ops: list[dict],
) -> Dict[str, Any]:
    """Create a draft change proposal for game data tables.

    Each op in ``ops`` MUST follow the ChangeOp schema below.

    Required fields:
        op (str): One of ``"update_cell"``, ``"insert_row"``, ``"delete_row"``.
                  (Note: lowercase with underscore. NOT "UPDATE" / "update".)
        table (str): Target table name (case-sensitive, matches indexed table).
        row_id (str | int): Primary key value of the target row.

    Optional fields (depend on op):
        field (str): Column name. Required for ``update_cell``.
        new_value (Any): New cell value. Required for ``update_cell`` and
                         ``insert_row``. Use a dict {col: val} for insert_row.
        old_value (Any): Optional, for audit / safe-update.

    DO NOT use ``updates`` (dict), ``filter`` (dict), or ``where``. Each cell
    change is one ``update_cell`` op. To change two columns on the same row,
    emit two ops.

    Example:
        ops = [
            {"op": "update_cell", "table": "Hero", "row_id": 1,
             "field": "HP", "new_value": 100},
            {"op": "update_cell", "table": "Hero", "row_id": 1,
             "field": "ATK", "new_value": 25},
        ]

    Returns:
        {"id": <proposal_id>, "status": "draft", "ops_count": <int>}
    """
    service, err = await _get_game_service()
    if err:
        return err
    store = getattr(service, "proposal_store", None)
    if store is None:
        return {"error": "Proposal store not available"}
    proposal = ChangeProposal(
        title=title,
        description=description,
        ops=[ChangeOp.model_validate(op) for op in ops],
        status="draft",
    )
    try:
        created = await store.create(proposal)
    except Exception as e:  # noqa: BLE001
        return {"error": f"Create proposal failed: {e}"}
    return {
        "id": created.id,
        "status": created.status,
        "ops_count": len(created.ops),
    }


async def game_apply_proposal(
    proposal_id: str,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """Preview or apply an approved proposal."""
    service, err = await _get_game_service()
    if err:
        return err
    store = getattr(service, "proposal_store", None)
    if store is None:
        return {"error": "Proposal store not available"}
    applier = getattr(service, "change_applier", None)
    if applier is None:
        return {"error": "Change applier not available"}
    proposal = await store.get(proposal_id)
    if proposal is None:
        return {"error": f"Proposal '{proposal_id}' not found"}
    try:
        if dry_run:
            preview = await applier.dry_run(proposal)
            return {"proposal_id": proposal.id, "dry_run": True, "preview": preview}
        if proposal.status != "approved":
            return {"error": f"Proposal '{proposal_id}' is not approved"}
        result = await applier.apply(proposal)
        updated = await store.update(
            proposal.model_copy(update={"status": "applied"})
        )
    except Exception as e:  # noqa: BLE001
        return {"error": f"Apply proposal failed: {e}"}
    return {
        "proposal_id": updated.id,
        "status": updated.status,
        "apply_result": result,
    }


async def game_commit_proposal(
    proposal_id: str,
) -> Dict[str, Any]:
    """Commit an applied proposal through SVN."""
    service, err = await _get_game_service()
    if err:
        return err
    if getattr(service.user_config, "my_role", None) != "maintainer":
        return {"error": "Only maintainers can commit proposals"}
    store = getattr(service, "proposal_store", None)
    if store is None:
        return {"error": "Proposal store not available"}
    committer = getattr(service, "svn_committer", None)
    if committer is None:
        return {"error": "SVN committer not available"}
    applier = getattr(service, "change_applier", None)
    if applier is None:
        return {"error": "Change applier not available"}
    proposal = await store.get(proposal_id)
    if proposal is None:
        return {"error": f"Proposal '{proposal_id}' not found"}
    if proposal.status != "applied":
        return {"error": f"Proposal '{proposal_id}' is not applied"}
    try:
        grouped = applier._group_ops_by_file(proposal.ops)
        changed_files = [
            str(path.relative_to(applier.svn_root)).replace("\\", "/")
            for path in grouped.keys()
        ]
        revision = await committer.commit_proposal(proposal, changed_files)
        updated = await store.update(
            proposal.model_copy(
                update={"status": "committed", "commit_revision": revision}
            )
        )
    except Exception as e:  # noqa: BLE001
        return {"error": f"Commit proposal failed: {e}"}
    return {
        "proposal_id": updated.id,
        "status": updated.status,
        "commit_revision": updated.commit_revision,
    }
