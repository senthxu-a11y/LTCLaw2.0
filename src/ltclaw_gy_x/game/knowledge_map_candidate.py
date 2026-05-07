from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from .knowledge_rag_context import KnowledgeReleaseContextPathError, _resolve_release_artifact_path
from .knowledge_release_builders import build_minimal_map
from .local_project_paths import normalize_local_project_relative_path
from .knowledge_release_store import get_current_release, load_knowledge_map, load_manifest
from .models import (
    KnowledgeDocRef,
    KnowledgeMap,
    KnowledgeRelationship,
    KnowledgeScriptRef,
    KnowledgeSystem,
    KnowledgeTableRef,
)
from .paths import get_release_dir


MAP_CANDIDATE_RELEASE_INDEXES = ('table_schema', 'doc_knowledge', 'script_evidence')
_GENERIC_SOURCE_DIRS = {'docs', 'doc', 'kb', 'knowledge', 'scripts', 'script', 'tables', 'table'}


def build_map_candidate_from_release(project_root: Path, release_id: str | None = None) -> KnowledgeMap:
    manifest = load_manifest(project_root, release_id) if str(release_id or '').strip() else get_current_release(project_root)
    existing_map = load_knowledge_map(project_root, manifest.release_id)
    release_dir = get_release_dir(project_root, manifest.release_id)

    table_records = _load_release_index_records(release_dir, manifest.indexes.get('table_schema', None))
    doc_records = _load_release_index_records(release_dir, manifest.indexes.get('doc_knowledge', None))
    script_records = _load_release_index_records(release_dir, manifest.indexes.get('script_evidence', None))

    table_hints_by_source = {
        table.source_path: table
        for table in existing_map.tables
        if table.source_path
    }
    doc_hints_by_source = {
        doc.source_path: doc
        for doc in existing_map.docs
        if doc.source_path
    }
    script_hints_by_source = {
        script.source_path: script
        for script in existing_map.scripts
        if script.source_path
    }

    tables = _build_table_refs(table_records, table_hints_by_source)
    table_by_id = {table.table_id: table for table in tables}
    docs = _build_doc_refs(doc_records, doc_hints_by_source, table_by_id)
    scripts = _build_script_refs(script_records, script_hints_by_source, table_by_id)

    relationships = _build_doc_relationships(doc_records, docs, table_by_id)
    relationships.extend(_build_script_relationships(script_records, scripts, table_by_id))

    systems = _build_systems(existing_map, tables, docs, scripts)
    deprecated = _filter_deprecated_refs(existing_map.deprecated, tables, docs, scripts)
    return build_minimal_map(
        manifest.release_id,
        systems=systems,
        tables=tables,
        docs=docs,
        scripts=scripts,
        relationships=relationships,
        deprecated=deprecated,
    )


def _load_release_index_records(release_dir: Path, artifact) -> list[dict[str, Any]]:
    if artifact is None:
        return []
    index_path = _resolve_release_artifact_path(release_dir, artifact.path)
    if not index_path.exists() or not index_path.is_file():
        return []
    payload = index_path.read_text(encoding='utf-8')
    records: list[dict[str, Any]] = []
    for line in payload.splitlines():
        if not line.strip():
            continue
        records.append(json.loads(line))
    return records


def _build_table_refs(
    records: Iterable[dict[str, Any]],
    hints_by_source: dict[str, KnowledgeTableRef],
) -> list[KnowledgeTableRef]:
    refs: list[KnowledgeTableRef] = []
    for record in sorted(records, key=lambda item: (str(item.get('source_path') or ''), str(item.get('table_name') or ''))):
        source_path = _normalize_source_path(record.get('source_path'))
        hint = hints_by_source.get(source_path)
        table_id = str((hint.table_id if hint else None) or record.get('table_name') or Path(source_path).stem).strip()
        refs.append(
            KnowledgeTableRef(
                table_id=table_id,
                title=str((hint.title if hint else None) or record.get('table_name') or table_id),
                source_path=source_path,
                source_hash=_coerce_source_hash(record.get('source_hash'), hint.source_hash if hint else None),
                system_id=(hint.system_id if hint else None) or _derive_table_system_id(record, source_path),
                status='active',
            )
        )
    return refs


