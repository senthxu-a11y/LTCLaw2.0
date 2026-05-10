from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .code_indexer import CodeFileIndex
from .models import TableIndex
from ..knowledge_base import get_kb_store
from .paths import get_knowledge_base_dir, get_retrieval_dir
from ..knowledge_base.local_vector_store import _tokens as tokenize


_DOC_EXTENSIONS = {".md", ".markdown", ".txt", ".html", ".htm"}
_DOC_NOISE_PARTS = {
    ".git",
    ".svn",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
    "tmp",
    "temp",
    "__pycache__",
}
_DOC_NOISE_PREFIXES = (
    ".ltclaw_index/",
    "console/dist/",
    "website/dist/",
)
_DOC_TEXT_LIMIT = 120000
_DOC_CHUNK_SIZE = 1200
_DOC_CHUNK_OVERLAP = 180


def _retrieval_dir(workspace_dir: Path, svn_root: Path | None = None) -> Path:
    base = get_retrieval_dir(workspace_dir, svn_root)
    base.mkdir(parents=True, exist_ok=True)
    return base


def _retrieval_status_path(workspace_dir: Path, svn_root: Path | None = None) -> Path:
    return _retrieval_dir(workspace_dir, svn_root) / "status.json"


def _doc_chunk_path(workspace_dir: Path, svn_root: Path | None = None) -> Path:
    return _retrieval_dir(workspace_dir, svn_root) / "doc_chunks.jsonl"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _normalize_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"))


