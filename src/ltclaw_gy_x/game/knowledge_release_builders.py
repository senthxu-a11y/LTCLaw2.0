from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .local_project_paths import normalize_local_project_relative_path
from .models import (
    CodeFileIndex,
    DocIndex,
    KnowledgeDocRef,
    KnowledgeIndexArtifact,
    KnowledgeManifest,
    KnowledgeMap,
    ReleaseBuildMode,
    ReleaseCandidate,
    ReleaseMapSource,
    TableIndex,
)

DEFAULT_RELEASE_INDEXES: dict[str, str] = {
    "table_schema": "indexes/table_schema.jsonl",
    "doc_knowledge": "indexes/doc_knowledge.jsonl",
    "script_evidence": "indexes/script_evidence.jsonl",
    "candidate_evidence": "indexes/candidate_evidence.jsonl",
}

DOC_KNOWLEDGE_RECORD_SCHEMA_VERSION = "doc-knowledge-record.v1"
SCRIPT_EVIDENCE_RECORD_SCHEMA_VERSION = "script-evidence-record.v1"
CANDIDATE_EVIDENCE_RECORD_SCHEMA_VERSION = "candidate-evidence-record.v1"
TABLE_SCHEMA_RECORD_SCHEMA_VERSION = "table-schema-record.v1"


def export_table_schema_jsonl(table_indexes: Iterable[TableIndex]) -> tuple[str, KnowledgeIndexArtifact]:
    records = [_table_index_to_release_record(table_index) for table_index in table_indexes]
    records.sort(key=lambda record: (str(record.get("source_path") or ""), str(record.get("table_name") or "")))
    payload = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records)
    return payload, KnowledgeIndexArtifact(
        path=DEFAULT_RELEASE_INDEXES["table_schema"],
        hash=_hash_text(payload),
        count=len(records),
    )


def export_doc_knowledge_jsonl(
    doc_indexes: Iterable[DocIndex] = (),
    knowledge_docs: Iterable[KnowledgeDocRef] = (),
) -> tuple[str, KnowledgeIndexArtifact]:
    records = [_doc_index_to_release_record(doc_index) for doc_index in doc_indexes]
    seen_doc_sources = {
        str(record.get("source_path") or "").strip()
        for record in records
        if str(record.get("source_path") or "").strip()
    }
    for knowledge_doc in knowledge_docs:
        if knowledge_doc.status == "ignored":
            continue
        normalized_source_path = _normalize_local_project_relative_path(knowledge_doc.source_path)
        if normalized_source_path in seen_doc_sources:
            continue
        records.append(_knowledge_doc_to_release_record(knowledge_doc))
    records.sort(key=lambda record: (str(record.get("source_path") or ""), str(record.get("title") or "")))
    payload = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records)
    return payload, KnowledgeIndexArtifact(
        path=DEFAULT_RELEASE_INDEXES["doc_knowledge"],
        hash=_hash_text(payload),
        count=len(records),
    )


def export_script_evidence_jsonl(code_indexes: Iterable[CodeFileIndex] = ()) -> tuple[str, KnowledgeIndexArtifact]:
    records = [_code_file_index_to_release_record(code_index) for code_index in code_indexes]
    records.sort(key=lambda record: str(record.get("source_path") or ""))
    payload = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records)
    return payload, KnowledgeIndexArtifact(
        path=DEFAULT_RELEASE_INDEXES["script_evidence"],
        hash=_hash_text(payload),
        count=len(records),
    )


def export_candidate_evidence_jsonl(
    release_candidates: Iterable[ReleaseCandidate] = (),
) -> tuple[str, KnowledgeIndexArtifact]:
    records = [_release_candidate_to_evidence_record(candidate) for candidate in release_candidates]
    records.sort(key=lambda record: (str(record.get("candidate_id") or ""), str(record.get("test_plan_id") or "")))
    payload = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records)
    return payload, KnowledgeIndexArtifact(
        path=DEFAULT_RELEASE_INDEXES["candidate_evidence"],
        hash=_hash_text(payload),
        count=len(records),
    )


