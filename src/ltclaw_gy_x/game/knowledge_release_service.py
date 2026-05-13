from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from ..knowledge_base.kb_store import KnowledgeBaseEntry, get_kb_store
from .code_indexer import CodeIndexStore
from .knowledge_formal_map_store import FormalKnowledgeMapStoreError, load_formal_knowledge_map
from .knowledge_release_builders import (
    build_minimal_map,
    build_minimal_manifest,
    export_candidate_evidence_jsonl,
    export_doc_knowledge_jsonl,
    export_script_evidence_jsonl,
    export_table_schema_jsonl,
    validate_release_id,
)
from .knowledge_release_candidate_store import KnowledgeReleaseCandidateStoreError, list_release_candidates
from .knowledge_release_store import CurrentKnowledgeReleaseNotSetError, create_release, get_current_release_map
from .local_project_paths import normalize_local_project_relative_path
from .models import (
    CodeFileIndex,
    DocIndex,
    KnowledgeDocRef,
    KnowledgeIndexArtifact,
    KnowledgeManifest,
    KnowledgeMap,
    KnowledgeRelationship,
    KnowledgeScriptRef,
    KnowledgeSystem,
    KnowledgeTableRef,
    ReleaseCandidate,
    TableIndex,
)
from .paths import get_code_index_dir, get_table_indexes_path


class KnowledgeReleaseBuildServiceError(RuntimeError):
    pass


class KnowledgeProjectRootNotFoundError(KnowledgeReleaseBuildServiceError):
    pass


class KnowledgeReleasePrerequisiteError(KnowledgeReleaseBuildServiceError):
    pass


@dataclass(frozen=True)
class KnowledgeReleaseBuildResult:
    release_dir: Path
    manifest: KnowledgeManifest
    knowledge_map: KnowledgeMap
    artifacts: dict[str, KnowledgeIndexArtifact]


def build_knowledge_release(
    project_root: Path,
    release_id: str,
    knowledge_map: KnowledgeMap,
    *,
    table_indexes: Iterable[TableIndex] = (),
    doc_indexes: Iterable[DocIndex] = (),
    code_indexes: Iterable[CodeFileIndex] = (),
    knowledge_docs: Iterable[KnowledgeDocRef] = (),
    release_candidates: Iterable[ReleaseCandidate] = (),
    created_by: str | None = None,
    created_at: datetime | None = None,
    release_notes: str = '',
) -> KnowledgeReleaseBuildResult:
    root = Path(project_root).expanduser().resolve(strict=False)
    if not root.exists() or not root.is_dir():
        raise KnowledgeProjectRootNotFoundError(f'Project root not found: {project_root}')

    validated_release_id = validate_release_id(release_id)
    if knowledge_map.release_id != validated_release_id:
        raise ValueError('Release id and knowledge map release id must match')

    table_indexes = list(table_indexes)
    doc_indexes = list(doc_indexes)
    code_indexes = list(code_indexes)
    knowledge_docs = list(knowledge_docs)
    release_candidates = list(release_candidates)

    table_payload, table_artifact = export_table_schema_jsonl(table_indexes)
    doc_payload, doc_artifact = export_doc_knowledge_jsonl(
        doc_indexes=doc_indexes,
        knowledge_docs=knowledge_docs,
    )
    script_payload, script_artifact = export_script_evidence_jsonl(code_indexes)
    candidate_payload, candidate_artifact = export_candidate_evidence_jsonl(release_candidates)

    artifacts = {
        'table_schema': table_artifact,
        'doc_knowledge': doc_artifact,
        'script_evidence': script_artifact,
        'candidate_evidence': candidate_artifact,
    }
    manifest = build_minimal_manifest(
        root,
        validated_release_id,
        knowledge_map,
        source_paths=_collect_source_paths(
            knowledge_map,
            table_indexes=table_indexes,
            doc_indexes=doc_indexes,
            code_indexes=code_indexes,
            knowledge_docs=knowledge_docs,
            release_candidates=release_candidates,
        ),
        created_by=created_by,
        created_at=created_at,
        index_entries=artifacts,
    )
    release_dir = create_release(
        root,
        manifest,
        knowledge_map,
        indexes={
            'table_schema.jsonl': table_payload,
            'doc_knowledge.jsonl': doc_payload,
            'script_evidence.jsonl': script_payload,
            **({'candidate_evidence.jsonl': candidate_payload} if candidate_artifact.count > 0 else {}),
        },
        release_notes=release_notes,
    )
    return KnowledgeReleaseBuildResult(
        release_dir=release_dir,
        manifest=manifest,
        knowledge_map=knowledge_map,
        artifacts=dict(manifest.indexes),
    )


