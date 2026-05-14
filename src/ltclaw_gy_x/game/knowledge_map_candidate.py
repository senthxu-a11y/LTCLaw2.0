from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from .canonical_facts import normalize_canonical_header
from .knowledge_formal_map_store import load_formal_knowledge_map
from .knowledge_rag_context import KnowledgeReleaseContextPathError, _resolve_release_artifact_path
from .knowledge_release_builders import build_minimal_map
from .local_project_paths import normalize_local_project_relative_path
from .knowledge_release_store import (
    CurrentKnowledgeReleaseNotSetError,
    get_current_release,
    get_current_release_map,
    load_knowledge_map,
    load_manifest,
)
from .models import (
    CanonicalDocFacts,
    CanonicalScriptFacts,
    CanonicalTableSchema,
    KnowledgeDocRef,
    KnowledgeMapCandidateResult,
    KnowledgeMap,
    KnowledgeRelationship,
    KnowledgeScriptRef,
    KnowledgeSystem,
    KnowledgeTableRef,
    MapDiffReview,
)
from .paths import (
    get_project_canonical_docs_dir,
    get_project_canonical_scripts_dir,
    get_project_canonical_tables_dir,
    get_release_dir,
)


MAP_CANDIDATE_RELEASE_INDEXES = ('table_schema', 'doc_knowledge', 'script_evidence')
_GENERIC_SOURCE_DIRS = {'docs', 'doc', 'kb', 'knowledge', 'scripts', 'script', 'tables', 'table'}
_SOURCE_CANDIDATE_RELEASE_ID = 'candidate-source-canonical'
_RELEASE_SNAPSHOT_WARNING = (
    'This candidate is reconstructed from the current release snapshot for review compatibility; '
    'it is not the primary path for rebuilding the project knowledge map.'
)
_NO_CANONICAL_FACTS_WARNING = (
    'No canonical facts were available; source/canonical candidate review could not build a candidate map.'
)


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


def build_map_candidate_result_from_release(
    project_root: Path,
    release_id: str | None = None,
) -> KnowledgeMapCandidateResult:
    candidate_map = build_map_candidate_from_release(project_root, release_id=release_id)
    return KnowledgeMapCandidateResult(
        mode='candidate_map',
        map=candidate_map,
        release_id=candidate_map.release_id,
        candidate_source='release_snapshot',
        is_formal_map=False,
        source_release_id=candidate_map.release_id,
        uses_existing_formal_map_as_hint=False,
        warnings=[_RELEASE_SNAPSHOT_WARNING],
    )


def build_map_candidate_from_canonical_facts(
    project_root: Path,
    existing_formal_map: KnowledgeMap | None = None,
) -> KnowledgeMapCandidateResult:
    canonical_tables = _load_canonical_models(get_project_canonical_tables_dir(project_root), CanonicalTableSchema)
    canonical_docs = _load_canonical_models(get_project_canonical_docs_dir(project_root), CanonicalDocFacts)
    canonical_scripts = _load_canonical_models(get_project_canonical_scripts_dir(project_root), CanonicalScriptFacts)

    uses_existing_formal_map_as_hint = existing_formal_map is not None
    if not canonical_tables and not canonical_docs and not canonical_scripts:
        return KnowledgeMapCandidateResult(
            mode='no_canonical_facts',
            map=None,
            release_id=None,
            candidate_source='source_canonical',
            is_formal_map=False,
            source_release_id=None,
            uses_existing_formal_map_as_hint=uses_existing_formal_map_as_hint,
            warnings=[_NO_CANONICAL_FACTS_WARNING],
        )

    hint_tables_by_source, hint_tables_by_id = _table_hint_indexes(existing_formal_map)
    hint_docs_by_source, hint_docs_by_id = _doc_hint_indexes(existing_formal_map)
    hint_scripts_by_source, hint_scripts_by_id = _script_hint_indexes(existing_formal_map)

    tables = _build_table_refs_from_canonical(canonical_tables, hint_tables_by_source, hint_tables_by_id)
    table_by_id = {table.table_id: table for table in tables}
    docs = _build_doc_refs_from_canonical(canonical_docs, table_by_id, hint_docs_by_source, hint_docs_by_id)
    scripts = _build_script_refs_from_canonical(canonical_scripts, table_by_id, hint_scripts_by_source, hint_scripts_by_id)
    doc_by_id = {doc.doc_id: doc for doc in docs}
    script_by_id = {script.script_id: script for script in scripts}

    warnings: list[str] = []
    relationships = _build_relationships_from_canonical(canonical_docs, canonical_scripts, doc_by_id, script_by_id, table_by_id)
    if existing_formal_map is not None:
        carryover_relationships, carryover_warnings = _carryover_formal_relationship_hints(
            existing_formal_map,
            tables=tables,
            docs=docs,
            scripts=scripts,
            relationships=relationships,
        )
        relationships.extend(carryover_relationships)
        warnings.extend(carryover_warnings)

    systems = _build_systems_from_candidate_hint(existing_formal_map, tables, docs, scripts)
    candidate_map = build_minimal_map(
        _SOURCE_CANDIDATE_RELEASE_ID,
        systems=systems,
        tables=tables,
        docs=docs,
        scripts=scripts,
        relationships=relationships,
        deprecated=[],
    )

    return KnowledgeMapCandidateResult(
        mode='candidate_map',
        map=candidate_map,
        release_id=None,
        candidate_source='source_canonical',
        is_formal_map=False,
        source_release_id=None,
        uses_existing_formal_map_as_hint=uses_existing_formal_map_as_hint,
        warnings=warnings,
    )


