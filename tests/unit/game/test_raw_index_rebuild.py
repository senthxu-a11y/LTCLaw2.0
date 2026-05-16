from __future__ import annotations

import asyncio
from pathlib import Path

import openpyxl

from ltclaw_gy_x.game.config import ProjectTablesSourceConfig
from ltclaw_gy_x.game.raw_index_rebuild import rebuild_raw_table_indexes


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


def test_rebuild_raw_table_indexes_succeeds_for_csv(tmp_path):
    project_root = tmp_path / 'project-root'
    tables_dir = project_root / 'Tables'
    tables_dir.mkdir(parents=True)
    (tables_dir / 'HeroTable.csv').write_text(
        'ID,Name,HP,Attack\n1,HeroA,100,20\n',
        encoding='utf-8',
    )

    result = asyncio.run(
        rebuild_raw_table_indexes(
            project_root,
            ProjectTablesSourceConfig(
                roots=['Tables'],
                include=['**/*.csv'],
                exclude=[],
                header_row=1,
                primary_key_candidates=['ID'],
            ),
        )
    )

    assert result['success'] is True
    assert result['raw_table_index_count'] == 1
    assert result['indexed_tables'][0]['table_id'] == 'HeroTable'
    assert result['errors'] == []


def test_rebuild_raw_table_indexes_succeeds_for_xlsx(tmp_path):
    project_root = tmp_path / 'project-root'
    tables_dir = project_root / 'Tables'
    tables_dir.mkdir(parents=True)
    _write_xlsx(
        tables_dir / 'HeroTable.xlsx',
        [('Heroes', [['ID', 'Name', 'HP', 'Attack'], [1, 'HeroA', 100, 20]])],
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
    assert result['indexed_tables'][0]['table_id'] == 'HeroTable'
    assert result['indexed_tables'][0]['source_path'] == 'Tables/HeroTable.xlsx'
    assert result['indexed_tables'][0]['row_count'] == 1
    assert result['errors'] == []


def test_rebuild_raw_table_indexes_succeeds_for_txt(tmp_path):
    project_root = tmp_path / 'project-root'
    tables_dir = project_root / 'Tables'
    tables_dir.mkdir(parents=True)
    (tables_dir / 'HeroTable.txt').write_text(
        '# Hero table\nID\tName\tHP\tAttack\n1\tHeroA\t100\t20\n',
        encoding='utf-8',
    )

    result = asyncio.run(
        rebuild_raw_table_indexes(
            project_root,
            ProjectTablesSourceConfig(
                roots=['Tables'],
                include=['**/*.txt'],
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
            'table_id': 'HeroTable',
            'source_path': 'Tables/HeroTable.txt',
            'row_count': 1,
            'field_count': 4,
            'primary_key': 'ID',
        }
    ]
    assert result['errors'] == []


def test_rebuild_raw_table_indexes_indexes_csv_xlsx_and_txt_when_all_exist(tmp_path):
    project_root = tmp_path / 'project-root'
    tables_dir = project_root / 'Tables'
    tables_dir.mkdir(parents=True)
    (tables_dir / 'HeroTable.csv').write_text(
        'ID,Name,HP,Attack\n1,HeroA,100,20\n',
        encoding='utf-8',
    )
    _write_xlsx(
        tables_dir / 'OtherTable.xlsx',
        [('Weapons', [['ID', 'Name'], [1001, 'IronSword']])],
    )
    (tables_dir / 'EnemyConfig.txt').write_text(
        '# Enemy config table\nID\tName\tHP\tAttack\n2001\tSlime\t30\t5\n',
        encoding='utf-8',
    )

    result = asyncio.run(
        rebuild_raw_table_indexes(
            project_root,
            ProjectTablesSourceConfig(
                roots=['Tables'],
                include=['**/*.csv', '**/*.xlsx', '**/*.txt'],
                exclude=[],
                header_row=1,
                primary_key_candidates=['ID'],
            ),
        )
    )

    assert result['success'] is True
    assert result['raw_table_index_count'] == 3
    assert {item['table_id'] for item in result['indexed_tables']} == {'HeroTable', 'OtherTable', 'EnemyConfig'}