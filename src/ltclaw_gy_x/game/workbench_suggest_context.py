from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .knowledge_rag_context import build_current_release_context


DEFAULT_FORMAL_MAX_CHUNKS = 6
DEFAULT_FORMAL_MAX_CHARS = 8000


def build_workbench_suggest_formal_context(
    project_root: Path | None,
    user_intent: str,
) -> dict[str, Any]:
    query = str(user_intent or '').strip()
    if project_root is None:
        return {
            'mode': 'formal_context_unavailable',
            'status': 'formal_context_unavailable',
            'release_id': None,
            'reason': 'project_root_unavailable',
            'built_at': None,
            'chunks': [],
            'citations': [],
            'evidence_catalog': [],
            'allowed_evidence_refs': [],
        }

    context = build_current_release_context(
        project_root,
        query,
        max_chunks=DEFAULT_FORMAL_MAX_CHUNKS,
        max_chars=DEFAULT_FORMAL_MAX_CHARS,
    )
    evidence_catalog = _build_evidence_catalog(context)
    return {
        'mode': context.get('mode'),
        'status': _formal_context_status(context),
        'release_id': context.get('release_id'),
        'reason': context.get('reason'),
        'built_at': context.get('built_at'),
        'chunks': list(context.get('chunks') or []),
        'citations': list(context.get('citations') or []),
        'evidence_catalog': evidence_catalog,
        'allowed_evidence_refs': sorted({item['evidence_ref'] for item in evidence_catalog}),
    }


def build_workbench_suggest_prompt(
    *,
    user_intent: str,
    tables_meta: list[dict[str, Any]],
    related_meta: list[dict[str, Any]],
    chat_history: list[dict[str, str]],
    draft_overlay: list[dict[str, Any]],
    formal_context: dict[str, Any],
) -> str:
    prompt_sections: list[str] = []
    prompt_sections.append(
        '你是游戏数值策划助手。你只能基于提供的上下文输出严格 JSON。'
        '不要修改 Formal Map、Current Release 或正式 RAG。'
    )
    prompt_sections.append(
        'Formal Knowledge Context (正式证据, 仅可来自 Current Release + Map-gated RAG):\n'
        f'{json.dumps(_prompt_formal_context(formal_context), ensure_ascii=False)}'
    )
    prompt_sections.append(
        'Workbench Runtime Context (仅本次运行态上下文, 不是正式证据):\n'
        f'{json.dumps({"tables": tables_meta, "related_tables": related_meta}, ensure_ascii=False)}'
    )
    prompt_sections.append(
        'Draft Overlay (非正式上下文, 只能辅助建议, 不能作为 formal evidence):\n'
        f'{json.dumps(draft_overlay, ensure_ascii=False)}'
    )
    prompt_sections.append(
        'Conversation Context (最近对话历史, 不是正式证据):\n'
        f'{json.dumps(chat_history, ensure_ascii=False)}'
    )
    prompt_sections.append(f'User Intent:\n{str(user_intent or "").strip()}')
    prompt_sections.append(
        '输出规则:\n'
        '1) 只输出严格 JSON, 不要 markdown 代码块, 不要额外解释。\n'
        '2) table 只能来自 Workbench Runtime Context 的 tables[].table。\n'
        '3) field 只能来自对应 tables[].fields[].name。\n'
        '4) row_id 必须来自对应 tables[].row_index 中 primary_key 的真实值; 找不到就不要编造。\n'
        '5) evidence_refs 只能使用 Formal Knowledge Context 中列出的 evidence_ref; 没有正式证据时必须输出空数组。\n'
        '6) Draft Overlay 可辅助 uses_draft_overlay=true, 但不能作为 formal evidence。\n'
        '7) 如果无法给出合法 change, changes 留空, 在 message 中说明。\n'
        'JSON schema:\n'
        '{'
        '"message": "<简短说明>", '
        '"changes": ['
        '{'
        '"table": "<表>", '
        '"row_id": "<行ID>", '
        '"field": "<字段>", '
        '"new_value": <新值>, '
        '"reason": "<理由>", '
        '"confidence": 0.0, '
        '"uses_draft_overlay": false, '
        '"evidence_refs": ["<formal evidence_ref>"]'
        '}'
        ']'
        '}'
    )
    return '\n\n'.join(prompt_sections)