def build_source_snapshot_entries(project_root: Path, source_paths: Iterable[str]) -> list[dict[str, Any]]:
    root = _canonical_project_root(project_root)
    entries: list[dict[str, Any]] = []
    for source_path in source_paths:
        normalized = _normalize_local_project_relative_path(source_path)
        absolute_path = root / normalized
        stat = absolute_path.stat()
        entries.append(
            {
                "path": normalized,
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "sha256": _hash_bytes(absolute_path.read_bytes()),
            }
        )
    entries.sort(key=lambda entry: entry["path"])
    return entries


def compute_source_snapshot_hash(project_root: Path, source_paths: Iterable[str]) -> str:
    return _hash_json(build_source_snapshot_entries(project_root, source_paths))


def compute_map_hash(knowledge_map: KnowledgeMap) -> str:
    return _hash_json(knowledge_map.model_dump(mode="json"))


def build_minimal_manifest(
    project_root: Path,
    release_id: str,
    knowledge_map: KnowledgeMap,
    *,
    source_paths: Iterable[str],
    created_by: str | None = None,
    created_at: datetime | None = None,
    build_mode: ReleaseBuildMode = "strict",
    map_source: ReleaseMapSource = "provided",
    warnings: Iterable[str] = (),
    index_entries: Mapping[str, KnowledgeIndexArtifact | Mapping[str, Any]] | None = None,
) -> KnowledgeManifest:
    validated_release_id = validate_release_id(release_id)
    if knowledge_map.release_id != validated_release_id:
        raise ValueError("Manifest release id must match knowledge map release id")

    warning_list = [str(warning) for warning in warnings if str(warning).strip()]
    manifest = KnowledgeManifest(
        release_id=validated_release_id,
        created_at=created_at or datetime.now(timezone.utc),
        created_by=created_by,
        build_mode=build_mode,
        status="bootstrap_warning" if build_mode == "bootstrap" else "ready",
        map_source=map_source,
        warnings=warning_list,
        project_root_hash=_hash_text(str(_canonical_project_root(project_root)).replace("\\", "/")),
        source_snapshot=None,
        source_snapshot_hash=compute_source_snapshot_hash(project_root, source_paths),
        map_hash=compute_map_hash(knowledge_map),
        indexes=_build_index_records(index_entries),
        systems=list(knowledge_map.systems),
        tables=list(knowledge_map.tables),
        docs=list(knowledge_map.docs),
        scripts=list(knowledge_map.scripts),
    )
    manifest.source_snapshot = manifest.source_snapshot_hash
    return manifest


def build_minimal_map(
    release_id: str,
    *,
    systems=(),
    tables=(),
    docs=(),
    scripts=(),
    relationships=(),
    deprecated=(),
) -> KnowledgeMap:
    validated_release_id = validate_release_id(release_id)
    knowledge_map = KnowledgeMap(
        release_id=validated_release_id,
        systems=sorted(list(systems), key=lambda item: item.system_id),
        tables=sorted(list(tables), key=lambda item: item.table_id),
        docs=sorted(list(docs), key=lambda item: item.doc_id),
        scripts=sorted(list(scripts), key=lambda item: item.script_id),
        relationships=sorted(list(relationships), key=lambda item: item.relationship_id),
        deprecated=sorted(str(item) for item in deprecated),
    )
    knowledge_map.source_hash = compute_map_hash(knowledge_map)
    return knowledge_map


def validate_release_id(release_id: str) -> str:
    candidate = str(release_id or "").strip()
    if not candidate or candidate in {".", ".."}:
        raise ValueError(f"Invalid release id: {release_id!r}")
    if candidate.startswith("."):
        raise ValueError(f"Invalid release id: {release_id!r}")
    if "/" in candidate or "\\" in candidate:
        raise ValueError(f"Invalid release id: {release_id!r}")
    if Path(candidate).is_absolute() or ".." in Path(candidate).parts:
        raise ValueError(f"Invalid release id: {release_id!r}")
    return candidate


