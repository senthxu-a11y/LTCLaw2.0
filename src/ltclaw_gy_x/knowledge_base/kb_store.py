"""KB store: JSONL-backed entries + hybrid search."""
from __future__ import annotations

import json
import math
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Iterable

from .local_vector_store import LocalVectorStore, _tokens as _vs_tokens

_BM25_K1 = 1.5
_BM25_B = 0.75


def _minmax(values):
    if not values:
        return []
    lo = min(values); hi = max(values)
    if hi <= lo:
        return [0.0 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


@dataclass
class KnowledgeBaseEntry:
    id: str
    title: str
    summary: str = ""
    category: str = "general"
    source: str = "manual"
    tags: list = field(default_factory=list)
    extra: dict = field(default_factory=dict)
    created_at: float = 0.0

    def to_dict(self):
        return asdict(self)

    def index_text(self):
        parts = [self.title, self.summary, self.category, self.source]
        parts.extend(self.tags or [])
        return " ".join(p for p in parts if p)


class KnowledgeBaseStore:
    def __init__(self, workspace_dir):
        self._workspace = Path(workspace_dir)
        self._dir = self._workspace / "knowledge_base"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._jsonl = self._dir / "entries.jsonl"
        self._lock = threading.RLock()
        self._entries = {}
        self._vector = LocalVectorStore(dim=4096)
        self._kw_postings = {}
        self._kw_doc_len = {}
        self._load()

    def _load(self):
        if not self._jsonl.exists():
            return
        with self._lock:
            for line in self._jsonl.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                e = KnowledgeBaseEntry(
                    id=str(d.get("id") or uuid.uuid4().hex[:12]),
                    title=str(d.get("title") or ""),
                    summary=str(d.get("summary") or ""),
                    category=str(d.get("category") or "general"),
                    source=str(d.get("source") or "manual"),
                    tags=list(d.get("tags") or []),
                    extra=dict(d.get("extra") or {}),
                    created_at=float(d.get("created_at") or 0.0),
                )
                self._entries[e.id] = e
            self._rebuild_index()

    def _persist_all(self):
        tmp = self._jsonl.with_suffix(".jsonl.tmp")
        lines = [json.dumps(e.to_dict(), ensure_ascii=False) for e in self._entries.values()]
        tmp.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        tmp.replace(self._jsonl)

    def _rebuild_index(self):
        self._vector.bulk_load((e.id, e.index_text()) for e in self._entries.values())
        self._rebuild_kw_index()

    def _rebuild_kw_index(self):
        self._kw_postings = {}
        self._kw_doc_len = {}
        for e in self._entries.values():
            self._index_doc_kw(e)

    def _index_doc_kw(self, entry):
        toks = _vs_tokens(entry.index_text())
        self._kw_doc_len[entry.id] = len(toks)
        counts = {}
        for t in toks:
            counts[t] = counts.get(t, 0) + 1
        for tok, c in counts.items():
            self._kw_postings.setdefault(tok, {})[entry.id] = c

    def _unindex_doc_kw(self, entry_id):
        self._kw_doc_len.pop(entry_id, None)
        empty = []
        for tok, posting in self._kw_postings.items():
            if entry_id in posting:
                del posting[entry_id]
                if not posting:
                    empty.append(tok)
        for tok in empty:
            del self._kw_postings[tok]

    def _bm25_search(self, query, top_k):
        q_toks = _vs_tokens(query)
        if not q_toks or not self._entries:
            return []
        n = len(self._entries) or 1
        avgdl = sum(self._kw_doc_len.values()) / n if self._kw_doc_len else 1.0
        scores = {}
        seen_q = set()
        for qt in q_toks:
            if qt in seen_q:
                continue
            seen_q.add(qt)
            posting = self._kw_postings.get(qt)
            if not posting:
                continue
            df = len(posting)
            idf = math.log(1.0 + (n - df + 0.5) / (df + 0.5))
            for doc_id, tf in posting.items():
                dl = self._kw_doc_len.get(doc_id, 0) or 1
                denom = tf + _BM25_K1 * (1 - _BM25_B + _BM25_B * dl / (avgdl or 1.0))
                score = idf * (tf * (_BM25_K1 + 1)) / (denom or 1.0)
                scores[doc_id] = scores.get(doc_id, 0.0) + score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    def add(self, title, summary="", category="general", source="manual", tags=None, extra=None):
        with self._lock:
            entry = KnowledgeBaseEntry(
                id=uuid.uuid4().hex[:12],
                title=title,
                summary=summary,
                category=category,
                source=source,
                tags=list(tags or []),
                extra=dict(extra or {}),
                created_at=time.time(),
            )
            self._entries[entry.id] = entry
            self._vector.add(entry.id, entry.index_text())
            self._index_doc_kw(entry)
            self._persist_all()
            return entry

    def update(self, entry_id, **fields_in):
        with self._lock:
            entry = self._entries.get(entry_id)
            if entry is None:
                return None
            for k in ("title", "summary", "category", "source"):
                if k in fields_in and fields_in[k] is not None:
                    setattr(entry, k, fields_in[k])
            if "tags" in fields_in and fields_in["tags"] is not None:
                entry.tags = list(fields_in["tags"])
            if "extra" in fields_in and fields_in["extra"] is not None:
                entry.extra = dict(fields_in["extra"])
            self._vector.add(entry.id, entry.index_text())
            self._unindex_doc_kw(entry.id)
            self._index_doc_kw(entry)
            self._persist_all()
            return entry

    def delete(self, entry_id):
        with self._lock:
            if entry_id not in self._entries:
                return False
            del self._entries[entry_id]
            self._vector.remove(entry_id)
            self._unindex_doc_kw(entry_id)
            self._persist_all()
            return True

    def get(self, entry_id):
        return self._entries.get(entry_id)

    def list_entries(self):
        with self._lock:
            return sorted(self._entries.values(), key=lambda e: e.created_at, reverse=True)

    def search(self, query, top_k=10, category=None, mode="hybrid", alpha=0.6):
        query = (query or "").strip()
        if not query or not self._entries:
            return []
        pool = top_k * 3 if (mode == "hybrid" or category) else top_k
        with self._lock:
            vec_hits = dict(self._vector.search(query, top_k=pool))
            kw_hits = dict(self._bm25_search(query, top_k=pool))
            if mode == "vector":
                merged = vec_hits
            elif mode == "keyword":
                merged = kw_hits
            else:
                ids = list(set(vec_hits) | set(kw_hits))
                v_norm = dict(zip(ids, _minmax([vec_hits.get(i, 0.0) for i in ids])))
                k_norm = dict(zip(ids, _minmax([kw_hits.get(i, 0.0) for i in ids])))
                merged = {i: alpha * v_norm.get(i, 0.0) + (1 - alpha) * k_norm.get(i, 0.0) for i in ids}
            results = []
            for doc_id, score in sorted(merged.items(), key=lambda x: x[1], reverse=True):
                e = self._entries.get(doc_id)
                if e is None:
                    continue
                if category and e.category != category:
                    continue
                results.append((e, float(score)))
                if len(results) >= top_k:
                    break
            return results

    @property
    def size(self):
        return len(self._entries)


_INSTANCES = {}
_INSTANCES_LOCK = threading.Lock()


def get_kb_store(workspace_dir):
    key = str(Path(workspace_dir).resolve())
    with _INSTANCES_LOCK:
        inst = _INSTANCES.get(key)
        if inst is None:
            inst = KnowledgeBaseStore(workspace_dir)
            _INSTANCES[key] = inst
        return inst