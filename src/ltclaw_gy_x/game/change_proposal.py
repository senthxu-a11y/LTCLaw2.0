from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from .paths import get_proposals_dir


class ProposalStoreError(Exception):
    pass


class InvalidProposalState(ProposalStoreError):
    pass


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class ChangeOp(BaseModel):
    op: Literal["update_cell", "insert_row", "delete_row"]
    table: str
    row_id: str | int
    field: str | None = None
    old_value: Any | None = None
    new_value: Any | None = None


class ChangeProposal(BaseModel):
    schema_version: Literal["change-proposal.v1"] = "change-proposal.v1"
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    title: str
    description: str = ""
    ops: list[ChangeOp]
    status: Literal[
        "draft", "approved", "applied", "committed", "rejected", "reverted"
    ] = "draft"
    author: str = "agent"
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    applied_revision: int | None = None
    commit_revision: int | None = None
    error: str | None = None


class ProposalStore:
    _ALLOWED_TRANSITIONS = {
        "draft": {"approved", "rejected"},
        "approved": {"applied", "rejected"},
        "applied": {"committed", "reverted"},
    }

    def __init__(self, workspace_dir: Path):
        self.workspace_dir = Path(workspace_dir)
        self.proposals_dir = get_proposals_dir(self.workspace_dir)
        self.proposals_dir.mkdir(parents=True, exist_ok=True)

    async def create(self, proposal: ChangeProposal) -> ChangeProposal:
        return await asyncio.to_thread(self._create_sync, proposal)

    async def get(self, id: str) -> ChangeProposal | None:
        return await asyncio.to_thread(self._get_sync, id)

    async def list(
        self, status: str | None = None, limit: int = 50
    ) -> list[ChangeProposal]:
        return await asyncio.to_thread(self._list_sync, status, limit)

    async def update(self, proposal: ChangeProposal) -> ChangeProposal:
        return await asyncio.to_thread(self._update_sync, proposal)

    async def delete(self, id: str) -> bool:
        return await asyncio.to_thread(self._delete_sync, id)

    def _create_sync(self, proposal: ChangeProposal) -> ChangeProposal:
        path = self._proposal_path(proposal.id)
        if path.exists():
            raise ProposalStoreError(f"proposal already exists: {proposal.id}")
        self._write_proposal(path, proposal)
        return proposal

    def _get_sync(self, id: str) -> ChangeProposal | None:
        path = self._proposal_path(id)
        if not path.exists():
            return None
        return self._read_proposal(path)

    def _list_sync(self, status: str | None = None, limit: int = 50) -> list[ChangeProposal]:
        proposals: list[ChangeProposal] = []
        for path in self.proposals_dir.glob("*.json"):
            proposals.append(self._read_proposal(path))
        if status is not None:
            proposals = [proposal for proposal in proposals if proposal.status == status]
        proposals.sort(key=lambda proposal: proposal.created_at, reverse=True)
        return proposals[:limit]

    def _update_sync(self, proposal: ChangeProposal) -> ChangeProposal:
        path = self._proposal_path(proposal.id)
        if not path.exists():
            raise ProposalStoreError(f"proposal not found: {proposal.id}")
        existing = self._read_proposal(path)
        self._validate_transition(existing.status, proposal.status)
        updated = proposal.model_copy(update={"updated_at": _utcnow()})
        self._write_proposal(path, updated)
        return updated

    def _delete_sync(self, id: str) -> bool:
        path = self._proposal_path(id)
        if not path.exists():
            return False
        path.unlink()
        return True

    def _proposal_path(self, proposal_id: str) -> Path:
        return self.proposals_dir / f"{proposal_id}.json"

    def _read_proposal(self, path: Path) -> ChangeProposal:
        try:
            return ChangeProposal.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ProposalStoreError(f"failed to read proposal: {path}") from exc

    def _write_proposal(self, path: Path, proposal: ChangeProposal) -> None:
        payload = json.dumps(
            proposal.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
        tmp_path = path.with_suffix(f"{path.suffix}.tmp")
        try:
            tmp_path.write_text(payload, encoding="utf-8")
            tmp_path.replace(path)
        except Exception as exc:
            raise ProposalStoreError(f"failed to write proposal: {path}") from exc

    def _validate_transition(self, old_status: str, new_status: str) -> None:
        allowed = self._ALLOWED_TRANSITIONS.get(old_status, set())
        if new_status not in allowed:
            raise InvalidProposalState(f"{old_status}->{new_status}")
