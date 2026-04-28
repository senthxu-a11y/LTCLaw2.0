from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from ltclaw_gy_x.app.agent_context import get_agent_for_request
from ltclaw_gy_x.app.routers.game_change import router
from ltclaw_gy_x.game.change_proposal import ChangeOp, ChangeProposal, InvalidProposalState


class _Store:
    def __init__(self):
        self.items = {}

    async def create(self, proposal):
        self.items[proposal.id] = proposal
        return proposal

    async def list(self, status=None, limit=50):
        items = list(self.items.values())
        if status is not None:
            items = [item for item in items if item.status == status]
        return items[:limit]

    async def get(self, proposal_id):
        return self.items.get(proposal_id)

    async def update(self, proposal):
        current = self.items.get(proposal.id)
        if current and current.status == "draft" and proposal.status == "applied":
            raise InvalidProposalState("draft->applied")
        self.items[proposal.id] = proposal
        return proposal


def _workspace(role="maintainer", service=None):
    if service is None:
        service = SimpleNamespace(
            proposal_store=_Store(),
            change_applier=None,
            svn_committer=None,
            user_config=SimpleNamespace(my_role=role),
            svn=None,
        )
    return SimpleNamespace(
        service_manager=SimpleNamespace(services={"game_service": service})
    )


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return app


@pytest.fixture
def client(app):
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_create_list_and_get_happy_path(app, client):
    workspace = _workspace()
    app.dependency_overrides[get_agent_for_request] = lambda: workspace

    async with client:
        created = await client.post(
            "/api/game/change/proposals",
            json={
                "title": "Buff hp",
                "description": "Increase hp",
                "ops": [{"op": "update_cell", "table": "Hero", "row_id": 1, "field": "HP", "new_value": 100}],
            },
        )
        listed = await client.get("/api/game/change/proposals")
        detail = await client.get(f"/api/game/change/proposals/{created.json()['id']}")

    assert created.status_code == 200
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert detail.status_code == 200
    assert detail.json()["title"] == "Buff hp"


@pytest.mark.asyncio
async def test_invalid_state_transition_returns_409(app, client):
    store = _Store()
    proposal = ChangeProposal(
        id="p1",
        title="Bad apply",
        ops=[ChangeOp(op="update_cell", table="Hero", row_id=1, field="HP", new_value=100)],
        status="draft",
    )
    store.items[proposal.id] = proposal

    async def _apply(_proposal):
        return {"changed_files": [], "summary": "0 updates / 0 inserts / 0 deletes"}

    service = SimpleNamespace(
        proposal_store=store,
        change_applier=SimpleNamespace(apply=_apply),
        svn_committer=None,
        user_config=SimpleNamespace(my_role="maintainer"),
        svn=None,
    )
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(service=service)

    async with client:
        response = await client.post("/api/game/change/proposals/p1/apply")

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_non_maintainer_approve_returns_403(app, client):
    store = _Store()
    proposal = ChangeProposal(id="p1", title="Approve", ops=[], status="draft")
    store.items[proposal.id] = proposal
    service = SimpleNamespace(
        proposal_store=store,
        change_applier=None,
        svn_committer=None,
        user_config=SimpleNamespace(my_role="consumer"),
        svn=None,
    )
    app.dependency_overrides[get_agent_for_request] = lambda: _workspace(role="consumer", service=service)

    async with client:
        response = await client.post("/api/game/change/proposals/p1/approve")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_missing_service_returns_404(app, client):
    app.dependency_overrides[get_agent_for_request] = lambda: SimpleNamespace(
        service_manager=SimpleNamespace(services={})
    )

    async with client:
        response = await client.get("/api/game/change/proposals")

    assert response.status_code == 404
