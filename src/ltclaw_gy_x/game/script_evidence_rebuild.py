from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .canonical_facts import build_canonical_script_facts
from .code_indexer import CodeIndexer
from .config import ProjectScriptsSourceConfig
from .models import CodeFileIndex, CodeSymbol, CodeSymbolReference
from .paths import get_project_canonical_script_facts_path, get_project_raw_scripts_dir, get_project_raw_table_indexes_path
from .script_source_discovery import discover_script_sources


_PY_DEF_PATTERN = re.compile(r'^\s*def\s+(\w+)\s*\(([^)]*)\)\s*:', re.MULTILINE)
_PY_CLASS_PATTERN = re.compile(r'^\s*class\s+(\w+)\b', re.MULTILINE)
_LUA_FUNCTION_PATTERN = re.compile(r'^\s*function\s+([A-Za-z0-9_.:]+)\s*\(([^)]*)\)', re.MULTILINE)
_LUA_LOCAL_MODULE_PATTERN = re.compile(r'^\s*local\s+(\w+)\s*=\s*\{\s*\}\s*$', re.MULTILINE)


def _write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + '.tmp')
    temp_path.write_text(content, encoding='utf-8')
    temp_path.replace(path)


def _load_known_tables(project_root: Path) -> tuple[set[str], dict[str, set[str]]]:
    raw_indexes_path = get_project_raw_table_indexes_path(project_root)
    if not raw_indexes_path.exists():
        return set(), {}
    try:
        payload = json.loads(raw_indexes_path.read_text(encoding='utf-8'))
    except Exception:
        return set(), {}
    tables = payload.get('tables') if isinstance(payload, dict) else None
    if not isinstance(tables, list):
        return set(), {}
    table_names: set[str] = set()
    table_fields: dict[str, set[str]] = {}
    for item in tables:
        if not isinstance(item, dict):
            continue
        table_name = str(item.get('table_name') or item.get('table_id') or '').strip()
        if not table_name:
            continue
        table_names.add(table_name)
        fields = item.get('fields')
        if isinstance(fields, list):
            table_fields[table_name] = {
                str(field.get('name') or '').strip()
                for field in fields
                if isinstance(field, dict) and str(field.get('name') or '').strip()
            }
    return table_names, table_fields


def _collect_references(text: str, known_tables: Iterable[str], known_fields: dict[str, set[str]]) -> list[CodeSymbolReference]:
    references: list[CodeSymbolReference] = []
    seen: set[tuple[str | None, str | None, int]] = set()
    lines = text.splitlines()
    for line_idx, line in enumerate(lines):
        snippet = line.strip()[:120]
        if not snippet:
            continue
        for table_name in known_tables:
            if f'{table_name}.' in line:
                suffix = line.split(f'{table_name}.', 1)[1]
                field_match = re.match(r'(\w+)', suffix)
                field_name = field_match.group(1) if field_match else None
                if field_name and field_name in known_fields.get(table_name, set()):
                    key = (table_name, field_name, line_idx)
                    if key not in seen:
                        seen.add(key)
                        references.append(CodeSymbolReference(target_kind='field', target_table=table_name, target_field=field_name, line=line_idx, snippet=snippet, confidence='confirmed'))
                    continue
            if table_name in line:
                key = (table_name, None, line_idx)
                if key in seen:
                    continue
                seen.add(key)
                references.append(CodeSymbolReference(target_kind='table', target_table=table_name, line=line_idx, snippet=snippet, confidence='confirmed' if f'"{table_name}"' in line or f"'{table_name}'" in line else 'inferred'))
    return references


def _symbol_summary(name: str, line: str) -> str:
    text = line.strip()
    if not text:
        return ''
    return text[:200]


def _index_python_file(source_file: Path, project_root: Path, known_tables: set[str], known_fields: dict[str, set[str]]) -> CodeFileIndex:
    text = source_file.read_text(encoding='utf-8')
    references = _collect_references(text, known_tables, known_fields)
    symbols: list[CodeSymbol] = []
    lines = text.splitlines()
    for match in _PY_CLASS_PATTERN.finditer(text):
        line_idx = text[:match.start()].count('\n')
        symbols.append(CodeSymbol(name=match.group(1), kind='class', signature=lines[line_idx].strip(), line_start=line_idx, line_end=line_idx, summary=_symbol_summary(match.group(1), lines[line_idx])))
    for match in _PY_DEF_PATTERN.finditer(text):
        line_idx = text[:match.start()].count('\n')
        symbols.append(CodeSymbol(name=match.group(1), kind='method', signature=lines[line_idx].strip(), line_start=line_idx, line_end=line_idx, summary=_symbol_summary(match.group(1), lines[line_idx])))
    return CodeFileIndex(source_path=source_file.relative_to(project_root).as_posix(), source_hash='sha256:' + hashlib.sha256(source_file.read_bytes()).hexdigest(), svn_revision=0, namespace=None, using=[], symbols=symbols, references=references, indexer_version='script-regex.v1', last_indexed_at=datetime.now(timezone.utc))