def _read_text_file(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except Exception:
            continue
    else:
        text = raw.decode("utf-8", errors="replace")
    text = _normalize_text(text)
    if len(text) > _DOC_TEXT_LIMIT:
        text = text[:_DOC_TEXT_LIMIT]
    return text


def _summarize(text: str, limit: int = 220) -> str:
    normalized = " ".join(part.strip() for part in text.splitlines() if part.strip())
    return normalized[:limit]


def _chunk_text(text: str, size: int = _DOC_CHUNK_SIZE, overlap: int = _DOC_CHUNK_OVERLAP) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    if not text.strip():
        return chunks
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(text_len, start + size)
        if end < text_len:
            boundary = text.rfind("\n", start, end)
            if boundary > start + size // 2:
                end = boundary
        chunk = text[start:end].strip()
        if chunk:
            chunks.append({"offset_start": start, "offset_end": end, "text": chunk})
        if end >= text_len:
            break
        start = max(end - overlap, start + 1)
    return chunks


def _score_text(query: str, text: str) -> float:
    query_tokens = tokenize(query)
    text_tokens = tokenize(text)
    if not query_tokens or not text_tokens:
        return 0.0
    query_set = set(query_tokens)
    text_set = set(text_tokens)
    overlap = len(query_set & text_set)
    coverage = overlap / max(1, len(query_set))
    density = overlap / max(1, len(text_set))
    phrase_bonus = 0.2 if query.lower() in text.lower() else 0.0
    return coverage * 0.75 + density * 0.25 + phrase_bonus


def _hash_chunk(doc_id: str, offset_start: int, offset_end: int) -> str:
    return hashlib.sha1(f"{doc_id}:{offset_start}:{offset_end}".encode("utf-8")).hexdigest()[:16]


def _resolve_svn_root(game_service) -> Path | None:
    root = getattr(game_service.user_config, "svn_local_root", None)
    if not root and getattr(game_service, "project_config", None) is not None:
        root = game_service.project_config.svn.root
    if not root:
        return None
    path = Path(root).expanduser()
    return path if path.exists() else None


def _iter_doc_roots(game_service, svn_root: Path) -> list[Path]:
    config = getattr(game_service, "project_config", None)
    roots: list[Path] = []
    seen: set[str] = set()

    def add_root(path: Path) -> None:
        if not path.exists():
            return
        key = str(path.resolve())
        if key in seen:
            return
        seen.add(key)
        roots.append(path)

    if config is not None:
        for rule in config.paths:
            if rule.semantic not in {"doc", "template"}:
                continue
            pattern = str(rule.path or "").strip().replace("\\", "/")
            if not pattern:
                continue
            if any(ch in pattern for ch in "*?[]"):
                for matched in svn_root.glob(pattern):
                    add_root(matched if matched.is_dir() else matched.parent)
            else:
                add_root(svn_root / pattern)

    if not roots:
        add_root(svn_root / "docs")
    if not roots:
        add_root(svn_root)
    return roots


def _is_doc_noise(relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/")
    if any(normalized.startswith(prefix) for prefix in _DOC_NOISE_PREFIXES):
        return True
    parts = [part for part in Path(normalized).parts if part not in {"", "."}]
    return any(part in _DOC_NOISE_PARTS for part in parts)


def _collect_confirmed_doc_entries(workspace_dir: Path, svn_root: Path | None = None) -> dict[str, dict[str, Any]]:
    kb_store = get_kb_store(get_knowledge_base_dir(workspace_dir, svn_root))
    docs: dict[str, dict[str, Any]] = {}
    for entry in kb_store.list_entries():
        if entry.source != "doc_library":
            continue
        doc_path = str(entry.extra.get("doc_path") or "").strip()
        if not doc_path:
            continue
        docs[doc_path] = {
            "kb_entry_id": entry.id,
            "title": entry.title,
            "category": entry.category,
            "tags": list(entry.tags or []),
            "extra": dict(entry.extra or {}),
        }
    return docs


def rebuild_doc_chunk_index(workspace_dir: Path, game_service) -> dict[str, Any]:
    svn_root = _resolve_svn_root(game_service)
    if svn_root is None:
        status = {
            "last_built_at": _now_iso(),
            "configured": False,
            "doc_count": 0,
            "doc_chunk_count": 0,
        }
        _retrieval_status_path(workspace_dir, svn_root).write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        _doc_chunk_path(workspace_dir, svn_root).write_text("", encoding="utf-8")
        return status

    confirmed_docs = _collect_confirmed_doc_entries(workspace_dir, svn_root)
    records: list[dict[str, Any]] = []
    doc_count = 0
    for root in _iter_doc_roots(game_service, svn_root):
        candidates = [root] if root.is_file() else root.rglob("*")
        for path in candidates:
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix not in _DOC_EXTENSIONS:
                continue
            relative_path = path.relative_to(svn_root).as_posix()
            if _is_doc_noise(relative_path):
                continue
            confirmed = confirmed_docs.get(relative_path)
            if confirmed is None:
                continue
            text = _read_text_file(path)
            if not text.strip():
                continue
            doc_count += 1
            title = confirmed.get("title") or path.stem
            category = confirmed.get("category") or "doc:general"
            tags = list(confirmed.get("tags") or [])
            kb_entry_id = confirmed.get("kb_entry_id")
            updated_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
            for chunk in _chunk_text(text):
                chunk_id = _hash_chunk(relative_path, chunk["offset_start"], chunk["offset_end"])
                records.append({
                    "chunk_id": chunk_id,
                    "doc_id": relative_path,
                    "doc_path": relative_path,
                    "kb_entry_id": kb_entry_id,
                    "title": title,
                    "category": category,
                    "tags": tags,
                    "offset_start": chunk["offset_start"],
                    "offset_end": chunk["offset_end"],
                    "summary": _summarize(chunk["text"], 260),
                    "text": chunk["text"],
                    "updated_at": updated_at,
                })

    chunk_path = _doc_chunk_path(workspace_dir, svn_root)
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    chunk_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    status = {
        "last_built_at": _now_iso(),
        "configured": True,
        "doc_count": doc_count,
        "doc_chunk_count": len(records),
    }
    _retrieval_status_path(workspace_dir, svn_root).write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    return status



def load_doc_chunk_index(workspace_dir: Path, game_service, rebuild: bool = False) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    svn_root = _resolve_svn_root(game_service)
    chunk_path = _doc_chunk_path(workspace_dir, svn_root)
    status_path = _retrieval_status_path(workspace_dir, svn_root)
    if rebuild or not chunk_path.exists() or not status_path.exists():
        status = rebuild_doc_chunk_index(workspace_dir, game_service)
    else:
        try:
            status = json.loads(status_path.read_text(encoding="utf-8"))
        except Exception:
            status = rebuild_doc_chunk_index(workspace_dir, game_service)
    records: list[dict[str, Any]] = []
    if chunk_path.exists():
        for line in chunk_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except Exception:
                continue
    return records, status


def get_retrieval_status(game_service, *, rebuild_doc_index: bool = False) -> dict[str, Any]:
    workspace_dir = Path(game_service.workspace_dir)
    _, status = load_doc_chunk_index(workspace_dir, game_service, rebuild=rebuild_doc_index)
    svn_root = _resolve_svn_root(game_service)
    kb_store = get_kb_store(get_knowledge_base_dir(workspace_dir, svn_root))
    tables = []
    if getattr(game_service, "index_committer", None) is not None:
        tables = game_service.index_committer.load_table_indexes() or []
        dep = game_service.index_committer.load_dependency_graph()
        status["dependency_edge_count"] = len(getattr(dep, "edges", []) or []) if dep else 0
    code_files = []
    if getattr(game_service, "code_index_store", None) is not None:
        code_files = game_service.code_index_store.load_all()
    status["kb_entry_count"] = kb_store.size
    status["table_count"] = len(tables)
    status["code_file_count"] = len(code_files)
    return status


def _table_results(query: str, tables: Iterable[TableIndex], limit: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for table in tables:
        haystack = " ".join([
            table.table_name,
            table.ai_summary or "",
            table.system or "",
            " ".join(field.name for field in table.fields),
        ])
        score = _score_text(query, haystack)
        if score <= 0:
            continue
        results.append({
            "source_type": "table",
            "score": score,
            "title": table.table_name,
            "summary": _summarize(table.ai_summary or table.table_name),
            "content": table.ai_summary or "",
            "table": table.table_name,
            "system": table.system,
            "row_count": table.row_count,
            "source_path": table.source_path,
            "evidence": {
                "table": table.table_name,
                "path": table.source_path,
                "system": table.system,
            },
        })
        for field in table.fields:
            field_haystack = f"{table.table_name} {field.name} {field.description} {' '.join(field.tags or [])}"
            field_score = _score_text(query, field_haystack)
            if field_score <= 0:
                continue
            results.append({
                "source_type": "field",
                "score": field_score + 0.05,
                "title": f"{table.table_name}.{field.name}",
                "summary": _summarize(field.description or field.name),
                "content": field.description or "",
                "table": table.table_name,
                "field": field.name,
                "source_path": table.source_path,
                "evidence": {
                    "table": table.table_name,
                    "field": field.name,
                    "path": table.source_path,
                },
            })
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:limit]


def _code_results(query: str, code_entries: Iterable[CodeFileIndex], limit: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for entry in code_entries:
        for symbol in entry.symbols:
            text = " ".join([
                entry.source_path,
                entry.namespace or "",
                symbol.name,
                symbol.signature or "",
                symbol.summary or "",
            ])
            score = _score_text(query, text)
            if score > 0:
                results.append({
                    "source_type": "code_symbol",
                    "score": score,
                    "title": symbol.name,
                    "summary": _summarize(symbol.summary or symbol.signature or entry.source_path),
                    "content": symbol.signature or symbol.summary or "",
                    "source_path": entry.source_path,
                    "evidence": {
                        "path": entry.source_path,
                        "symbol": symbol.name,
                        "kind": symbol.kind,
                        "line_start": symbol.line_start,
                        "line_end": symbol.line_end,
                    },
                })
            for ref in symbol.references:
                ref_text = " ".join([
                    entry.source_path,
                    symbol.name,
                    ref.target_table or "",
                    ref.target_field or "",
                    ref.target_symbol or "",
                    ref.snippet or "",
                ])
                ref_score = _score_text(query, ref_text)
                if ref_score <= 0:
                    continue
                title = ref.target_symbol or ref.target_table or symbol.name
                results.append({
                    "source_type": "code_reference",
                    "score": ref_score + 0.03,
                    "title": title,
                    "summary": _summarize(ref.snippet or symbol.signature or entry.source_path),
                    "content": ref.snippet or "",
                    "source_path": entry.source_path,
                    "evidence": {
                        "path": entry.source_path,
                        "symbol": symbol.name,
                        "line": ref.line,
                        "target_table": ref.target_table,
                        "target_field": ref.target_field,
                        "target_symbol": ref.target_symbol,
                    },
                })
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:limit]


def unified_search(game_service, query: str, *, top_k: int = 8, mode: str = "hybrid", rebuild_doc_index: bool = False) -> dict[str, Any]:
    query = (query or "").strip()
    workspace_dir = Path(game_service.workspace_dir)
    if not query:
        return {"query": query, "mode": mode, "results": [], "status": {}}

    status: dict[str, Any] = {}
    results: list[dict[str, Any]] = []

    svn_root = _resolve_svn_root(game_service)
    kb_store = get_kb_store(get_knowledge_base_dir(workspace_dir, svn_root))
    kb_hits = kb_store.search(query, top_k=max(top_k * 2, 10), mode="hybrid")
    for entry, score in kb_hits:
        results.append({
            "source_type": "kb_entry",
            "score": float(score) + 0.02,
            "title": entry.title,
            "summary": _summarize(entry.summary or entry.title),
            "content": entry.summary or "",
            "category": entry.category,
            "source": entry.source,
            "source_path": entry.extra.get("doc_path") or entry.extra.get("path"),
            "kb_entry_id": entry.id,
            "evidence": {
                "kb_entry_id": entry.id,
                "path": entry.extra.get("doc_path") or entry.extra.get("path"),
                "source": entry.source,
            },
        })

    doc_chunks, doc_status = load_doc_chunk_index(workspace_dir, game_service, rebuild=rebuild_doc_index)
    status.update(doc_status)
    for chunk in doc_chunks:
        score = _score_text(query, f"{chunk.get('title', '')} {chunk.get('summary', '')} {chunk.get('text', '')}")
        if score <= 0:
            continue
        results.append({
            "source_type": "doc_chunk",
            "score": score + 0.08,
            "title": chunk.get("title") or chunk.get("doc_id"),
            "summary": chunk.get("summary") or "",
            "content": chunk.get("text") or "",
            "category": chunk.get("category"),
            "source_path": chunk.get("doc_path"),
            "kb_entry_id": chunk.get("kb_entry_id"),
            "evidence": {
                "chunk_id": chunk.get("chunk_id"),
                "path": chunk.get("doc_path"),
                "offset_start": chunk.get("offset_start"),
                "offset_end": chunk.get("offset_end"),
                "kb_entry_id": chunk.get("kb_entry_id"),
            },
        })

    tables = []
    if getattr(game_service, "index_committer", None) is not None:
        tables = game_service.index_committer.load_table_indexes() or []
        results.extend(_table_results(query, tables, max(top_k * 2, 10)))
        dep = game_service.index_committer.load_dependency_graph()
        status["dependency_edge_count"] = len(getattr(dep, "edges", []) or []) if dep else 0
    status["table_count"] = len(tables)

    code_entries = []
    if getattr(game_service, "code_index_store", None) is not None:
        code_entries = game_service.code_index_store.load_all()
        results.extend(_code_results(query, code_entries, max(top_k * 2, 10)))
    status["code_file_count"] = len(code_entries)
    status["kb_entry_count"] = kb_store.size

    deduped: dict[tuple[str, str], dict[str, Any]] = {}
    for item in results:
        source_key = item.get("source_path") or json.dumps(item.get("evidence") or {}, ensure_ascii=False, sort_keys=True)
        key = (str(item.get("source_type") or "unknown"), str(source_key))
        existing = deduped.get(key)
        if existing is None or float(item.get("score") or 0.0) > float(existing.get("score") or 0.0):
            deduped[key] = item

    merged = sorted(deduped.values(), key=lambda item: float(item.get("score") or 0.0), reverse=True)
    if mode == "exact":
        merged = [item for item in merged if item["source_type"] in {"table", "field"}]
    elif mode == "semantic":
        merged = [item for item in merged if item["source_type"] in {"doc_chunk", "kb_entry", "code_symbol", "code_reference"}]

    return {
        "query": query,
        "mode": mode,
        "results": merged[:top_k],
        "status": status,
    }


def build_chat_context_block(search_payload: dict[str, Any], *, max_items: int = 6) -> str:
    results = list(search_payload.get("results") or [])[:max_items]
    if not results:
        return ""
    lines = [
        "[?????] ?????????????????????????????????",
    ]
    for idx, item in enumerate(results, start=1):
        evidence = item.get("evidence") or {}
        path = evidence.get("path") or item.get("source_path") or ""
        source_type = item.get("source_type") or "unknown"
        summary = item.get("summary") or item.get("content") or ""
        score = float(item.get("score") or 0.0)
        lines.append(f"{idx}. [{source_type}] {item.get('title', '')} | score={score:.3f} | source={path}")
        if summary:
            lines.append(f"   ??: {summary[:280]}")
    return "\n".join(lines)
