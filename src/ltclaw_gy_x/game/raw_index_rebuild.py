from __future__ import annotations

import json
from pathlib import Path

from .config import (
    FilterConfig,
    ProjectConfig,
    ProjectMeta,
    ProjectTablesSourceConfig,
    SvnConfig,
    TableConvention,
)
from .source_discovery import discover_table_sources
from .table_indexer import TableIndexer
from .paths import (
    get_project_raw_table_index_path,
    get_project_raw_table_indexes_path,
    get_project_runtime_llm_cache_dir,
)


def _write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + '.tmp')
    temp_path.write_text(content, encoding='utf-8')
    temp_path.replace(path)


def _serialize_table_indexes(tables: list) -> str:
    payload = {
        'version': '1.0',
        'tables': [table.model_dump(mode='json') for table in tables],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _build_rule_only_project_config(project_root: Path, tables_config: ProjectTablesSourceConfig) -> ProjectConfig:
    primary_key = (
        tables_config.primary_key_candidates[0]
        if tables_config.primary_key_candidates
        else 'ID'
    )
    return ProjectConfig(
        project=ProjectMeta(name=project_root.name, engine='rule_only', language='zh'),
        svn=SvnConfig(root=str(project_root), poll_interval_seconds=300, jitter_seconds=30),
        paths=[],
        filters=FilterConfig(include_ext=['.csv'], exclude_glob=list(tables_config.exclude)),
        table_convention=TableConvention(
            header_row=tables_config.header_row,
            primary_key_field=primary_key,
        ),
        doc_templates={},
        models={},
    )


def _error_entry(source_path: str | None, error: str) -> dict:
    payload = {'error': error}
    if source_path:
        payload['source_path'] = source_path.replace('\\', '/')
    return payload


def _is_rule_only_available_csv(item: dict) -> bool:
    return (
        item.get('status') == 'available'
        and item.get('format') == 'csv'
        and item.get('cold_start_supported', True) is True
    )


def _recognized_but_not_supported_entries(discovery: dict) -> list[dict]:
    entries: list[dict] = []
    for item in discovery.get('table_files', []):
        if _is_rule_only_available_csv(item):
            continue
        status = item.get('status')
        fmt = item.get('format')
        source_path = item.get('source_path')
        if status in {'recognized', 'available'} and fmt != 'csv':
            entries.append(
                _error_entry(
                    source_path,
                    item.get('cold_start_reason') or 'rule_only_cold_start_currently_supports_csv',
                )
            )
    return entries


async def rebuild_raw_table_indexes(
    project_root: Path | None,
    tables_config: ProjectTablesSourceConfig | None,
) -> dict:
    result = {
        'success': False,
        'raw_table_index_count': 0,
        'indexed_tables': [],
        'errors': [],
        'next_action': 'run_canonical_rebuild',
    }
    discovery = discover_table_sources(project_root, tables_config)
    if project_root is None or not discovery['project_root']:
        result['errors'] = [_error_entry(None, 'project_root_not_configured')]
        return result
    if not discovery['table_files']:
        result['errors'] = [
            _error_entry(item.get('source_path'), item.get('reason', 'source_discovery_error'))
            for item in discovery['errors']
        ]
        if not result['errors']:
            result['errors'] = [_error_entry(None, 'no_available_table_files')]
        return result

    available_csv_items = [
        item
        for item in discovery['table_files']
        if _is_rule_only_available_csv(item)
    ]
    if not available_csv_items:
        recognized_errors = _recognized_but_not_supported_entries(discovery)
        unsupported_errors = [
            _error_entry(item.get('source_path'), item.get('reason', 'unsupported_table_format'))
            for item in discovery.get('unsupported_files', [])
        ]
        discovery_errors = [
            _error_entry(item.get('source_path'), item.get('reason', 'source_discovery_error'))
            for item in discovery.get('errors', [])
        ]
        errors = [
            _error_entry(None, 'no_csv_table_files_available_for_rule_only_cold_start'),
            *discovery_errors,
            *recognized_errors,
            *unsupported_errors,
        ]
        result.update(
            {
                'success': False,
                'raw_table_index_count': 0,
                'indexed_tables': [],
                'errors': errors,
                'next_action': 'configure_csv_tables_source',
                'discovery_summary': discovery.get('summary', {}),
            }
        )
        return result

    effective_config = tables_config or ProjectTablesSourceConfig()
    project_config = _build_rule_only_project_config(project_root, effective_config)
    indexer = TableIndexer(
        project=project_config,
        model_router=None,
        cache_dir=get_project_runtime_llm_cache_dir(project_root),
    )

    written_tables = []
    indexed_tables = []
    errors = []
    for item in available_csv_items:
        source_path = item['source_path']
        fmt = item['format']
        if fmt != 'csv':
            errors.append(_error_entry(source_path, 'rule_only_raw_index_currently_supports_csv'))
            continue
        source_file = project_root / source_path
        try:
            table_index = await indexer.index_one(source_file, project_root, 0, rule_only=True)
            _write_text_atomic(
                get_project_raw_table_index_path(project_root, table_index.table_name),
                table_index.model_dump_json(indent=2),
            )
            written_tables.append(table_index)
            indexed_tables.append(
                {
                    'table_id': table_index.table_name,
                    'source_path': table_index.source_path,
                    'row_count': table_index.row_count,
                    'field_count': len(table_index.fields),
                    'primary_key': table_index.primary_key,
                }
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(_error_entry(source_path, str(exc)))

    _write_text_atomic(
        get_project_raw_table_indexes_path(project_root),
        _serialize_table_indexes(written_tables),
    )
    result.update(
        {
            'success': len(indexed_tables) > 0,
            'raw_table_index_count': len(indexed_tables),
            'indexed_tables': indexed_tables,
            'errors': errors,
        }
    )
    return result