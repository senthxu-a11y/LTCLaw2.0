from __future__ import annotations

import asyncio
from pathlib import Path

import openpyxl

from ltclaw_gy_x.game.config import ProjectTablesSourceConfig
from ltclaw_gy_x.game.raw_index_rebuild import rebuild_raw_table_indexes
from ltclaw_gy_x.game.source_discovery import discover_table_sources


def _write_xlsx(path: Path, sheets: list[tuple[str, list[list[object]]]]) -> None:
    workbook = openpyxl.Workbook()
    first_sheet = workbook.active
    assert first_sheet is not None
    first_title, first_rows = sheets[0]
    first_sheet.title = first_title
    for row in first_rows:
        first_sheet.append(row)
    for title, rows in sheets[1:]:
        sheet = workbook.create_sheet(title=title)
        for row in rows:
            sheet.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)


def test_discover_table_sources_marks_xlsx_available_for_rule_only(tmp_path):
    project_root = tmp_path / 'project-root'
    tables_dir = project_root / 'Tables'
    _write_xlsx(
        tables_dir / 'WeaponConfig.xlsx',
        [('Weapons', [['ID', 'WeaponName'], [1001, 'IronSword']])],
    )

    result = discover_table_sources(
        project_root,
        ProjectTablesSourceConfig(
            roots=['Tables'],
            include=['**/*.xlsx'],
            exclude=[],
        ),
    )

    assert result['table_files'] == [
        {
            'source_path': 'Tables/WeaponConfig.xlsx',
            'format': 'xlsx',
            'status': 'available',
            'reason': 'matched_supported_format',
            'cold_start_supported': True,
            'cold_start_reason': 'rule_only_supported_xlsx',
        }
    ]
    assert result['summary']['available_table_count'] == 1
    assert result['next_action'] == 'run_raw_index'


def test_rebuild_raw_table_indexes_reads_first_non_empty_sheet_from_xlsx(tmp_path):
    project_root = tmp_path / 'project-root'
    tables_dir = project_root / 'Tables'
    _write_xlsx(
        tables_dir / 'WeaponConfig.xlsx',
        [
            ('EmptyFirst', []),
            ('Weapons', [['ID', 'WeaponName', 'Attack', 'Rarity'], [1001, 'IronSword', 12, 'Common']]),
            ('Ignored', [['Code', 'Value'], ['A', 1]]),
        ],
    )

    result = asyncio.run(
        rebuild_raw_table_indexes(
            project_root,
            ProjectTablesSourceConfig(
                roots=['Tables'],
                include=['**/*.xlsx'],
                exclude=[],
                header_row=1,
                primary_key_candidates=['ID'],
            ),
        )
    )

    assert result['success'] is True
    assert result['raw_table_index_count'] == 1
    assert result['indexed_tables'] == [
        {
            'table_id': 'WeaponConfig',
            'source_path': 'Tables/WeaponConfig.xlsx',
            'row_count': 1,
            'field_count': 4,
            'primary_key': 'ID',
        }
    ]
    assert result['errors'] == []