def build_knowledge_release_from_current_indexes(
    project_root: Path,
    workspace_dir: Path,
    release_id: str,
    *,
    candidate_ids: Iterable[str] = (),
    created_by: str | None = None,
    created_at: datetime | None = None,
    release_notes: str = '',
) -> KnowledgeReleaseBuildResult:
    root = Path(project_root).expanduser().resolve(strict=False)
    if not root.exists() or not root.is_dir():
        raise KnowledgeProjectRootNotFoundError(f'Project root not found: {project_root}')

    workspace = Path(workspace_dir).expanduser().resolve(strict=False)
    validated_release_id = validate_release_id(release_id)
    approved_docs = _load_approved_doc_entries(workspace)
    table_index_inventory = _load_current_table_indexes(root)
    code_index_inventory = _load_current_code_indexes(workspace, root)
    current_map = _resolve_effective_map_for_safe_build(
        root,
        validated_release_id,
        table_index_inventory=table_index_inventory,
        code_index_inventory=code_index_inventory,
        approved_docs=approved_docs,
    )
    selected_candidates = _resolve_release_candidates(root, candidate_ids)

    release_time = created_at or datetime.now(timezone.utc)
    table_indexes = _select_current_table_indexes(table_index_inventory, current_map)
    code_indexes = _select_current_code_indexes(code_index_inventory, current_map)
    doc_indexes, knowledge_docs = _build_release_docs(current_map, approved_docs, release_time)

    return build_knowledge_release(
        root,
        validated_release_id,
        current_map,
        table_indexes=table_indexes,
        doc_indexes=doc_indexes,
        code_indexes=code_indexes,
        knowledge_docs=knowledge_docs,
        release_candidates=selected_candidates,
        created_by=created_by,
        created_at=release_time,
        release_notes=release_notes,
    )


def _resolve_effective_map_for_safe_build(
    project_root: Path,
    release_id: str,
    *,
    table_index_inventory: list[TableIndex],
    code_index_inventory: list[CodeFileIndex],
    approved_docs: dict[str, KnowledgeBaseEntry],
) -> KnowledgeMap:
    try:
        formal_map_record = load_formal_knowledge_map(project_root)
    except FormalKnowledgeMapStoreError as exc:
        raise KnowledgeReleasePrerequisiteError(f'Saved formal knowledge map is invalid: {exc}') from exc

    if formal_map_record is not None:
        return formal_map_record.knowledge_map.model_copy(update={'release_id': release_id})

    try:
        current_map = get_current_release_map(project_root)
    except CurrentKnowledgeReleaseNotSetError:
        return _build_bootstrap_map_from_current_indexes(
            project_root,
            release_id,
            table_index_inventory=table_index_inventory,
            code_index_inventory=code_index_inventory,
            approved_docs=approved_docs,
        )
    return current_map.model_copy(update={'release_id': release_id})


