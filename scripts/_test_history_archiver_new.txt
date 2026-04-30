"""单元测试: history_archiver 阈值与归档行为。"""
import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ltclaw_gy_x.game.history_archiver import (
    record_change,
    diff_and_archive,
    flush_daily,
    flush_weekly_to_milestone,
)
from ltclaw_gy_x.game.models import FieldInfo, FieldConfidence, TableIndex


def _make_table(name="Hero", rows=10, fields=None, summary="s", revision=1):
    if fields is None:
        fields = [
            FieldInfo(name="ID", type="int", description="", confidence=FieldConfidence.CONFIRMED, inferred_by="rule"),
            FieldInfo(name="HP", type="int", description="", confidence=FieldConfidence.HIGH_AI, inferred_by="llm"),
        ]
    return TableIndex(
        table_name=name,
        source_path=f"t/{name}.xlsx",
        source_hash="sha256:x",
        svn_revision=revision,
        row_count=rows,
        primary_key="ID",
        ai_summary=summary,
        ai_summary_confidence=0.8,
        fields=fields,
        last_indexed_at=datetime(2026, 1, 1),
        indexer_model="m",
    )


def test_record_change_new_table_triggers_created():
    entry = record_change(None, _make_table())
    assert entry is not None
    assert "created" in entry.changes


def test_record_change_field_added():
    before = _make_table()
    after_fields = [
        FieldInfo(name="ID", type="int", description="", confidence=FieldConfidence.CONFIRMED, inferred_by="rule"),
        FieldInfo(name="HP", type="int", description="", confidence=FieldConfidence.HIGH_AI, inferred_by="llm"),
        FieldInfo(name="MP", type="int", description="", confidence=FieldConfidence.HIGH_AI, inferred_by="llm"),
    ]
    after = _make_table(fields=after_fields, revision=2)
    entry = record_change(before, after)
    assert entry is not None
    assert "fields_added" in entry.changes
    assert entry.fields_added == ["MP"]


def test_record_change_row_count_delta():
    entry = record_change(_make_table(rows=10), _make_table(rows=11, revision=2))
    assert entry is not None
    assert "row_count_delta" in entry.changes


def test_record_change_no_change_returns_none():
    entry = record_change(_make_table(), _make_table())
    assert entry is None


def test_record_change_summary_change_only():
    entry = record_change(
        _make_table(summary="old"),
        _make_table(summary="new", revision=2),
    )
    assert entry is not None
    assert "summary_changed" in entry.changes


def test_diff_and_archive_writes_jsonl(tmp_path):
    history = tmp_path / "history"
    written = diff_and_archive(
        before_tables=[_make_table(rows=10)],
        after_tables=[_make_table(rows=12, revision=2)],
        history_dir=history,
    )
    assert len(written) == 1
    files = list((history / "Hero").glob("*.jsonl"))
    assert len(files) == 1
    line = files[0].read_text(encoding="utf-8").strip()
    data = json.loads(line)
    assert data["table_name"] == "Hero"
    assert "row_count_delta" in data["changes"]


def test_diff_and_archive_skips_below_threshold(tmp_path):
    history = tmp_path / "history"
    written = diff_and_archive(
        before_tables=[_make_table()],
        after_tables=[_make_table()],
        history_dir=history,
    )
    assert written == []
    assert not history.exists() or not any(history.glob("**/*.jsonl"))


def test_flush_daily_aggregates_old_entries(tmp_path):
    history = tmp_path / "history"
    table_dir = history / "Hero"
    table_dir.mkdir(parents=True)
    old_day = datetime.now() - timedelta(days=45)
    old_file = table_dir / f"{old_day.strftime('%Y-%m-%d')}.jsonl"
    old_file.write_text('{"table_name":"Hero","timestamp":"2026-01-01","revision_before":1,"revision_after":2,"changes":["row_count_delta"],"fields_added":[],"fields_removed":[],"row_count_before":10,"row_count_after":11,"summary_changed":false}\n', encoding="utf-8")
    fresh_file = table_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    fresh_file.write_text('{"table_name":"Hero"}\n', encoding="utf-8")

    processed = flush_daily(history, days_to_keep=30)
    assert processed == 1
    assert not old_file.exists()
    assert fresh_file.exists()
    weekly_files = list((history / "weekly").glob("*.json"))
    assert len(weekly_files) == 1
    bucket = json.loads(weekly_files[0].read_text(encoding="utf-8"))
    assert len(bucket) == 1
    assert bucket[0]["table_name"] == "Hero"


def test_flush_weekly_to_milestone(tmp_path):
    history = tmp_path / "history"
    weekly_dir = history / "weekly"
    weekly_dir.mkdir(parents=True)
    target = weekly_dir / "2026-W10.json"
    target.write_text("[]", encoding="utf-8")
    other = weekly_dir / "2026-W11.json"
    other.write_text("[]", encoding="utf-8")

    moved = flush_weekly_to_milestone(history, milestone_tags=["2026-W10"])
    assert moved == 1
    assert (history / "milestone" / "2026-W10.json").exists()
    assert other.exists()