def build_map_diff_review(
    base_map: KnowledgeMap | None,
    candidate_map: KnowledgeMap,
    *,
    candidate_source: str,
    base_map_source: str,
    warnings: Iterable[str] = (),
) -> MapDiffReview:
    base_refs = _collect_map_ref_metadata(base_map)
    candidate_refs = _collect_map_ref_metadata(candidate_map)

    base_keys = set(base_refs)
    candidate_keys = set(candidate_refs)
    shared_keys = base_keys & candidate_keys

    changed_refs = sorted(ref for ref in shared_keys if base_refs[ref] != candidate_refs[ref])
    unchanged_refs = sorted(ref for ref in shared_keys if base_refs[ref] == candidate_refs[ref])

    return MapDiffReview(
        base_map_source=base_map_source,
        candidate_source=candidate_source,
        added_refs=sorted(candidate_keys - base_keys),
        removed_refs=sorted(base_keys - candidate_keys),
        changed_refs=changed_refs,
        unchanged_refs=unchanged_refs,
        warnings=[str(warning) for warning in warnings if str(warning).strip()],
    )


def resolve_map_diff_base(project_root: Path, existing_formal_map: KnowledgeMap | None = None) -> tuple[KnowledgeMap | None, str]:
    if existing_formal_map is not None:
        return existing_formal_map, 'formal_map'
    try:
        return get_current_release_map(project_root), 'current_release'
    except CurrentKnowledgeReleaseNotSetError:
        return None, 'none'


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


def _load_canonical_models(directory: Path, model_type: type[CanonicalTableSchema] | type[CanonicalDocFacts] | type[CanonicalScriptFacts]):
    if not directory.exists() or not directory.is_dir():
        return []
    loaded = []
    for candidate in sorted(directory.glob('*.json')):
        loaded.append(model_type.model_validate(json.loads(candidate.read_text(encoding='utf-8'))))
    return loaded


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


def _build_systems_from_candidate_hint(
    existing_formal_map: KnowledgeMap | None,
    tables: list[KnowledgeTableRef],
    docs: list[KnowledgeDocRef],
    scripts: list[KnowledgeScriptRef],
) -> list[KnowledgeSystem]:
    hint_map = existing_formal_map or KnowledgeMap(release_id='candidate-hint')
    return _build_systems(hint_map, tables, docs, scripts)


def _table_hint_indexes(existing_formal_map: KnowledgeMap | None) -> tuple[dict[str, KnowledgeTableRef], dict[str, KnowledgeTableRef]]:
    if existing_formal_map is None:
        return {}, {}
    return (
        {table.source_path: table for table in existing_formal_map.tables if table.source_path},
        {table.table_id: table for table in existing_formal_map.tables},
    )


def _doc_hint_indexes(existing_formal_map: KnowledgeMap | None) -> tuple[dict[str, KnowledgeDocRef], dict[str, KnowledgeDocRef]]:
    if existing_formal_map is None:
        return {}, {}
    return (
        {doc.source_path: doc for doc in existing_formal_map.docs if doc.source_path},
        {doc.doc_id: doc for doc in existing_formal_map.docs},
    )


def _script_hint_indexes(existing_formal_map: KnowledgeMap | None) -> tuple[dict[str, KnowledgeScriptRef], dict[str, KnowledgeScriptRef]]:
    if existing_formal_map is None:
        return {}, {}
    return (
        {script.source_path: script for script in existing_formal_map.scripts if script.source_path},
        {script.script_id: script for script in existing_formal_map.scripts},
    )


