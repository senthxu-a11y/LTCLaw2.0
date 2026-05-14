from __future__ import annotations

from pathlib import Path

from ltclaw_gy_x.game import workbench_suggest_context as suggest_context_module


def test_build_workbench_suggest_formal_context_uses_map_gated_rag(monkeypatch):
    monkeypatch.setattr(
        suggest_context_module,
        'build_current_release_context',
        lambda project_root, query, **kwargs: {
            'mode': 'context',
            'release_id': 'release-001',
            'reason': None,
            'built_at': '2026-01-01T00:00:00Z',
            'chunks': [
                {
                    'chunk_id': 'chunk-001',
                    'citation_id': 'citation-001',
                    'text': 'Combat damage uses release formula.',
                }
            ],
            'citations': [
                {
                    'citation_id': 'citation-001',
                    'ref': 'doc:combat.formula',
                    'source_type': 'doc_knowledge',
                    'artifact_path': 'indexes/doc_knowledge.jsonl',
                    'source_path': 'Docs/Combat.md',
                    'title': 'Combat Overview',
                    'row': None,
                    'field': None,
                }
            ],
        },
    )

    payload = suggest_context_module.build_workbench_suggest_formal_context(Path('/tmp/project'), 'combat damage')

    assert payload['status'] == 'grounded'
    assert payload['release_id'] == 'release-001'
    assert payload['allowed_evidence_refs'] == ['doc:combat.formula']
    assert payload['evidence_catalog'][0]['evidence_ref'] == 'doc:combat.formula'
    assert payload['evidence_catalog'][0]['chunk_text'] == 'Combat damage uses release formula.'


def test_validate_workbench_suggest_payload_filters_invalid_entities_and_refs():
    tables_meta = [
        {
            'table': 'Hero',
            'primary_key': 'ID',
            'fields': [
                {'name': 'ID'},
                {'name': 'HP'},
                {'name': 'Name'},
            ],
            'row_index': [
                {'ID': 1, 'Name': 'Knight'},
                {'ID': 2, 'Name': 'Mage'},
            ],
        }
    ]
    formal_context = {
        'status': 'grounded',
        'release_id': 'release-001',
        'allowed_evidence_refs': ['doc:combat.formula'],
    }
    parsed = {
        'message': 'ok',
        'changes': [
            {'table': 'Skill', 'row_id': 1, 'field': 'Cost', 'new_value': 10},
            {'table': 'Hero', 'row_id': 1, 'field': 'Cost', 'new_value': 10},
            {'table': 'Hero', 'row_id': 99, 'field': 'HP', 'new_value': 10},
            {
                'table': 'Hero',
                'row_id': 1,
                'field': 'HP',
                'new_value': 120,
                'reason': 'Boost frontline hero.',
                'confidence': 0.91,
                'uses_draft_overlay': True,
                'evidence_refs': ['doc:combat.formula', 'doc:fake'],
            },
        ],
    }

    payload = suggest_context_module.validate_workbench_suggest_payload(
        parsed,
        tables_meta=tables_meta,
        formal_context=formal_context,
        draft_overlay=[{'table': 'Hero', 'row_id': 1, 'field': 'HP', 'new_value': 110}],
    )

    assert len(payload['changes']) == 1
    change = payload['changes'][0]
    assert change['table'] == 'Hero'
    assert change['field'] == 'HP'
    assert change['row_id'] == 1
    assert change['confidence'] == 0.91
    assert change['uses_draft_overlay'] is True
    assert change['source_release_id'] == 'release-001'
    assert change['validation_status'] == 'validated'
    assert change['evidence_refs'] == ['doc:combat.formula']
    assert payload['evidence_refs'] == ['doc:combat.formula']
    assert 'outside context_tables' in payload['message']
