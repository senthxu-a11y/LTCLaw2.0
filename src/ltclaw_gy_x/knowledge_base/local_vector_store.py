"""Zero-dep hashing TF-IDF vector store with cosine similarity."""
from __future__ import annotations

import hashlib
import math
import re
import threading
from dataclasses import dataclass, field
from typing import Iterable


_TOKEN_RE = re.compile(r"[A-Za-z0-9]+|[\u4e00-\u9fff]")


def _tokens(text: str) -> list[str]:
    if not text:
        return []
    raw = text.lower()
    out: list[str] = []
    out.extend(_TOKEN_RE.findall(raw))
    cjk = "".join(c for c in raw if "\u4e00" <= c <= "\u9fff")
    for i in range(len(cjk) - 1):
        out.append(cjk[i:i + 2])
    return out


def _hash_token(tok: str, dim: int) -> int:
    h = hashlib.md5(tok.encode("utf-8")).digest()
    return int.from_bytes(h[:4], "big") % dim


@dataclass
class _Doc:
    doc_id: str
    text: str
    vec: dict[int, float] = field(default_factory=dict)
    norm: float = 0.0


class LocalVectorStore:
    """Hashing TF-IDF cosine similarity, fully in-memory."""

    def __init__(self, dim: int = 4096) -> None:
        self._dim = dim
        self._docs: dict[str, _Doc] = {}
        self._df: dict[int, int] = {}
        self._lock = threading.RLock()

    def _tf(self, text: str) -> dict[int, float]:
        toks = _tokens(text)
        if not toks:
            return {}
        counts: dict[int, int] = {}
        for t in toks:
            h = _hash_token(t, self._dim)
            counts[h] = counts.get(h, 0) + 1
        total = sum(counts.values())
        return {h: c / total for h, c in counts.items()}

    def _idf(self, h: int) -> float:
        n = max(len(self._docs), 1)
        df = self._df.get(h, 0)
        return math.log((1 + n) / (1 + df)) + 1.0

    def _rebuild_doc_vec(self, doc: _Doc) -> None:
        tf = self._tf(doc.text)
        vec = {h: w * self._idf(h) for h, w in tf.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        doc.vec = vec
        doc.norm = norm

    def _rebuild_all(self) -> None:
        for d in self._docs.values():
            self._rebuild_doc_vec(d)

    def add(self, doc_id: str, text: str) -> None:
        with self._lock:
            old = self._docs.get(doc_id)
            if old is not None:
                for h in set(_hash_token(t, self._dim) for t in _tokens(old.text)):
                    self._df[h] = max(self._df.get(h, 1) - 1, 0)
            doc = _Doc(doc_id=doc_id, text=text)
            self._docs[doc_id] = doc
            seen: set[int] = set()
            for tok in _tokens(text):
                h = _hash_token(tok, self._dim)
                if h not in seen:
                    self._df[h] = self._df.get(h, 0) + 1
                    seen.add(h)
            self._rebuild_all()

    def remove(self, doc_id: str) -> bool:
        with self._lock:
            old = self._docs.pop(doc_id, None)
            if old is None:
                return False
            for h in set(_hash_token(t, self._dim) for t in _tokens(old.text)):
                self._df[h] = max(self._df.get(h, 1) - 1, 0)
            self._rebuild_all()
            return True

    def clear(self) -> None:
        with self._lock:
            self._docs.clear()
            self._df.clear()

    def search(self, query: str, top_k: int = 10, min_score: float = 0.0):
        with self._lock:
            if not self._docs:
                return []
            q_tf = self._tf(query)
            if not q_tf:
                return []
            q_vec = {h: w * self._idf(h) for h, w in q_tf.items()}
            q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0
            scored: list[tuple[str, float]] = []
            for doc in self._docs.values():
                a, b = (q_vec, doc.vec) if len(q_vec) <= len(doc.vec) else (doc.vec, q_vec)
                dot = 0.0
                for h, w in a.items():
                    other = b.get(h)
                    if other is not None:
                        dot += w * other
                if dot <= 0:
                    continue
                score = dot / (q_norm * doc.norm)
                if score >= min_score:
                    scored.append((doc.doc_id, score))
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:top_k]

    def bulk_load(self, items: Iterable[tuple[str, str]]) -> None:
        with self._lock:
            self._docs.clear()
            self._df.clear()
            for doc_id, text in items:
                doc = _Doc(doc_id=doc_id, text=text)
                self._docs[doc_id] = doc
                seen: set[int] = set()
                for tok in _tokens(text):
                    h = _hash_token(tok, self._dim)
                    if h not in seen:
                        self._df[h] = self._df.get(h, 0) + 1
                        seen.add(h)
            self._rebuild_all()

    @property
    def size(self) -> int:
        return len(self._docs)