def _build_table_refs_from_canonical(
    canonical_tables: Iterable[CanonicalTableSchema],
    hints_by_source: dict[str, KnowledgeTableRef],
    hints_by_id: dict[str, KnowledgeTableRef],
) -> list[KnowledgeTableRef]:
    refs: list[KnowledgeTableRef] = []
    for table_schema in sorted(canonical_tables, key=lambda item: (item.source_path, item.table_id)):
        hint = hints_by_id.get(table_schema.table_id) or hints_by_source.get(table_schema.source_path)
        refs.append(
            KnowledgeTableRef(
                table_id=table_schema.table_id,
                title=(hint.title if hint else None) or table_schema.table_id,
                source_path=table_schema.source_path,
                source_hash=table_schema.source_hash,
                system_id=(hint.system_id if hint else None) or _derive_system_from_source_path(table_schema.source_path),
                status=(hint.status if hint else 'active'),
            )
        )
    return refs


def _build_doc_refs_from_canonical(
    canonical_docs: Iterable[CanonicalDocFacts],
    table_by_id: dict[str, KnowledgeTableRef],
    hints_by_source: dict[str, KnowledgeDocRef],
    hints_by_id: dict[str, KnowledgeDocRef],
) -> list[KnowledgeDocRef]:
    refs: list[KnowledgeDocRef] = []
    for doc_facts in sorted(canonical_docs, key=lambda item: (item.source_path, item.doc_id)):
        hint = hints_by_id.get(doc_facts.doc_id) or hints_by_source.get(doc_facts.source_path)
        refs.append(
            KnowledgeDocRef(
                doc_id=doc_facts.doc_id,
                title=(hint.title if hint else None) or doc_facts.title,
                source_path=doc_facts.source_path,
                source_hash=doc_facts.source_hash,
                system_id=(hint.system_id if hint else None) or _system_id_from_related_refs(doc_facts.related_refs, table_by_id),
                status=(hint.status if hint else 'active'),
            )
        )
    return refs


def _build_script_refs_from_canonical(
    canonical_scripts: Iterable[CanonicalScriptFacts],
    table_by_id: dict[str, KnowledgeTableRef],
    hints_by_source: dict[str, KnowledgeScriptRef],
    hints_by_id: dict[str, KnowledgeScriptRef],
) -> list[KnowledgeScriptRef]:
    refs: list[KnowledgeScriptRef] = []
    for script_facts in sorted(canonical_scripts, key=lambda item: (item.source_path, item.script_id)):
        hint = hints_by_id.get(script_facts.script_id) or hints_by_source.get(script_facts.source_path)
        fallback_title = script_facts.symbols[0] if script_facts.symbols else Path(script_facts.source_path).stem or script_facts.script_id
        refs.append(
            KnowledgeScriptRef(
                script_id=script_facts.script_id,
                title=(hint.title if hint else None) or fallback_title,
                source_path=script_facts.source_path,
                source_hash=script_facts.source_hash,
                system_id=(hint.system_id if hint else None) or _system_id_from_related_refs(script_facts.related_refs, table_by_id),
                status=(hint.status if hint else 'active'),
            )
        )
    return refs


def _build_relationships_from_canonical(
    canonical_docs: Iterable[CanonicalDocFacts],
    canonical_scripts: Iterable[CanonicalScriptFacts],
    doc_by_id: dict[str, KnowledgeDocRef],
    script_by_id: dict[str, KnowledgeScriptRef],
    table_by_id: dict[str, KnowledgeTableRef],
) -> list[KnowledgeRelationship]:
    relationships: list[KnowledgeRelationship] = []
    seen: set[str] = set()

    for doc_facts in canonical_docs:
        doc = doc_by_id.get(doc_facts.doc_id)
        if doc is None:
            continue
        for related_ref in sorted(set(doc_facts.related_refs)):
            relationship = _canonical_related_ref_to_relationship('doc', doc.doc_id, doc.source_hash, related_ref, table_by_id)
            if relationship is None or relationship.relationship_id in seen:
                continue
            seen.add(relationship.relationship_id)
            relationships.append(relationship)

    for script_facts in canonical_scripts:
        script = script_by_id.get(script_facts.script_id)
        if script is None:
            continue
        for related_ref in sorted(set(script_facts.related_refs)):
            relationship = _canonical_related_ref_to_relationship('script', script.script_id, script.source_hash, related_ref, table_by_id)
            if relationship is None or relationship.relationship_id in seen:
                continue
            seen.add(relationship.relationship_id)
            relationships.append(relationship)

    return relationships


