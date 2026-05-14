from __future__ import annotations

import fnmatch
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from ..agent_context import get_agent_for_request
from ...game.retrieval import get_retrieval_status
from ...knowledge_base import get_kb_store


router = APIRouter(prefix="/game-doc-library", tags=["game-doc-library"])

LEGACY_DOC_LIBRARY_SYNC_MODE = "legacy_kb_migration_only"


_DOC_EXTENSIONS = {
    ".md": "Markdown",
    ".markdown": "Markdown",
    ".txt": "??",
    ".doc": "Word",
    ".docx": "Word",
    ".html": "HTML",
    ".htm": "HTML",
    ".pdf": "PDF",
}

_STATUS_RULES = (
    ("draft", "??"),
    ("drafts", "??"),
    ("wip", "??"),
    ("review", "???"),
    ("pending", "???"),
    ("archive", "??"),
    ("archived", "??"),
    ("final", "???"),
    ("approved", "???"),
    ("release", "???"),
)

_COMMON_DOC_DIRS = ("docs", "Docs", "document", "documents", "design", "Design", "??", "??")
_DOC_LIBRARY_DIR = ("game_index", "doc_library")
_SUPPORTED_TEXT_EXTENSIONS = {".md", ".markdown", ".txt", ".html", ".htm"}
_VALID_STATUSES = {"??", "???", "???", "??"}
_NOISE_PARTS = {".git", ".svn", "node_modules", "dist", "build", ".next", ".nuxt", "coverage", "tmp", "temp", "__pycache__"}
_NOISE_PREFIXES = (".ltclaw_index/", "console/dist/", "website/dist/")


def _game_service_or_404(workspace):
    svc = workspace.service_manager.services.get("game_service")
    if svc is None:
        raise HTTPException(status_code=404, detail="Game service not available")
    return svc


def _normalize_pattern(pattern: str) -> str:
    return pattern.strip().replace("\\", "/")


def _has_glob(pattern: str) -> bool:
    return any(ch in pattern for ch in "*?[]")


def _is_excluded(relative_path: str, patterns: list[str]) -> bool:
    path_text = relative_path.replace("\\", "/")
    if "/.svn/" in f"/{path_text}/" or path_text.startswith(".svn/"):
        return True
    if "/.ltclaw_index/" in f"/{path_text}/" or path_text.startswith(".ltclaw_index/"):
        return True
    if any(path_text.startswith(prefix) for prefix in _NOISE_PREFIXES):
        return True
    parts = [part for part in Path(path_text).parts if part not in {"", "."}]
    if any(part in _NOISE_PARTS for part in parts):
        return True
    for pattern in patterns:
        normalized = _normalize_pattern(pattern)
        if normalized and fnmatch.fnmatch(path_text, normalized):
            return True
    return False


def _resolve_svn_root(game_service) -> Path | None:
    root = game_service.user_config.svn_local_root
    if not root and game_service.project_config is not None:
        root = game_service.project_config.svn.root
    if not root:
        return None
    svn_root = Path(root).expanduser()
    if not svn_root.exists():
        return None
    return svn_root


def _resolve_doc_roots(svn_root: Path, game_service) -> list[Path]:
    config = game_service.project_config
    roots: list[Path] = []
    seen: set[str] = set()

    def add_root(path: Path) -> None:
        try:
            resolved = path.resolve()
        except Exception:
            resolved = path
        key = str(resolved)
        if key in seen or not path.exists():
            return
        seen.add(key)
        roots.append(path)

    if config is not None:
        for rule in config.paths:
            if rule.semantic not in {"doc", "template"}:
                continue
            pattern = _normalize_pattern(rule.path)
            if not pattern:
                continue
            if _has_glob(pattern):
                for matched in svn_root.glob(pattern):
                    add_root(matched if matched.is_dir() else matched.parent)
            else:
                add_root((svn_root / pattern))

    for dirname in _COMMON_DOC_DIRS:
        add_root(svn_root / dirname)

    if not roots:
        add_root(svn_root)
    return roots


