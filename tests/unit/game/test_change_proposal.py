import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from ltclaw_gy_x.game.change_proposal import (
    ChangeOp,
    ChangeProposal,
    InvalidProposalState,
    ProposalStore,
)
from ltclaw_gy_x.game.paths import get_proposals_dir


def _make_proposal(
    proposal_id: str,
    *,
    title: str | None = None,
    status: str = "draft",
    created_at: datetime | None = None,
) -> ChangeProposal:
    timestamp = created_at or datetime.now(UTC).replace(tzinfo=None)
    return ChangeProposal(
        id=proposal_id,
        title=title or proposal_id,
        ops=[
            ChangeOp(
                op="update_cell",
                table="hero",
                row_id=1,
                field="hp",
                old_value=10,
                new_value=20,
            )
        ],
        status=status,
        created_at=timestamp,
        updated_at=timestamp,
    )


@pytest.mark.asyncio
async def test_create_get_and_delete_round_trip(tmp_path):
    store = ProposalStore(tmp_path)
    proposal = _make_proposal("p1")

    created = await store.create(proposal)
    loaded = await store.get(proposal.id)
    deleted = await store.delete(proposal.id)

    assert created == proposal
    assert loaded == proposal
    assert deleted is True
    assert await store.get(proposal.id) is None


@pytest.mark.asyncio
async def test_list_returns_created_at_desc_order(tmp_path):
    store = ProposalStore(tmp_path)
    now = datetime.now(UTC).replace(tzinfo=None)
    older = _make_proposal("older", created_at=now - timedelta(minutes=2))
    newer = _make_proposal("newer", created_at=now)

    await store.create(older)
    await store.create(newer)

    proposals = await store.list()

    assert [proposal.id for proposal in proposals] == ["newer", "older"]


@pytest.mark.asyncio
async def test_list_filters_by_status_and_limit(tmp_path):
    store = ProposalStore(tmp_path)
    base = datetime.now(UTC).replace(tzinfo=None)
    await store.create(_make_proposal("draft-1", created_at=base - timedelta(minutes=3)))
    await store.create(
        _make_proposal(
            "approved-1",
            status="approved",
            created_at=base - timedelta(minutes=2),
        )
    )
    await store.create(
        _make_proposal(
            "approved-2",
            status="approved",
            created_at=base - timedelta(minutes=1),
        )
    )

    proposals = await store.list(status="approved", limit=1)

    assert [proposal.id for proposal in proposals] == ["approved-2"]


@pytest.mark.asyncio
async def test_update_applies_valid_state_transition_and_refreshes_updated_at(tmp_path):
    store = ProposalStore(tmp_path)
    proposal = _make_proposal("p1")
    await store.create(proposal)

    updated = await store.update(proposal.model_copy(update={"status": "approved"}))

    assert updated.status == "approved"
    assert updated.updated_at > proposal.updated_at
    assert (await store.get(proposal.id)).status == "approved"


@pytest.mark.asyncio
async def test_update_rejects_invalid_state_transition(tmp_path):
    store = ProposalStore(tmp_path)
    proposal = _make_proposal("p1")
    await store.create(proposal)

    with pytest.raises(InvalidProposalState, match="draft->applied"):
        await store.update(proposal.model_copy(update={"status": "applied"}))


@pytest.mark.asyncio
async def test_serialization_round_trip_preserves_datetime_and_literals(tmp_path):
    store = ProposalStore(tmp_path)
    proposal = ChangeProposal(
        id="p1",
        title="serialize",
        description="round trip",
        ops=[
            ChangeOp(
                op="insert_row",
                table="hero",
                row_id="1001",
                new_value={"ID": "1001", "name": "Mage"},
            )
        ],
        status="draft",
        created_at=datetime(2026, 4, 28, 1, 2, 3),
        updated_at=datetime(2026, 4, 28, 1, 2, 4),
    )

    await store.create(proposal)
    loaded = await store.get(proposal.id)

    assert loaded == proposal
    assert isinstance(loaded.created_at, datetime)
    assert loaded.ops[0].op == "insert_row"


@pytest.mark.asyncio
async def test_concurrent_create_keeps_all_records(tmp_path):
    store = ProposalStore(tmp_path)
    proposals = [_make_proposal(f"p{i}") for i in range(10)]

    await asyncio.gather(*(store.create(proposal) for proposal in proposals))

    loaded = await store.list(limit=20)

    assert len(loaded) == 10
    assert {proposal.id for proposal in loaded} == {proposal.id for proposal in proposals}


@pytest.mark.asyncio
async def test_store_creates_proposals_directory(tmp_path):
    store = ProposalStore(tmp_path)

    assert store.proposals_dir == get_proposals_dir(tmp_path)
    assert "sessions" in store.proposals_dir.parts
    assert "tools" in store.proposals_dir.parts
    assert store.proposals_dir.exists()