def _build_doc_refs(
    records: Iterable[dict[str, Any]],
    hints_by_source: dict[str, KnowledgeDocRef],
    table_by_id: dict[str, KnowledgeTableRef],
) -> list[KnowledgeDocRef]:
    refs: list[KnowledgeDocRef] = []
    used_doc_ids = {hint.doc_id for hint in hints_by_source.values()}
    for record in sorted(records, key=lambda item: (str(item.get('source_path') or ''), str(item.get('title') or ''))):
        source_path = _normalize_source_path(record.get('source_path'))
        hint = hints_by_source.get(source_path)
        fallback_title = str(record.get('title') or Path(source_path).stem or 'Document').strip()
        doc_id = hint.doc_id if hint else _stable_ref_id('doc', source_path, fallback_title, used_doc_ids)
        used_doc_ids.add(doc_id)
        refs.append(
            KnowledgeDocRef(
                doc_id=doc_id,
                title=str((hint.title if hint else None) or fallback_title),
                source_path=source_path,
                source_hash=_coerce_source_hash(record.get('source_hash'), hint.source_hash if hint else None),
                system_id=(hint.system_id if hint else None) or _derive_doc_system_id(record, source_path, table_by_id),
                status='active',
            )
        )
    return refs


def _build_script_refs(
    records: Iterable[dict[str, Any]],
    hints_by_source: dict[str, KnowledgeScriptRef],
    table_by_id: dict[str, KnowledgeTableRef],
) -> list[KnowledgeScriptRef]:
    refs: list[KnowledgeScriptRef] = []
    used_script_ids = {hint.script_id for hint in hints_by_source.values()}
    for record in sorted(records, key=lambda item: str(item.get('source_path') or '')):
        source_path = _normalize_source_path(record.get('source_path'))
        hint = hints_by_source.get(source_path)
        fallback_title = _script_title(record, source_path)
        script_id = hint.script_id if hint else _stable_ref_id('script', source_path, fallback_title, used_script_ids)
        used_script_ids.add(script_id)
        refs.append(
            KnowledgeScriptRef(
                script_id=script_id,
                title=str((hint.title if hint else None) or fallback_title),
                source_path=source_path,
                source_hash=_coerce_source_hash(record.get('source_hash'), hint.source_hash if hint else None),
                system_id=(hint.system_id if hint else None) or _derive_script_system_id(record, source_path, table_by_id),
                status='active',
            )
        )
    return refs


def _build_doc_relationships(
    records: Iterable[dict[str, Any]],
    docs: list[KnowledgeDocRef],
    table_by_id: dict[str, KnowledgeTableRef],
) -> list[KnowledgeRelationship]:
    doc_by_source = {doc.source_path: doc for doc in docs}
    relationships: list[KnowledgeRelationship] = []
    for record in sorted(records, key=lambda item: (str(item.get('source_path') or ''), str(item.get('title') or ''))):
        doc = doc_by_source.get(_normalize_source_path(record.get('source_path')))
        if doc is None:
            continue
        for table_id in sorted({_normalize_table_id(item) for item in record.get('related_tables') or [] if _normalize_table_id(item)}):
            if table_id not in table_by_id:
                continue
            relationships.append(
                KnowledgeRelationship(
                    relationship_id=f'rel:doc:{doc.doc_id}:table:{table_id}:related_table',
                    from_ref=f'doc:{doc.doc_id}',
                    to_ref=f'table:{table_id}',
                    relation_type='related_table',
                    source_hash=doc.source_hash,
                )
            )
    return relationships


def _build_script_relationships(
    records: Iterable[dict[str, Any]],
    scripts: list[KnowledgeScriptRef],
    table_by_id: dict[str, KnowledgeTableRef],
) -> list[KnowledgeRelationship]:
    script_by_source = {script.source_path: script for script in scripts}
    relationships: list[KnowledgeRelationship] = []
    seen_ids: set[str] = set()
    for record in sorted(records, key=lambda item: str(item.get('source_path') or '')):
        script = script_by_source.get(_normalize_source_path(record.get('source_path')))
        if script is None:
            continue
        for reference in _iter_script_references(record):
            table_id = _normalize_table_id(reference.get('target_table'))
            if not table_id or table_id not in table_by_id:
                continue
            relationship_id = f'rel:script:{script.script_id}:table:{table_id}:references_table'
            if relationship_id in seen_ids:
                continue
            seen_ids.add(relationship_id)
            relationships.append(
                KnowledgeRelationship(
                    relationship_id=relationship_id,
                    from_ref=f'script:{script.script_id}',
                    to_ref=f'table:{table_id}',
                    relation_type='references_table',
                    source_hash=script.source_hash,
                )
            )
    return relationships


def _build_systems(
    existing_map: KnowledgeMap,
    tables: list[KnowledgeTableRef],
    docs: list[KnowledgeDocRef],
    scripts: list[KnowledgeScriptRef],
) -> list[KnowledgeSystem]:
    existing_by_id = {system.system_id: system for system in existing_map.systems}
    system_ids = sorted(
        {
            ref.system_id
            for ref in [*tables, *docs, *scripts]
            if ref.system_id
        }
    )
    systems: list[KnowledgeSystem] = []
    for system_id in system_ids:
        hint = existing_by_id.get(system_id)
        systems.append(
            KnowledgeSystem(
                system_id=system_id,
                title=(hint.title if hint else None) or _humanize_identifier(system_id),
                description=hint.description if hint else None,
                status=hint.status if hint else 'active',
                table_ids=sorted(table.table_id for table in tables if table.system_id == system_id),
                doc_ids=sorted(doc.doc_id for doc in docs if doc.system_id == system_id),
                script_ids=sorted(script.script_id for script in scripts if script.system_id == system_id),
            )
        )
    return systems