def _guess_status(relative_path: str) -> str:
    lowered = relative_path.lower().replace("\\", "/")
    for needle, status in _STATUS_RULES:
        if f"/{needle}/" in f"/{lowered}/" or lowered.startswith(f"{needle}/"):
            return status
    return "???"


def _guess_category(relative_path: str) -> str:
    parts = [part for part in Path(relative_path).parts[:-1] if part not in {".", ""}]
    if not parts:
        return "???"
    ignored = {"docs", "Docs", "document", "documents", "design", "Design"}
    for part in parts:
        if part not in ignored:
            return part
    return parts[0]


def _build_tags(relative_path: str, suffix: str) -> list[str]:
    tags: list[str] = []
    parts = [part for part in Path(relative_path).parts[:-1] if part not in {".", ""}]
    for part in parts[:2]:
        if part not in tags:
            tags.append(part)
    type_tag = _DOC_EXTENSIONS.get(suffix.lower())
    if type_tag and type_tag not in tags:
        tags.append(type_tag)
    return tags


def _serialize_document(path: Path, svn_root: Path) -> dict[str, Any]:
    stat = path.stat()
    relative_path = path.relative_to(svn_root).as_posix()
    suffix = path.suffix.lower()
    return {
        "id": relative_path,
        "title": path.stem,
        "type": _DOC_EXTENSIONS.get(suffix, suffix.lstrip(".").upper() or "??"),
        "status": _guess_status(relative_path),
        "updated_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
        "author": "system",
        "category": _guess_category(relative_path),
        "tags": _build_tags(relative_path, suffix),
        "path": relative_path,
    }


def _doc_library_state_path(workspace_dir: Path) -> Path:
    base_dir = workspace_dir.joinpath(*_DOC_LIBRARY_DIR)
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / "state.json"


def _load_doc_library_state(workspace_dir: Path) -> dict[str, Any]:
    state_path = _doc_library_state_path(workspace_dir)
    if not state_path.exists():
        return {"documents": {}}
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return {"documents": {}}
    documents = payload.get("documents")
    if not isinstance(documents, dict):
        return {"documents": {}}
    return {"documents": documents}



def _save_doc_library_state(workspace_dir: Path, state: dict[str, Any]) -> None:
    state_path = _doc_library_state_path(workspace_dir)
    tmp_path = state_path.with_suffix(".json.tmp")
    tmp_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    tmp_path.replace(state_path)


def _get_document_meta(state: dict[str, Any], doc_id: str) -> dict[str, Any]:
    documents = state.setdefault("documents", {})
    meta = documents.get(doc_id)
    if isinstance(meta, dict):
        return meta
    meta = {}
    documents[doc_id] = meta
    return meta


def _merge_document_meta(document: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    merged = dict(document)
    if isinstance(meta.get("status"), str) and meta["status"] in _VALID_STATUSES:
        merged["status"] = meta["status"]
    if isinstance(meta.get("title"), str) and meta["title"].strip():
        merged["title"] = meta["title"].strip()
    if isinstance(meta.get("category"), str) and meta["category"].strip():
        merged["category"] = meta["category"].strip()
    if isinstance(meta.get("author"), str) and meta["author"].strip():
        merged["author"] = meta["author"].strip()
    if isinstance(meta.get("tags"), list):
        merged["tags"] = [str(tag) for tag in meta["tags"] if str(tag).strip()]
    return merged


def _resolve_document_path(svn_root: Path, doc_id: str) -> Path:
    candidate = (svn_root / doc_id).resolve()
    svn_root_resolved = svn_root.resolve()
    try:
        candidate.relative_to(svn_root_resolved)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid document path") from exc
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail="document not found")
    return candidate