def _carryover_formal_relationship_hints(
    existing_formal_map: KnowledgeMap,
    *,
    tables: list[KnowledgeTableRef],
    docs: list[KnowledgeDocRef],
    scripts: list[KnowledgeScriptRef],
    relationships: list[KnowledgeRelationship],
) -> tuple[list[KnowledgeRelationship], list[str]]:
    valid_refs = {
        *(f'system:{system.system_id}' for system in existing_formal_map.systems),
        *(f'table:{table.table_id}' for table in tables),
        *(f'doc:{doc.doc_id}' for doc in docs),
        *(f'script:{script.script_id}' for script in scripts),
    }
    existing_ids = {relationship.relationship_id for relationship in relationships}
    carried: list[KnowledgeRelationship] = []
    skipped = 0
    for relationship in existing_formal_map.relationships:
        if relationship.relationship_id in existing_ids:
            continue
        if relationship.from_ref not in valid_refs or relationship.to_ref not in valid_refs:
            skipped += 1
            continue
        carried.append(relationship)
    warnings: list[str] = []
    if carried:
        warnings.append('Carried over matching relationships from the existing formal map as hints only.')
    if skipped:
        warnings.append('Skipped one or more existing formal-map relationships because their refs were absent from canonical facts.')
    return carried, warnings


def _system_id_from_related_refs(related_refs: Iterable[str], table_by_id: dict[str, KnowledgeTableRef]) -> str | None:
    system_ids = []
    for related_ref in related_refs:
        if not str(related_ref).startswith('table:'):
            continue
        table_id = str(related_ref).split(':', 1)[1]
        table = table_by_id.get(table_id)
        if table and table.system_id:
            system_ids.append(table.system_id)
    return _single_system_id(system_ids)


def _canonical_related_ref_to_relationship(
    source_kind: str,
    source_id: str,
    source_hash: str,
    related_ref: str,
    table_by_id: dict[str, KnowledgeTableRef],
) -> KnowledgeRelationship | None:
    ref_text = str(related_ref or '').strip()
    if not ref_text or ':' not in ref_text:
        return None
    ref_kind, ref_id = ref_text.split(':', 1)
    if ref_kind == 'table':
        if ref_id not in table_by_id:
            return None
        relation_type = 'related_table' if source_kind == 'doc' else 'references_table'
    elif ref_kind in {'system', 'doc', 'script'}:
        relation_type = 'related_ref'
    else:
        return None
    relationship_id = f'rel:{source_kind}:{source_id}:{ref_kind}:{ref_id}:{relation_type}'
    return KnowledgeRelationship(
        relationship_id=relationship_id,
        from_ref=f'{source_kind}:{source_id}',
        to_ref=f'{ref_kind}:{ref_id}',
        relation_type=relation_type,
        source_hash=source_hash,
    )


def _collect_map_ref_metadata(knowledge_map: KnowledgeMap | None) -> dict[str, dict[str, Any]]:
    if knowledge_map is None:
        return {}
    refs: dict[str, dict[str, Any]] = {}
    for system in knowledge_map.systems:
        refs[f'system:{system.system_id}'] = {
            'title': system.title,
            'description': system.description,
            'status': system.status,
        }
    for table in knowledge_map.tables:
        refs[f'table:{table.table_id}'] = {
            'source_path': table.source_path,
            'source_hash': table.source_hash,
            'system_id': table.system_id,
            'status': table.status,
            'title': table.title,
        }
    for doc in knowledge_map.docs:
        refs[f'doc:{doc.doc_id}'] = {
            'source_path': doc.source_path,
            'source_hash': doc.source_hash,
            'system_id': doc.system_id,
            'status': doc.status,
            'title': doc.title,
        }
    for script in knowledge_map.scripts:
        refs[f'script:{script.script_id}'] = {
            'source_path': script.source_path,
            'source_hash': script.source_hash,
            'system_id': script.system_id,
            'status': script.status,
            'title': script.title,
        }
    for relationship in knowledge_map.relationships:
        refs[f'relationship:{relationship.relationship_id}'] = {
            'from_ref': relationship.from_ref,
            'to_ref': relationship.to_ref,
            'relation_type': relationship.relation_type,
            'source_hash': relationship.source_hash,
        }
    return refs


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
