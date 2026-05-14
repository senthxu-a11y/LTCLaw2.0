from __future__ import annotations

import json
from datetime import datetime

from ltclaw_gy_x.game.canonical_facts_committer import CanonicalFactsCommitter
from ltclaw_gy_x.game.models import CanonicalTableSchema, FieldConfidence, FieldInfo, TableIndex
from ltclaw_gy_x.game.paths import (
    get_project_canonical_table_schema_path,
    get_project_raw_table_indexes_path,
)


def _now():
    return datetime(2026, 1, 1, 12, 0, 0)


def _table_index(table_name: str = 'HeroTable') -> TableIndex:
    return TableIndex(
        table_name=table_name,
        source_path=f'Tables/{table_name}.csv',
        source_hash=f'sha256:{table_name}',
        svn_revision=7,
        system='combat',
        row_count=3,
        primary_key='ID',
        ai_summary='hero schema',
        ai_summary_confidence=0.9,
        fields=[
            FieldInfo(name='ID', type='int', description='identifier', confidence=FieldConfidence.CONFIRMED),
            FieldInfo(name='Hero Name', type='str', description='display name', confidence=FieldConfidence.HIGH_AI),
        ],
        last_indexed_at=_now(),
        indexer_model='test-model',
    )


def _write_raw_indexes_payload(project_root, tables) -> None:
    raw_indexes_path = get_project_raw_table_indexes_path(project_root)
    raw_indexes_path.parent.mkdir(parents=True, exist_ok=True)
    raw_indexes_path.write_text(
        json.dumps({'version': '1.0', 'tables': tables}, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )


def test_rebuild_tables_writes_canonical_schema_from_raw_indexes(tmp_path):
    project_root = tmp_path / 'project-root'
    table_index = _table_index()
    _write_raw_indexes_payload(project_root, [table_index.model_dump(mode='json')])

    result = CanonicalFactsCommitter(project_root).rebuild_tables(force=False)

    assert result.raw_table_index_count == 1
    assert result.canonical_table_count == 1
    assert result.written == ['HeroTable.json']
    assert result.errors == []

    canonical_path = get_project_canonical_table_schema_path(project_root, 'HeroTable')
    canonical_schema = CanonicalTableSchema.model_validate_json(canonical_path.read_text(encoding='utf-8'))
    assert canonical_schema.table_id == 'HeroTable'
    assert canonical_schema.fields[0].canonical_header == 'id'
    assert canonical_schema.fields[0].semantic_type == 'id'
    assert canonical_schema.fields[0].source == 'raw_index_rule'
    assert canonical_schema.fields[1].canonical_header == 'hero_name'


def test_rebuild_tables_keeps_processing_when_one_raw_index_fails(tmp_path):
    project_root = tmp_path / 'project-root'
    _write_raw_indexes_payload(
        project_root,
        [
            _table_index('HeroTable').model_dump(mode='json'),
            {'table_name': 'BrokenTable'},
        ],
    )

    result = CanonicalFactsCommitter(project_root).rebuild_tables(force=False)

    assert result.raw_table_index_count == 2
    assert result.canonical_table_count == 1
    assert result.written == ['HeroTable.json']
    assert len(result.errors) == 1
    assert result.errors[0].raw_index_file == 'BrokenTable.json'


def test_rebuild_tables_returns_explicit_error_when_raw_indexes_are_missing(tmp_path):
    project_root = tmp_path / 'project-root'

    result = CanonicalFactsCommitter(project_root).rebuild_tables(force=False)

    assert result.raw_table_index_count == 0
    assert result.canonical_table_count == 0
    assert result.written == []
    assert result.warnings == []
    assert len(result.errors) == 1
    assert result.errors[0].raw_index_file == 'table_indexes.json'
    assert result.errors[0].error == f'Raw table indexes file does not exist: {get_project_raw_table_indexes_path(project_root)}'
    assert result.errors[0].table_id is None