def _build_bootstrap_map_from_current_indexes(
    project_root: Path,
    release_id: str,
    *,
    table_index_inventory: list[TableIndex],
    code_index_inventory: list[CodeFileIndex],
    approved_docs: dict[str, KnowledgeBaseEntry],
) -> KnowledgeMap:
    if not table_index_inventory:
        raise KnowledgeReleasePrerequisiteError(
            'Current table indexes are required to build the first knowledge release'
        )

    table_refs = [
        KnowledgeTableRef(
            table_id=table_index.table_name,
            title=table_index.table_name,
            source_path=table_index.source_path,
            source_hash=table_index.source_hash,
            system_id=_normalize_system_id(table_index.system),
            status='active',
        )
        for table_index in sorted(table_index_inventory, key=lambda item: (item.source_path, item.table_name))
    ]
    table_ids = {table_ref.table_id for table_ref in table_refs}

    doc_refs = [
        KnowledgeDocRef(
            doc_id=_stable_doc_id(source_path),
            title=approved_entry.title or Path(source_path).stem,
            source_path=source_path,
            source_hash=_hash_project_source(project_root, source_path),
            system_id=_doc_system_id(approved_entry),
            status='active',
        )
        for source_path, approved_entry in sorted(approved_docs.items())
    ]

    script_refs: list[KnowledgeScriptRef] = []
    relationships: list[KnowledgeRelationship] = []
    seen_relationship_ids: set[str] = set()
    for code_index in sorted(code_index_inventory, key=lambda item: item.source_path):
        script_id = _stable_script_id(code_index.source_path)
        script_refs.append(
            KnowledgeScriptRef(
                script_id=script_id,
                title=Path(code_index.source_path).stem or script_id,
                source_path=code_index.source_path,
                source_hash=code_index.source_hash,
                system_id=_script_system_id(code_index, table_index_inventory),
                status='active',
            )
        )
        for table_id in _referenced_table_ids(code_index, table_ids):
            relationship_id = f'rel:script:{script_id}:table:{table_id}:references_table'
            if relationship_id in seen_relationship_ids:
                continue
            seen_relationship_ids.add(relationship_id)
            relationships.append(
                KnowledgeRelationship(
                    relationship_id=relationship_id,
                    from_ref=f'script:{script_id}',
                    to_ref=f'table:{table_id}',
                    relation_type='references_table',
                    source_hash=code_index.source_hash,
                )
            )

    systems = _build_bootstrap_systems(table_refs, doc_refs, script_refs)
    return build_minimal_map(
        release_id,
        systems=systems,
        tables=table_refs,
        docs=doc_refs,
        scripts=script_refs,
        relationships=relationships,
    )


def _collect_source_paths(
    knowledge_map: KnowledgeMap,
    *,
    table_indexes: Iterable[TableIndex],
    doc_indexes: Iterable[DocIndex],
    code_indexes: Iterable[CodeFileIndex],
    knowledge_docs: Iterable[KnowledgeDocRef],
    release_candidates: Iterable[ReleaseCandidate],
) -> list[str]:
    seen: set[str] = set()
    ordered_paths: list[str] = []

    def add(source_path: str | None) -> None:
        if not source_path:
            return
        if source_path in seen:
            return
        seen.add(source_path)
        ordered_paths.append(source_path)

    for table_index in table_indexes:
        add(table_index.source_path)
    for doc_index in doc_indexes:
        add(doc_index.source_path)
    for code_index in code_indexes:
        add(code_index.source_path)
    for knowledge_doc in knowledge_docs:
        add(knowledge_doc.source_path)
    for release_candidate in release_candidates:
        for source_ref in release_candidate.source_refs:
            add(source_ref)
    for table in knowledge_map.tables:
        add(table.source_path)
    for doc in knowledge_map.docs:
        add(doc.source_path)
    for script in knowledge_map.scripts:
        add(script.source_path)
    return ordered_paths


def _resolve_release_candidates(project_root: Path, candidate_ids: Iterable[str]) -> list[ReleaseCandidate]:
    normalized = [str(candidate_id or '').strip() for candidate_id in candidate_ids if str(candidate_id or '').strip()]
    if not normalized:
        return []

    try:
        available_candidates = {
            candidate.candidate_id: candidate
            for candidate in list_release_candidates(project_root)
        }
    except KnowledgeReleaseCandidateStoreError as exc:
        raise KnowledgeReleasePrerequisiteError(str(exc)) from exc

    selected_candidates: list[ReleaseCandidate] = []
    seen: set[str] = set()
    for candidate_id in normalized:
        if candidate_id in seen:
            continue
        seen.add(candidate_id)

        candidate = available_candidates.get(candidate_id)
        if candidate is None:
            raise KnowledgeReleasePrerequisiteError(f'Release candidate not found: {candidate_id}')
        if candidate.status != 'accepted':
            raise KnowledgeReleasePrerequisiteError(
                f'Release candidate must be accepted: {candidate_id} ({candidate.status})'
            )
        if not candidate.selected:
            raise KnowledgeReleasePrerequisiteError(
                f'Release candidate must be selected for build: {candidate_id}'
            )
        selected_candidates.append(candidate)

    return selected_candidates