def _index_lua_file(source_file: Path, project_root: Path, known_tables: set[str], known_fields: dict[str, set[str]]) -> CodeFileIndex:
    text = source_file.read_text(encoding='utf-8')
    references = _collect_references(text, known_tables, known_fields)
    symbols: list[CodeSymbol] = []
    lines = text.splitlines()
    for match in _LUA_LOCAL_MODULE_PATTERN.finditer(text):
        line_idx = text[:match.start()].count('\n')
        symbols.append(CodeSymbol(name=match.group(1), kind='class', signature=lines[line_idx].strip(), line_start=line_idx, line_end=line_idx, summary=_symbol_summary(match.group(1), lines[line_idx])))
    for match in _LUA_FUNCTION_PATTERN.finditer(text):
        line_idx = text[:match.start()].count('\n')
        raw_name = match.group(1)
        symbol_name = raw_name.split('.')[-1].split(':')[-1]
        parent = raw_name.split('.')[0] if '.' in raw_name else None
        symbols.append(CodeSymbol(name=symbol_name, kind='method', parent=parent, signature=lines[line_idx].strip(), line_start=line_idx, line_end=line_idx, summary=_symbol_summary(symbol_name, lines[line_idx])))
    return CodeFileIndex(source_path=source_file.relative_to(project_root).as_posix(), source_hash='sha256:' + hashlib.sha256(source_file.read_bytes()).hexdigest(), svn_revision=0, namespace=None, using=[], symbols=symbols, references=references, indexer_version='script-regex.v1', last_indexed_at=datetime.now(timezone.utc))


async def rebuild_script_evidence(project_root: Path | None, scripts_config: ProjectScriptsSourceConfig | None) -> dict:
    result = {
        'success': False,
        'raw_script_index_count': 0,
        'canonical_script_count': 0,
        'indexed_scripts': [],
        'errors': [],
        'next_action': 'run_canonical_rebuild',
    }
    discovery = discover_script_sources(project_root, scripts_config)
    if project_root is None or not discovery['project_root']:
        result['errors'] = [{'error': 'project_root_not_configured'}]
        return result

    available_script_items = [item for item in discovery.get('script_files', []) if item.get('status') == 'available' and item.get('cold_start_supported', False)]
    if not available_script_items:
        result['errors'] = [
            {'source_path': item.get('source_path'), 'error': item.get('reason', 'script_source_discovery_error')}
            for item in discovery.get('errors', [])
        ] or [{'error': 'no_supported_script_files_available_for_rule_only_cold_start'}]
        result['next_action'] = str(discovery.get('next_action') or 'configure_scripts_source')
        return result

    known_tables, known_fields = _load_known_tables(project_root)
    csharp_indexer = CodeIndexer()
    indexed_scripts: list[dict] = []
    errors: list[dict] = []
    raw_count = 0
    canonical_count = 0
    for item in available_script_items:
        source_path = str(item['source_path'])
        source_file = project_root / source_path
        try:
            suffix = source_file.suffix.lower()
            if suffix == '.cs':
                code_index = await csharp_indexer.index_one(source_file, project_root, known_tables=known_tables, known_fields=known_fields)
            elif suffix == '.lua':
                code_index = _index_lua_file(source_file, project_root, known_tables, known_fields)
            elif suffix == '.py':
                code_index = _index_python_file(source_file, project_root, known_tables, known_fields)
            else:
                raise ValueError(f'unsupported script format: {suffix}')
            raw_file_name = source_path.replace('/', '__').replace('\\', '__') + '.json'
            raw_path = get_project_raw_scripts_dir(project_root) / raw_file_name
            _write_text_atomic(raw_path, code_index.model_dump_json(indent=2))
            canonical = build_canonical_script_facts(code_index, confirmed=False)
            _write_text_atomic(get_project_canonical_script_facts_path(project_root, canonical.script_id), canonical.model_dump_json(indent=2))
            raw_count += 1
            canonical_count += 1
            indexed_scripts.append({'script_id': canonical.script_id, 'source_path': code_index.source_path, 'symbol_count': len(code_index.symbols), 'related_refs': list(canonical.related_refs)})
        except Exception as exc:  # noqa: BLE001
            errors.append({'source_path': source_path, 'error': str(exc)})

    manifest_path = get_project_raw_scripts_dir(project_root) / 'script_indexes.json'
    _write_text_atomic(manifest_path, json.dumps({'version': '1.0', 'scripts': indexed_scripts}, ensure_ascii=False, indent=2))
    result.update({'success': canonical_count > 0, 'raw_script_index_count': raw_count, 'canonical_script_count': canonical_count, 'indexed_scripts': indexed_scripts, 'errors': errors})
    return result