def validate_knowledge_map(knowledge_map: KnowledgeMap) -> None:
    validate_release_id(knowledge_map.release_id)
    for table in knowledge_map.tables:
        _normalize_local_project_relative_path(table.source_path)
    for doc in knowledge_map.docs:
        _normalize_local_project_relative_path(doc.source_path)
    for script in knowledge_map.scripts:
        _normalize_local_project_relative_path(script.source_path)
    refs = _collect_map_refs(knowledge_map)
    for relationship in knowledge_map.relationships:
        if relationship.from_ref not in refs:
            raise ValueError(f"Unknown relationship source: {relationship.from_ref}")
        if relationship.to_ref not in refs:
            raise ValueError(f"Unknown relationship target: {relationship.to_ref}")
        if not str(relationship.source_hash).startswith("sha256:"):
            raise ValueError("Relationship source hash must use sha256 prefix")
    for deprecated_ref in knowledge_map.deprecated:
        if deprecated_ref not in refs:
            raise ValueError(f"Unknown deprecated reference: {deprecated_ref}")


def validate_knowledge_manifest(manifest: KnowledgeManifest) -> None:
    validate_release_id(manifest.release_id)
    for field_name in ("project_root_hash", "source_snapshot_hash", "map_hash"):
        value = getattr(manifest, field_name)
        if not value or not str(value).startswith("sha256:"):
            raise ValueError(f"Manifest field {field_name} must be a sha256 hash")
    if manifest.build_mode == "strict" and manifest.status != "ready":
        raise ValueError("Strict release manifests must use ready status")
    if manifest.build_mode == "bootstrap":
        if manifest.status != "bootstrap_warning":
            raise ValueError("Bootstrap release manifests must use bootstrap_warning status")
        if not manifest.warnings:
            raise ValueError("Bootstrap release manifests must include warnings")
    if set(manifest.indexes.keys()) != set(DEFAULT_RELEASE_INDEXES.keys()):
        raise ValueError("Manifest indexes must represent all optional release indexes explicitly")
    for index_name, default_path in DEFAULT_RELEASE_INDEXES.items():
        artifact = manifest.indexes[index_name]
        normalized_path = _normalize_relative_release_path(artifact.path)
        if normalized_path != default_path:
            raise ValueError(f"Manifest index path mismatch for {index_name}: {artifact.path}")
        if artifact.count < 0:
            raise ValueError(f"Manifest index count must be non-negative: {index_name}")
        if artifact.hash is not None and not str(artifact.hash).startswith("sha256:"):
            raise ValueError(f"Manifest index hash must use sha256 prefix: {index_name}")


def _table_index_to_release_record(table_index: TableIndex) -> dict[str, Any]:
    source_path = _normalize_local_project_relative_path(table_index.source_path)
    record = {
        "schema_version": TABLE_SCHEMA_RECORD_SCHEMA_VERSION,
        "table_name": table_index.table_name,
        "system": table_index.system,
        "summary": table_index.ai_summary,
        "summary_confidence": table_index.ai_summary_confidence,
        "source_path": source_path,
        "source_hash": table_index.source_hash,
        "primary_key": table_index.primary_key,
        "row_count": table_index.row_count,
        "fields": [
            {
                "name": field.name,
                "type": field.type,
                "description": field.description,
                "confidence": field.confidence.value,
            }
            for field in table_index.fields
        ],
    }
    if table_index.svn_revision > 0:
        record["source_revision"] = table_index.svn_revision
    return record


def _doc_index_to_release_record(doc_index: DocIndex) -> dict[str, Any]:
    record = {
        "schema_version": DOC_KNOWLEDGE_RECORD_SCHEMA_VERSION,
        "title": doc_index.title,
        "summary": doc_index.summary,
        "category": doc_index.doc_type,
        "tags": sorted(doc_index.tags),
        "chunks": list(doc_index.chunks),
        "source_path": _normalize_local_project_relative_path(doc_index.source_path),
        "related_tables": sorted(doc_index.related_tables),
        "source_hash": doc_index.source_hash,
    }
    if doc_index.svn_revision > 0:
        record["source_revision"] = doc_index.svn_revision
    return record