def _load_current_table_indexes(project_root: Path) -> list[TableIndex]:
    index_path = get_table_indexes_path(project_root)
    if not index_path.exists():
        return []

    try:
        payload = json.loads(index_path.read_text(encoding='utf-8'))
    except Exception as exc:  # noqa: BLE001
        raise KnowledgeReleasePrerequisiteError('Current table indexes could not be read') from exc

    return [TableIndex.model_validate(item) for item in payload.get('tables', [])]


def _select_current_table_indexes(table_indexes: Iterable[TableIndex], knowledge_map: KnowledgeMap) -> list[TableIndex]:
    table_indexes = list(table_indexes)
    if not table_indexes:
        raise KnowledgeReleasePrerequisiteError('Current table indexes are not available')

    by_source_path = {table.source_path: table for table in table_indexes}
    by_table_name = {table.table_name: table for table in table_indexes}

    selected: list[TableIndex] = []
    missing: list[str] = []
    for table_ref in knowledge_map.tables:
        table_index = by_source_path.get(table_ref.source_path) or by_table_name.get(table_ref.table_id)
        if table_index is None:
            missing.append(table_ref.source_path)
            continue
        selected.append(table_index)

    if missing:
        raise KnowledgeReleasePrerequisiteError(
            'Current table indexes are missing for: ' + ', '.join(sorted(missing))
        )
    return selected


def _load_current_code_indexes(workspace_dir: Path, project_root: Path) -> list[CodeFileIndex]:
    index_dir = get_code_index_dir(workspace_dir, project_root)
    if not index_dir.exists():
        return []

    store = CodeIndexStore(index_dir)
    return list(store.load_all())


def _select_current_code_indexes(code_indexes: Iterable[CodeFileIndex], knowledge_map: KnowledgeMap) -> list[CodeFileIndex]:
    code_indexes = list(code_indexes)
    if not code_indexes and knowledge_map.scripts:
        raise KnowledgeReleasePrerequisiteError('Current code indexes are not available')

    by_source_path = {entry.source_path: entry for entry in code_indexes}
    selected: list[CodeFileIndex] = []
    missing: list[str] = []
    for script_ref in knowledge_map.scripts:
        code_index = by_source_path.get(script_ref.source_path)
        if code_index is None:
            missing.append(script_ref.source_path)
            continue
        selected.append(code_index)

    if missing:
        raise KnowledgeReleasePrerequisiteError(
            'Current code indexes are missing for: ' + ', '.join(sorted(missing))
        )
    return selected


def _normalize_system_id(value: str | None) -> str | None:
    candidate = str(value or '').strip().lower().replace(' ', '_').replace('-', '_')
    return candidate or None


def _doc_system_id(entry: KnowledgeBaseEntry) -> str | None:
    for tag in entry.tags or []:
        candidate = _normalize_system_id(str(tag or ''))
        if candidate:
            return candidate
    return None


def _stable_doc_id(source_path: str) -> str:
    return 'doc-' + hashlib.sha1(source_path.encode('utf-8')).hexdigest()[:12]


def _stable_script_id(source_path: str) -> str:
    return 'script-' + hashlib.sha1(source_path.encode('utf-8')).hexdigest()[:12]


def _hash_project_source(project_root: Path, source_path: str) -> str:
    try:
        normalized = normalize_local_project_relative_path(source_path, error_label='approved doc path')
    except ValueError as exc:
        raise KnowledgeReleasePrerequisiteError(str(exc)) from exc
    absolute_path = project_root / normalized
    if not absolute_path.exists() or not absolute_path.is_file():
        raise KnowledgeReleasePrerequisiteError(f'Approved doc source is missing: {source_path}')
    return 'sha256:' + hashlib.sha256(absolute_path.read_bytes()).hexdigest()


def _script_system_id(code_index: CodeFileIndex, table_indexes: Iterable[TableIndex]) -> str | None:
    table_indexes = list(table_indexes)
    namespace = str(code_index.namespace or '').strip()
    if namespace:
        namespace_head = namespace.split('.', 1)[0]
        candidate = _normalize_system_id(namespace_head)
        if candidate:
            return candidate

    referenced_table_ids = set(_referenced_table_ids(code_index, {table.table_name for table in table_indexes}))
    table_systems = {
        _normalize_system_id(table_index.system)
        for table_index in table_indexes
        if table_index.table_name in referenced_table_ids
    }
    table_systems.discard(None)
    if len(table_systems) == 1:
        return next(iter(table_systems))
    return None