def validate_workbench_suggest_payload(
    parsed: Mapping[str, Any] | None,
    *,
    tables_meta: list[dict[str, Any]],
    formal_context: dict[str, Any],
    draft_overlay: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = dict(parsed or {})
    table_validators = _build_table_validators(tables_meta)
    allowed_evidence_refs = set(formal_context.get('allowed_evidence_refs') or [])
    release_id = formal_context.get('release_id')
    raw_changes = payload.get('changes') or []
    changes: list[dict[str, Any]] = []
    dropped: list[str] = []

    for index, raw_change in enumerate(raw_changes, start=1):
        if not isinstance(raw_change, Mapping):
            dropped.append(f'change[{index}] is not an object')
            continue
        normalized = _normalize_change_candidate(
            raw_change,
            table_validators=table_validators,
            allowed_evidence_refs=allowed_evidence_refs,
            draft_overlay_present=bool(draft_overlay),
            source_release_id=release_id,
        )
        if normalized is None:
            dropped.append(_describe_invalid_change(index, raw_change, table_validators))
            continue
        changes.append(normalized)

    message = str(payload.get('message') or '').strip()
    if dropped:
        suffix = '; '.join(dropped[:3])
        message = f'{message} Validation filtered invalid suggestions: {suffix}'.strip()

    evidence_refs = sorted({ref for change in changes for ref in change.get('evidence_refs', [])})
    return {
        'message': message,
        'changes': changes,
        'evidence_refs': evidence_refs,
        'formal_context_status': formal_context.get('status'),
    }


def _formal_context_status(context: Mapping[str, Any]) -> str:
    mode = str(context.get('mode') or '').strip() or 'formal_context_unavailable'
    if mode == 'context':
        return 'grounded'
    reason = str(context.get('reason') or '').strip()
    return reason or mode


def _build_evidence_catalog(context: Mapping[str, Any]) -> list[dict[str, Any]]:
    chunks_by_citation = {
        str(chunk.get('citation_id') or '').strip(): str(chunk.get('text') or '').strip()
        for chunk in list(context.get('chunks') or [])
        if str(chunk.get('citation_id') or '').strip()
    }
    catalog: list[dict[str, Any]] = []
    for citation in list(context.get('citations') or []):
        if not isinstance(citation, Mapping):
            continue
        evidence_ref = str(citation.get('ref') or '').strip()
        if not evidence_ref:
            continue
        citation_id = str(citation.get('citation_id') or '').strip()
        catalog.append(
            {
                'evidence_ref': evidence_ref,
                'citation_id': citation_id,
                'release_id': context.get('release_id'),
                'source_type': citation.get('source_type'),
                'artifact_path': citation.get('artifact_path'),
                'source_path': citation.get('source_path'),
                'title': citation.get('title'),
                'row': citation.get('row'),
                'field': citation.get('field'),
                'chunk_text': chunks_by_citation.get(citation_id, ''),
            }
        )
    return catalog


def _prompt_formal_context(formal_context: Mapping[str, Any]) -> dict[str, Any]:
    return {
        'status': formal_context.get('status'),
        'release_id': formal_context.get('release_id'),
        'reason': formal_context.get('reason'),
        'evidence_catalog': list(formal_context.get('evidence_catalog') or []),
    }


def _build_table_validators(tables_meta: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    validators: dict[str, dict[str, Any]] = {}
    for table in tables_meta:
        table_name = str(table.get('table') or '').strip()
        if not table_name:
            continue
        primary_key = str(table.get('primary_key') or 'ID')
        fields = {
            str(field.get('name') or '').strip()
            for field in list(table.get('fields') or [])
            if str(field.get('name') or '').strip()
        }
        row_ids = {
            str(row.get(primary_key))
            for row in list(table.get('row_index') or [])
            if row.get(primary_key) not in (None, '')
        }
        validators[table_name] = {
            'primary_key': primary_key,
            'fields': fields,
            'row_ids': row_ids,
        }
    return validators


def _normalize_change_candidate(
    raw_change: Mapping[str, Any],
    *,
    table_validators: dict[str, dict[str, Any]],
    allowed_evidence_refs: set[str],
    draft_overlay_present: bool,
    source_release_id: str | None,
) -> dict[str, Any] | None:
    table = str(raw_change.get('table') or '').strip()
    field = str(raw_change.get('field') or '').strip()
    row_id = raw_change.get('row_id')
    if table not in table_validators:
        return None
    table_validator = table_validators[table]
    if field not in table_validator['fields']:
        return None
    if row_id in (None, ''):
        return None
    if str(row_id) not in table_validator['row_ids']:
        return None

    evidence_refs = []
    seen_refs: set[str] = set()
    for ref in list(raw_change.get('evidence_refs') or []):
        normalized_ref = str(ref or '').strip()
        if not normalized_ref or normalized_ref in seen_refs or normalized_ref not in allowed_evidence_refs:
            continue
        seen_refs.add(normalized_ref)
        evidence_refs.append(normalized_ref)

    confidence = raw_change.get('confidence')
    try:
        confidence_value = max(0.0, min(float(confidence), 1.0))
    except Exception:
        confidence_value = None

    uses_draft_overlay = bool(raw_change.get('uses_draft_overlay')) and draft_overlay_present
    validation_status = 'validated' if evidence_refs else 'validated_runtime_only'
    return {
        'table': table,
        'row_id': row_id,
        'field': field,
        'new_value': raw_change.get('new_value'),
        'reason': str(raw_change.get('reason') or ''),
        'confidence': confidence_value,
        'uses_draft_overlay': uses_draft_overlay,
        'source_release_id': source_release_id if evidence_refs else None,
        'validation_status': validation_status,
        'evidence_refs': evidence_refs,
    }


def _describe_invalid_change(
    index: int,
    raw_change: Mapping[str, Any],
    table_validators: Mapping[str, dict[str, Any]],
) -> str:
    table = str(raw_change.get('table') or '').strip()
    field = str(raw_change.get('field') or '').strip()
    row_id = raw_change.get('row_id')
    if table not in table_validators:
        return f'change[{index}] table={table or "<missing>"} is outside context_tables'
    if field not in table_validators[table]['fields']:
        return f'change[{index}] field={field or "<missing>"} is not a valid field of {table}'
    if row_id in (None, '') or str(row_id) not in table_validators[table]['row_ids']:
        return f'change[{index}] row_id={row_id!r} is not a valid {table} primary key'
    return f'change[{index}] is invalid'