def _knowledge_doc_to_release_record(knowledge_doc: KnowledgeDocRef) -> dict[str, Any]:
    record = {
        "schema_version": DOC_KNOWLEDGE_RECORD_SCHEMA_VERSION,
        "title": knowledge_doc.title,
        "summary": None,
        "category": "approved_doc",
        "tags": [],
        "source_path": _normalize_local_project_relative_path(knowledge_doc.source_path),
        "related_tables": [],
        "source_hash": knowledge_doc.source_hash,
    }
    if knowledge_doc.system_id:
        record["tags"] = [knowledge_doc.system_id]
    return record


def _code_file_index_to_release_record(code_index: CodeFileIndex) -> dict[str, Any]:
    summary = next((symbol.summary for symbol in code_index.symbols if symbol.summary), None)
    suffix = Path(str(code_index.source_path or '')).suffix.lower()
    language = {
        '.cs': 'csharp',
        '.lua': 'lua',
        '.py': 'python',
    }.get(suffix, 'script')
    record = {
        "schema_version": SCRIPT_EVIDENCE_RECORD_SCHEMA_VERSION,
        "source_path": _normalize_local_project_relative_path(code_index.source_path),
        "source_hash": code_index.source_hash,
        "language": language,
        "kind": "code_index",
        "symbols": [symbol.model_dump(mode="json") for symbol in code_index.symbols],
        "references": [reference.model_dump(mode="json") for reference in code_index.references],
        "summary": summary,
    }
    if code_index.svn_revision > 0:
        record["source_revision"] = code_index.svn_revision
    return record


def _release_candidate_to_evidence_record(candidate: ReleaseCandidate) -> dict[str, Any]:
    record = {
        "schema_version": CANDIDATE_EVIDENCE_RECORD_SCHEMA_VERSION,
        "candidate_id": candidate.candidate_id,
        "test_plan_id": candidate.test_plan_id,
        "title": candidate.title,
        "source_refs": sorted(
            {
                _normalize_local_project_relative_path(source_ref)
                for source_ref in candidate.source_refs
            }
        ),
        "source_hash": candidate.source_hash,
        "created_at": candidate.created_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": candidate.status,
        "selected": candidate.selected,
    }
    if candidate.project_key:
        record["project_key"] = candidate.project_key
    return record


def _build_index_records(
    index_entries: Mapping[str, KnowledgeIndexArtifact | Mapping[str, Any]] | None,
) -> dict[str, KnowledgeIndexArtifact]:
    index_entries = index_entries or {}
    records: dict[str, KnowledgeIndexArtifact] = {}
    for index_name, default_path in DEFAULT_RELEASE_INDEXES.items():
        raw = index_entries.get(index_name)
        if raw is None:
            records[index_name] = KnowledgeIndexArtifact(path=default_path, hash=None, count=0)
            continue
        if isinstance(raw, KnowledgeIndexArtifact):
            data = raw.model_dump(mode="python")
        else:
            data = dict(raw)
        data.setdefault("path", default_path)
        data.setdefault("hash", None)
        data.setdefault("count", 0)
        data["path"] = _normalize_relative_release_path(str(data["path"]))
        records[index_name] = KnowledgeIndexArtifact.model_validate(data)
    return records


def _collect_map_refs(knowledge_map: KnowledgeMap) -> set[str]:
    refs: set[str] = set()
    refs.update(f"system:{system.system_id}" for system in knowledge_map.systems)
    refs.update(f"table:{table.table_id}" for table in knowledge_map.tables)
    refs.update(f"doc:{doc.doc_id}" for doc in knowledge_map.docs)
    refs.update(f"script:{script.script_id}" for script in knowledge_map.scripts)
    return refs


def _normalize_local_project_relative_path(source_path: str) -> str:
    return normalize_local_project_relative_path(source_path)


def _normalize_relative_release_path(path: str) -> str:
    return _normalize_local_project_relative_path(path)


def _canonical_project_root(project_root: Path) -> Path:
    return Path(project_root).expanduser().resolve(strict=False)


def _hash_json(payload: Any) -> str:
    return _hash_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def _hash_text(payload: str) -> str:
    return _hash_bytes(payload.encode("utf-8"))


def _hash_bytes(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"