def _read_document_content(path: Path) -> tuple[str, str, bool]:
    suffix = path.suffix.lower()
    if suffix not in _SUPPORTED_TEXT_EXTENSIONS:
        return ("?????????????????????????????", "unsupported", False)
    raw = path.read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except Exception:
            continue
    else:
        text = raw.decode("utf-8", errors="replace")
    truncated = False
    if len(text) > 120000:
        text = text[:120000] + "\n\n... [?????]"
        truncated = True
    preview_kind = "markdown" if suffix in {".md", ".markdown"} else "text"
    return (text, preview_kind, truncated)


def _document_summary(content: str) -> str:
    normalized = " ".join(line.strip() for line in content.splitlines() if line.strip())
    return normalized[:400]


def _sync_document_to_kb(workspace_dir: Path, document: dict[str, Any], content: str, meta: dict[str, Any]) -> str | None:
    """Maintain a legacy KB mirror for migration/debug only.

    This sync path does not participate in formal release, RAG, or workbench-suggest.
    """
    if document.get("status") != "???":
        return meta.get("kb_entry_id") if isinstance(meta.get("kb_entry_id"), str) else None

    kb_store = get_kb_store(workspace_dir)
    kb_entry_id = meta.get("kb_entry_id") if isinstance(meta.get("kb_entry_id"), str) else None
    entry = kb_store.get(kb_entry_id) if kb_entry_id else None

    if entry is None:
        for candidate in kb_store.list_entries():
            if candidate.source != "doc_library":
                continue
            if candidate.extra.get("doc_path") == document["id"]:
                entry = candidate
                kb_entry_id = candidate.id
                break

    payload = {
        "title": document["title"],
        "summary": _document_summary(content),
        "category": f"doc:{document['category']}",
        "source": "doc_library",
        "tags": list(document.get("tags") or []),
        "extra": {
            "doc_id": document["id"],
            "doc_path": document["path"],
            "doc_status": document["status"],
            "doc_type": document["type"],
        },
    }

    if entry is None:
        created = kb_store.add(**payload)
        return created.id

    updated = kb_store.update(entry.id, **payload)
    return updated.id if updated is not None else entry.id


def _collect_documents(workspace, svn_root: Path) -> list[dict[str, Any]]:
    game_service = _game_service_or_404(workspace)
    config = game_service.project_config
    include_ext = {ext.lower() for ext in (config.filters.include_ext if config is not None else [])}
    allowed_ext = set(_DOC_EXTENSIONS)
    if include_ext:
        allowed_ext &= include_ext
    if not allowed_ext:
        allowed_ext = set(_DOC_EXTENSIONS)
    exclude_patterns = list(config.filters.exclude_glob if config is not None else [])
    state = _load_doc_library_state(workspace.workspace_dir)

    docs: dict[str, dict[str, Any]] = {}
    for root in _resolve_doc_roots(svn_root, game_service):
        candidates = [root] if root.is_file() else root.rglob("*")
        for path in candidates:
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix not in allowed_ext:
                continue
            relative_path = path.relative_to(svn_root).as_posix()
            if _is_excluded(relative_path, exclude_patterns):
                continue
            doc = _serialize_document(path, svn_root)
            docs[relative_path] = _merge_document_meta(doc, _get_document_meta(state, relative_path))
            if len(docs) >= 500:
                break
        if len(docs) >= 500:
            break
    return list(docs.values())


@router.get("/documents")
async def list_documents(
    search: str | None = Query(default=None),
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    workspace=Depends(get_agent_for_request),
) -> dict[str, Any]:
    game_service = _game_service_or_404(workspace)
    svn_root = _resolve_svn_root(game_service)
    if svn_root is None:
        return {"items": [], "categories": [], "count": 0}

    items = _collect_documents(workspace, svn_root)
    if category:
        items = [item for item in items if item["category"] == category]
    if status:
        items = [item for item in items if item["status"] == status]
    if search:
        query = search.strip().lower()
        if query:
            items = [
                item for item in items
                if query in item["title"].lower()
                or query in item["author"].lower()
                or query in item["path"].lower()
                or any(query in tag.lower() for tag in item.get("tags", []))
            ]

    items = sorted(items, key=lambda item: (item["updated_at"], item["id"]), reverse=True)
    categories = sorted({item["category"] for item in items})
    return {
        "items": items,
        "categories": categories,
        "count": len(items),
        "scope": "legacy_doc_library",
        "knowledge_sync": {
            "mode": LEGACY_DOC_LIBRARY_SYNC_MODE,
            "affects_release": False,
        },
    }


