"""In-memory pub/sub broker for Chat -> Workbench cards."""
from __future__ import annotations

import asyncio
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

CARD_KINDS = ("numeric_table", "draft_doc", "svn_change", "kb_hit")
MAX_BUFFER = 50


@dataclass
class WorkbenchCard:
    id: str
    agent_id: str
    kind: str
    title: str
    summary: str = ""
    href: Optional[str] = None
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class _AgentBroker:
    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        self._buffer: deque[WorkbenchCard] = deque(maxlen=MAX_BUFFER)
        self._subs: list[asyncio.Queue] = []
        self._lock = threading.Lock()

    def publish(self, card: WorkbenchCard) -> None:
        with self._lock:
            for i, c in enumerate(list(self._buffer)):
                if c.id == card.id:
                    try:
                        self._buffer.remove(c)
                    except ValueError:
                        pass
                    break
            self._buffer.append(card)
            subs = list(self._subs)
        for q in subs:
            try:
                q.put_nowait(card)
            except asyncio.QueueFull:
                pass
            except Exception:
                pass

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=128)
        with self._lock:
            self._subs.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        with self._lock:
            try:
                self._subs.remove(q)
            except ValueError:
                pass

    def list_recent(self, limit: int = MAX_BUFFER) -> list[WorkbenchCard]:
        with self._lock:
            items = list(self._buffer)
        return items[-limit:]


_BROKERS: dict[str, _AgentBroker] = {}
_BROKERS_LOCK = threading.Lock()


def get_broker(agent_id: str) -> _AgentBroker:
    with _BROKERS_LOCK:
        b = _BROKERS.get(agent_id)
        if b is None:
            b = _AgentBroker(agent_id)
            _BROKERS[agent_id] = b
        return b


def publish_card(
    *,
    agent_id: str,
    kind: str,
    title: str,
    summary: str = "",
    card_id: Optional[str] = None,
    href: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
) -> WorkbenchCard:
    card = WorkbenchCard(
        id=card_id or uuid.uuid4().hex,
        agent_id=agent_id,
        kind=kind,
        title=title,
        summary=summary,
        href=href,
        payload=payload or {},
    )
    get_broker(agent_id).publish(card)
    return card