from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import json

import pytest
from agentscope.tool import ToolResponse

from ltclaw_gy_x.agents.tools import gamedev_tools
from ltclaw_gy_x.game.change_proposal import ChangeOp, ChangeProposal


class _Store:
    def __init__(self, proposal: ChangeProposal | None = None):
        self.created = []
        self.updated = []
        self.proposal = proposal

    async def create(self, proposal):
        self.created.append(proposal)
        self.proposal = proposal
        return proposal

    async def get(self, proposal_id):
        if self.proposal and self.proposal.id == proposal_id:
            return self.proposal
        return None

    async def update(self, proposal):
        self.updated.append(proposal)
        self.proposal = proposal
        return proposal


@pytest.mark.asyncio
async def test_game_propose_change_creates_draft(monkeypatch):
    store = _Store()
    service = SimpleNamespace(proposal_store=store, user_config=SimpleNamespace(my_role="maintainer"))
    monkeypatch.setattr(gamedev_tools, "_get_game_service", lambda: _async_result((service, None)))

    result = await gamedev_tools.game_propose_change(
        "Buff hp",
        "Increase hero hp",
        [{"op": "update_cell", "table": "Hero", "row_id": 1, "field": "HP", "new_value": 100}],
    )

    assert result["status"] == "draft"
    assert result["ops_count"] == 1
    assert store.created[0].title == "Buff hp"


@pytest.mark.asyncio
async def test_game_apply_proposal_dry_run(monkeypatch):
    proposal = ChangeProposal(
        id="p1",
        title="Buff hp",
        ops=[ChangeOp(op="update_cell", table="Hero", row_id=1, field="HP", new_value=100)],
        status="approved",
    )
    store = _Store(proposal)

    async def _dry_run(_proposal):
        return [{"ok": True}]

    service = SimpleNamespace(
        proposal_store=store,
        change_applier=SimpleNamespace(dry_run=_dry_run),
        user_config=SimpleNamespace(my_role="maintainer"),
    )
    monkeypatch.setattr(gamedev_tools, "_get_game_service", lambda: _async_result((service, None)))

    result = await gamedev_tools.game_apply_proposal("p1", dry_run=True)

    assert result == {"proposal_id": "p1", "dry_run": True, "preview": [{"ok": True}]}


@pytest.mark.asyncio
async def test_game_commit_proposal_updates_store(monkeypatch):
    proposal = ChangeProposal(
        id="p1",
        title="Buff hp",
        ops=[ChangeOp(op="update_cell", table="Hero", row_id=1, field="HP", new_value=100)],
        status="applied",
    )
    store = _Store(proposal)

    async def _commit(_proposal, changed_files):
        assert changed_files == ["tables/Hero.csv"]
        return 789

    service = SimpleNamespace(
        proposal_store=store,
        change_applier=SimpleNamespace(
            svn_root=Path("repo"),
            _group_ops_by_file=lambda _ops: {Path("repo") / "tables" / "Hero.csv": _ops},
        ),
        svn_committer=SimpleNamespace(commit_proposal=_commit),
        user_config=SimpleNamespace(my_role="maintainer"),
    )
    monkeypatch.setattr(gamedev_tools, "_get_game_service", lambda: _async_result((service, None)))

    result = await gamedev_tools.game_commit_proposal("p1")

    assert result["status"] == "committed"
    assert result["commit_revision"] == 789
    assert store.updated[-1].commit_revision == 789


async def _async_result(value):
    return value


def _tool_payload(response: ToolResponse):
    assert isinstance(response, ToolResponse)
    assert response.content
    first = response.content[0]
    text = first.get("text") if isinstance(first, dict) else first.text
    return json.loads(text)


@pytest.mark.asyncio
async def test_game_query_tables_returns_tool_response(monkeypatch):
    router = SimpleNamespace(query=lambda query, mode: _async_result({"query": query, "mode": mode, "count": 1}))
    service = SimpleNamespace(query_router=router, configured=True)
    monkeypatch.setattr(gamedev_tools, "_get_game_service", lambda: _async_result((service, None)))

    result = await gamedev_tools.game_query_tables("Hero", mode="auto")

    assert isinstance(result, ToolResponse)
    assert _tool_payload(result) == {"query": "Hero", "mode": "auto", "count": 1}


@pytest.mark.asyncio
async def test_game_describe_field_returns_tool_response(monkeypatch):
    field = SimpleNamespace(model_dump=lambda mode="json": {"name": "HP", "type": "int"}, name="HP")
    table_index = SimpleNamespace(fields=[field], ai_summary="hero table", row_count=10)
    router = SimpleNamespace(get_table=lambda table: _async_result(table_index))
    service = SimpleNamespace(query_router=router, configured=True)
    monkeypatch.setattr(gamedev_tools, "_get_game_service", lambda: _async_result((service, None)))

    result = await gamedev_tools.game_describe_field("Hero", "HP")

    assert isinstance(result, ToolResponse)
    assert _tool_payload(result) == {
        "table": "Hero",
        "field": {"name": "HP", "type": "int"},
        "table_summary": "hero table",
        "row_count": 10,
    }


@pytest.mark.asyncio
async def test_game_reverse_impact(monkeypatch):
    edge1 = SimpleNamespace(
        from_table="Skill", from_field="HeroId", to_table="Hero", to_field="ID",
        confidence=SimpleNamespace(value="confirmed"), inferred_by="rule",
    )
    edge2 = SimpleNamespace(
        from_table="Buff", from_field="SkillId", to_table="Skill", to_field="ID",
        confidence=SimpleNamespace(value="confirmed"), inferred_by="rule",
    )
    committer = SimpleNamespace(
        load_dependency_graph=lambda: SimpleNamespace(edges=[edge1, edge2]),
    )
    service = SimpleNamespace(index_committer=committer)
    monkeypatch.setattr(
        gamedev_tools, "_get_game_service",
        lambda: _async_result((service, None)),
    )

    result = await gamedev_tools.game_reverse_impact("Hero", max_depth=3)
    assert result["total"] == 2
    assert sorted(result["tables"]) == ["Buff", "Skill"]
    depths = {i["from_table"]: i["depth"] for i in result["impacts"]}
    assert depths == {"Skill": 1, "Buff": 2}


@pytest.mark.asyncio
async def test_game_reverse_impact_no_graph(monkeypatch):
    service = SimpleNamespace(index_committer=SimpleNamespace(load_dependency_graph=lambda: None))
    monkeypatch.setattr(
        gamedev_tools, "_get_game_service",
        lambda: _async_result((service, None)),
    )
    result = await gamedev_tools.game_reverse_impact("X")
    assert result["total"] == 0
    assert result["tables"] == []