@router.get("/status")
async def get_doc_library_status(
    rebuild_doc_index: bool = Query(False),
    workspace=Depends(get_agent_for_request),
) -> dict[str, Any]:
    game_service = _game_service_or_404(workspace)
    svn_root = _resolve_svn_root(game_service)
    if svn_root is None:
        return {"configured": False, "documents": {"count": 0, "by_status": {}}}

    items = _collect_documents(workspace, svn_root)
    by_status: dict[str, int] = {}
    for item in items:
        doc_status = str(item.get("status") or "??")
        by_status[doc_status] = by_status.get(doc_status, 0) + 1
    retrieval_status = get_retrieval_status(game_service, rebuild_doc_index=rebuild_doc_index)
    return {
        "configured": True,
        "documents": {
            "count": len(items),
            "by_status": by_status,
            "categories": sorted({item["category"] for item in items}),
        },
        "knowledge_sync": {
            "mode": LEGACY_DOC_LIBRARY_SYNC_MODE,
            "affects_release": False,
        },
        "legacy_retrieval": retrieval_status,
    }


@router.get("/documents/{doc_id:path}")
async def get_document_detail(doc_id: str, workspace=Depends(get_agent_for_request)) -> dict[str, Any]:
    game_service = _game_service_or_404(workspace)
    svn_root = _resolve_svn_root(game_service)
    if svn_root is None:
        raise HTTPException(status_code=412, detail="SVN root not configured")

    path = _resolve_document_path(svn_root, doc_id)
    state = _load_doc_library_state(workspace.workspace_dir)
    document = _merge_document_meta(_serialize_document(path, svn_root), _get_document_meta(state, doc_id))
    content, preview_kind, truncated = _read_document_content(path)
    return {
        "item": document,
        "content": content,
        "preview_kind": preview_kind,
        "truncated": truncated,
        "knowledge_sync": {
            "mode": LEGACY_DOC_LIBRARY_SYNC_MODE,
            "affects_release": False,
        },
    }


@router.patch("/documents/{doc_id:path}")
async def update_document(
    doc_id: str,
    body: dict[str, Any] = Body(default_factory=dict),
    workspace=Depends(get_agent_for_request),
) -> dict[str, Any]:
    game_service = _game_service_or_404(workspace)
    svn_root = _resolve_svn_root(game_service)
    if svn_root is None:
        raise HTTPException(status_code=412, detail="SVN root not configured")

    path = _resolve_document_path(svn_root, doc_id)
    state = _load_doc_library_state(workspace.workspace_dir)
    meta = _get_document_meta(state, doc_id)

    next_status = body.get("status")
    if next_status is not None:
        if next_status not in _VALID_STATUSES:
            raise HTTPException(status_code=400, detail="invalid document status")
        meta["status"] = next_status

    document = _merge_document_meta(_serialize_document(path, svn_root), meta)
    content, preview_kind, truncated = _read_document_content(path)
    kb_entry_id = _sync_document_to_kb(workspace.workspace_dir, document, content, meta)
    if kb_entry_id:
        meta["kb_entry_id"] = kb_entry_id
    meta["updated_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    _save_doc_library_state(workspace.workspace_dir, state)

    return {
        "item": document,
        "content": content,
        "preview_kind": preview_kind,
        "truncated": truncated,
        "kb_entry_id": kb_entry_id,
        "legacy_kb_entry_id": kb_entry_id,
        "knowledge_sync": {
            "mode": LEGACY_DOC_LIBRARY_SYNC_MODE,
            "affects_release": False,
        },
    }