def _referenced_table_ids(code_index: CodeFileIndex, valid_table_ids: set[str]) -> list[str]:
    referenced: set[str] = set()
    for reference in code_index.references:
        table_id = str(reference.target_table or '').strip()
        if table_id and table_id in valid_table_ids:
            referenced.add(table_id)
    for symbol in code_index.symbols:
        for reference in symbol.references:
            table_id = str(reference.target_table or '').strip()
            if table_id and table_id in valid_table_ids:
                referenced.add(table_id)
    return sorted(referenced)


def _build_bootstrap_systems(
    table_refs: Iterable[KnowledgeTableRef],
    doc_refs: Iterable[KnowledgeDocRef],
    script_refs: Iterable[KnowledgeScriptRef],
) -> list[KnowledgeSystem]:
    table_refs = list(table_refs)
    doc_refs = list(doc_refs)
    script_refs = list(script_refs)
    system_ids = sorted(
        {
            system_id
            for system_id in [
                *(table.system_id for table in table_refs),
                *(doc.system_id for doc in doc_refs),
                *(script.system_id for script in script_refs),
            ]
            if system_id
        }
    )
    return [
        KnowledgeSystem(
            system_id=system_id,
            title=system_id.replace('_', ' ').title(),
            table_ids=sorted(table.table_id for table in table_refs if table.system_id == system_id),
            doc_ids=sorted(doc.doc_id for doc in doc_refs if doc.system_id == system_id),
            script_ids=sorted(script.script_id for script in script_refs if script.system_id == system_id),
        )
        for system_id in system_ids
    ]


def _load_approved_doc_entries(workspace_dir: Path) -> dict[str, KnowledgeBaseEntry]:
    approved_docs: dict[str, KnowledgeBaseEntry] = {}
    for entry in get_kb_store(workspace_dir).list_entries():
        if entry.source != 'doc_library':
            continue
        doc_path = str(entry.extra.get('doc_path') or '').strip()
        if not doc_path:
            continue
        approved_docs[doc_path] = entry
    return approved_docs


def _build_release_docs(
    knowledge_map: KnowledgeMap,
    approved_docs: dict[str, KnowledgeBaseEntry],
    indexed_at: datetime,
) -> tuple[list[DocIndex], list[KnowledgeDocRef]]:
    missing: list[str] = []
    doc_indexes: list[DocIndex] = []
    knowledge_docs: list[KnowledgeDocRef] = []
    related_tables = _collect_related_tables_by_doc(knowledge_map)

    for doc_ref in knowledge_map.docs:
        approved_entry = approved_docs.get(doc_ref.source_path)
        if approved_entry is None:
            missing.append(doc_ref.source_path)
            continue
        knowledge_docs.append(doc_ref)
        category = str(approved_entry.extra.get('doc_type') or approved_entry.category or 'doc')
        if category.startswith('doc:'):
            category = category[4:] or 'doc'
        doc_indexes.append(
            DocIndex(
                source_path=doc_ref.source_path,
                source_hash=doc_ref.source_hash,
                svn_revision=0,
                doc_type=category,
                title=approved_entry.title or doc_ref.title,
                summary=approved_entry.summary or doc_ref.title,
                related_tables=related_tables.get(doc_ref.doc_id, []),
                last_indexed_at=indexed_at,
            )
        )

    if missing:
        raise KnowledgeReleasePrerequisiteError(
            'Approved docs are missing for current formal map: ' + ', '.join(sorted(missing))
        )
    return doc_indexes, knowledge_docs


def _collect_related_tables_by_doc(knowledge_map: KnowledgeMap) -> dict[str, list[str]]:
    related: dict[str, set[str]] = {doc.doc_id: set() for doc in knowledge_map.docs}
    for relationship in knowledge_map.relationships:
        from_kind, _, from_id = relationship.from_ref.partition(':')
        to_kind, _, to_id = relationship.to_ref.partition(':')
        if from_kind == 'table' and to_kind == 'doc' and to_id in related:
            related[to_id].add(from_id)
        if from_kind == 'doc' and to_kind == 'table' and from_id in related:
            related[from_id].add(to_id)
    return {doc_id: sorted(table_ids) for doc_id, table_ids in related.items()}
