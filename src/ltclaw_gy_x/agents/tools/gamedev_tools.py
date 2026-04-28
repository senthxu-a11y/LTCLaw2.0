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
    """Create a draft change proposal."""
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
