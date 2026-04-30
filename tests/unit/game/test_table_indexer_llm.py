from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import openpyxl
import pytest

from ltclaw_gy_x.game.config import (
    FilterConfig,
    ProjectConfig,
    ProjectMeta,
    SvnConfig,
    TableConvention,
)
from ltclaw_gy_x.game.models import FieldConfidence
from ltclaw_gy_x.game.table_indexer import TableIndexer


def _project(svn_root: Path) -> ProjectConfig:
    return ProjectConfig(
        project=ProjectMeta(name="t", engine="Unity", language="zh-CN"),
        svn=SvnConfig(root=str(svn_root), poll_interval_seconds=300, jitter_seconds=30),
        paths=[],
        filters=FilterConfig(include_ext=[".xlsx", ".csv"], exclude_glob=[]),
        table_convention=TableConvention(),
        doc_templates={},
        models={},
    )


def _write_xlsx(path: Path) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    assert ws is not None
    ws.append(["ID", "Name", "Damage"])
    ws.append([1, "火球", 100])
    ws.append([2, "冰刺", 120])
    wb.save(path)


@pytest.mark.asyncio
async def test_index_one_uses_llm_descriptions_and_summary(tmp_path):
    svn_root = tmp_path / "svn"
    svn_root.mkdir()
    table_path = svn_root / "SkillTable.xlsx"
    _write_xlsx(table_path)
    router = SimpleNamespace()
    router.call_model = AsyncMock(
        side_effect=[
            '{"ID":{"description":"技能ID","confidence":0.95},"Name":{"description":"技能名","confidence":0.9},"Damage":{"description":"伤害值","confidence":0.88}}',
            "技能伤害配置总表",
        ]
    )
    indexer = TableIndexer(_project(svn_root), router, tmp_path / "cache")

    result = await indexer.index_one(table_path, svn_root, 123)

    assert result.ai_summary == "技能伤害配置总表"
    assert result.ai_summary_confidence == 0.8
    assert [field.description for field in result.fields] == ["技能ID", "技能名", "伤害值"]
    assert all(field.confidence == FieldConfidence.HIGH_AI for field in result.fields)


@pytest.mark.asyncio
async def test_index_one_treats_empty_llm_response_as_failure(tmp_path):
    svn_root = tmp_path / "svn"
    svn_root.mkdir()
    table_path = svn_root / "SkillTable.xlsx"
    _write_xlsx(table_path)
    router = SimpleNamespace()
    router.call_model = AsyncMock(side_effect=["", "   "])
    indexer = TableIndexer(_project(svn_root), router, tmp_path / "cache")

    result = await indexer.index_one(table_path, svn_root, 123)
    assert result.ai_summary == "SkillTable数据配置表"
    assert result.ai_summary_confidence == 0.1
    assert all(field.description.endswith("字段") for field in result.fields)
    assert all(field.confidence == FieldConfidence.LOW_AI for field in result.fields)


@pytest.mark.asyncio
async def test_index_one_treats_llm_exception_as_failure(tmp_path):
    svn_root = tmp_path / "svn"
    svn_root.mkdir()
    table_path = svn_root / "SkillTable.xlsx"
    _write_xlsx(table_path)

    router = SimpleNamespace(call_model=AsyncMock(side_effect=RuntimeError("boom")))
    indexer = TableIndexer(_project(svn_root), router, tmp_path / "cache")

    result = await indexer.index_one(table_path, svn_root, 123)
    assert result.ai_summary == "SkillTable数据配置表"
    assert result.ai_summary_confidence == 0.1
    assert all(field.description.endswith("字段") for field in result.fields)
