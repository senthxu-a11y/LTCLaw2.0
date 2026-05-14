"""单元测试: TableIndexer 工具方法。"""
from types import SimpleNamespace

import pytest

import ltclaw_gy_x.game.table_indexer as table_indexer_module
from ltclaw_gy_x.game.config import (
    FilterConfig,
    ProjectConfig,
    ProjectMeta,
    SvnConfig,
    TableConvention,
)
from ltclaw_gy_x.game.table_indexer import TableIndexer


def _project():
    return ProjectConfig(
        project=ProjectMeta(name="t", engine="Unity", language="zh-CN"),
        svn=SvnConfig(root="svn://x", poll_interval_seconds=300, jitter_seconds=30),
        paths=[],
        filters=FilterConfig(include_ext=[".xlsx", ".csv"], exclude_glob=[]),
        table_convention=TableConvention(),
        doc_templates={},
        models={},
    )


@pytest.fixture
def indexer(tmp_path):
    return TableIndexer(project=_project(), model_router=None, cache_dir=tmp_path / "cache")


def test_cache_dirs_created(indexer):
    assert indexer.cache_dir.exists()
    assert indexer.field_cache_dir.exists()
    assert indexer.summary_cache_dir.exists()


def test_calculate_file_hash_stable(indexer, tmp_path):
    f = tmp_path / "data.csv"
    f.write_bytes(b"hello,world\n")
    h1 = indexer._calculate_file_hash(f)
    h2 = indexer._calculate_file_hash(f)
    assert h1 == h2
    assert h1.startswith("sha256:")


def test_calculate_file_hash_changes_on_content(indexer, tmp_path):
    a = tmp_path / "a.csv"; a.write_bytes(b"a")
    b = tmp_path / "b.csv"; b.write_bytes(b"b")
    assert indexer._calculate_file_hash(a) != indexer._calculate_file_hash(b)


def test_infer_field_type_str_when_empty(indexer):
    assert indexer._infer_field_type([]) == "str"
    assert indexer._infer_field_type([None, ""]) == "str"


def test_infer_field_type_numeric(indexer):
    result = indexer._infer_field_type([1, 2, 3])
    assert isinstance(result, str)
    assert result != ""


@pytest.mark.asyncio
async def test_describe_fields_uses_field_describer_model_type(indexer):
    calls = []
    indexer.model_router = SimpleNamespace(
        call_model=lambda prompt, model_type="default": _record_call(calls, prompt, model_type, '{"Damage": {"description": "伤害", "confidence": 0.9}}')
    )

    payload = await indexer._describe_fields_with_llm(
        "SkillTable",
        [{"name": "Damage", "type": "int", "sample_values": [100, 120]}],
    )

    assert calls == ["field_describer"]
    assert payload["Damage"]["description"] == "伤害"


@pytest.mark.asyncio
async def test_generate_table_summary_uses_table_summarizer_model_type(indexer):
    calls = []
    indexer.model_router = SimpleNamespace(
        call_model=lambda prompt, model_type="default": _record_call(calls, prompt, model_type, "技能伤害配置表")
    )
    fields = [SimpleNamespace(name="Damage", description="伤害")]

    summary, confidence = await indexer._generate_table_summary("SkillTable", fields, [{"Damage": 100}])

    assert calls == ["table_summarizer"]
    assert summary == "技能伤害配置表"
    assert confidence == 0.8


@pytest.mark.asyncio
async def test_describe_fields_logs_error_and_falls_back_when_model_fails(indexer, monkeypatch):
    async def _raise(*_args, **_kwargs):
        raise RuntimeError("provider boom")

    indexer.model_router = SimpleNamespace(call_model=_raise)
    logged = []

    monkeypatch.setattr(table_indexer_module.logger, "error", lambda message: logged.append(message))

    payload = await indexer._describe_fields_with_llm(
        "SkillTable",
        [{"name": "Damage", "type": "int", "sample_values": [100, 120]}],
    )

    assert payload == {
        "Damage": {"description": "Damage字段", "confidence": 0.1}
    }
    assert any("LLM字段描述生成失败" in message for message in logged)


@pytest.mark.asyncio
async def test_generate_table_summary_logs_error_and_falls_back_on_empty_response(indexer, monkeypatch):
    async def _empty(*_args, **_kwargs):
        return "   "

    indexer.model_router = SimpleNamespace(call_model=_empty)
    fields = [SimpleNamespace(name="Damage", description="伤害")]
    logged = []

    monkeypatch.setattr(table_indexer_module.logger, "error", lambda message: logged.append(message))

    summary, confidence = await indexer._generate_table_summary("SkillTable", fields, [{"Damage": 100}])

    assert summary == "SkillTable数据配置表"
    assert confidence == 0.1
    assert any("生成表格摘要失败" in message for message in logged)


async def _record_call(calls, prompt, model_type, response):
    calls.append(model_type)
    return response