def _filter_deprecated_refs(
    deprecated_refs: Iterable[str],
    tables: list[KnowledgeTableRef],
    docs: list[KnowledgeDocRef],
    scripts: list[KnowledgeScriptRef],
) -> list[str]:
    valid_refs = {
        *(f'table:{table.table_id}' for table in tables),
        *(f'doc:{doc.doc_id}' for doc in docs),
        *(f'script:{script.script_id}' for script in scripts),
    }
    return sorted({str(ref) for ref in deprecated_refs if str(ref) in valid_refs})


def _derive_table_system_id(record: dict[str, Any], source_path: str) -> str | None:
    return _normalize_identifier(record.get('system')) or _derive_system_from_source_path(source_path)


def _derive_doc_system_id(
    record: dict[str, Any],
    source_path: str,
    table_by_id: dict[str, KnowledgeTableRef],
) -> str | None:
    system_from_tables = _single_system_id(
        table_by_id[table_id].system_id
        for table_id in [_normalize_table_id(item) for item in record.get('related_tables') or []]
        if table_id in table_by_id
    )
    if system_from_tables:
        return system_from_tables
    return _normalize_identifier(record.get('category')) or _derive_system_from_source_path(source_path)


def _derive_script_system_id(
    record: dict[str, Any],
    source_path: str,
    table_by_id: dict[str, KnowledgeTableRef],
) -> str | None:
    namespace = _normalize_identifier(_namespace_head(record.get('namespace')))
    if namespace:
        return namespace
    system_from_tables = _single_system_id(
        table_by_id[table_id].system_id
        for table_id in [_normalize_table_id(reference.get('target_table')) for reference in _iter_script_references(record)]
        if table_id in table_by_id
    )
    if system_from_tables:
        return system_from_tables
    return _derive_system_from_source_path(source_path)


def _iter_script_references(record: dict[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for reference in record.get('references') or []:
        if isinstance(reference, dict):
            refs.append(reference)
    for symbol in record.get('symbols') or []:
        if not isinstance(symbol, dict):
            continue
        for reference in symbol.get('references') or []:
            if isinstance(reference, dict):
                refs.append(reference)
    return refs


def _script_title(record: dict[str, Any], source_path: str) -> str:
    symbols = record.get('symbols') or []
    for symbol in symbols:
        if isinstance(symbol, dict) and str(symbol.get('name') or '').strip():
            return str(symbol['name']).strip()
    return Path(source_path).stem or 'Script'


def _stable_ref_id(prefix: str, source_path: str, title: str, used_ids: set[str]) -> str:
    base = _normalize_identifier(title) or _normalize_identifier(Path(source_path).stem) or prefix
    candidate = base
    if candidate not in used_ids:
        return candidate
    path_candidate = _normalize_identifier(Path(source_path).with_suffix('').as_posix().replace('/', '-')) or f'{prefix}-ref'
    if path_candidate not in used_ids:
        return path_candidate
    suffix = 2
    while f'{path_candidate}-{suffix}' in used_ids:
        suffix += 1
    return f'{path_candidate}-{suffix}'


def _derive_system_from_source_path(source_path: str) -> str | None:
    parts = Path(source_path).parts
    for part in parts:
        candidate = _normalize_identifier(part)
        if candidate and candidate not in _GENERIC_SOURCE_DIRS:
            return candidate
    return None


def _namespace_head(namespace: Any) -> str:
    namespace_text = str(namespace or '').strip()
    if not namespace_text:
        return ''
    return namespace_text.split('.')[0]


def _normalize_source_path(value: Any) -> str:
    return normalize_local_project_relative_path(value)


def _normalize_identifier(value: Any) -> str | None:
    text = re.sub(r'[^a-z0-9]+', '-', str(value or '').strip().lower()).strip('-')
    return text or None


def _normalize_table_id(value: Any) -> str | None:
    text = str(value or '').strip()
    return text or None


def _coerce_source_hash(primary: Any, fallback: str | None = None) -> str:
    value = str(primary or fallback or '').strip()
    if value:
        return value
    return 'sha256:unknown'


def _single_system_id(values: Iterable[str | None]) -> str | None:
    normalized = sorted({value for value in values if value})
    if len(normalized) == 1:
        return normalized[0]
    return None


def _humanize_identifier(identifier: str) -> str:
    parts = [part for part in re.split(r'[-_]+', str(identifier or '').strip()) if part]
    return ' '.join(part.capitalize() for part in parts) or 'System'
