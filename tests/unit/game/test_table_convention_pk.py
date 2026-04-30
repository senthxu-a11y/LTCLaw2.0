# -*- coding: utf-8 -*-
"""Tests for TableConvention.resolve_primary_key (per-table override + auto-detect)."""
from __future__ import annotations

from ltclaw_gy_x.game.config import TableConvention


def test_default_when_no_headers():
    tc = TableConvention()
    assert tc.resolve_primary_key() == "ID"
    assert tc.resolve_primary_key("AnyTable") == "ID"


def test_per_table_override_wins():
    tc = TableConvention(per_table_primary_keys={"道具": "道具id"})
    assert tc.resolve_primary_key("道具", headers=["道具id", "Name"]) == "道具id"


def test_default_matched_in_headers_uses_actual_case():
    tc = TableConvention(primary_key_field="ID")
    # 实际 header 是 "Id"，应原样返回
    assert tc.resolve_primary_key("Hero", headers=["Id", "Name"]) == "Id"


def test_auto_detect_chinese_id():
    tc = TableConvention(primary_key_field="ID")
    headers = ["道具id", "名称"]
    assert tc.resolve_primary_key("Item", headers=headers) == "道具id"


def test_auto_detect_exact_id_alias():
    tc = TableConvention(primary_key_field="ID")
    headers = ["编号", "名称"]
    assert tc.resolve_primary_key("X", headers=headers) == "编号"


def test_auto_detect_disabled_falls_back():
    tc = TableConvention(primary_key_field="ID", auto_detect_primary_key=False)
    headers = ["道具id", "名称"]
    # 关闭嗅探后，回退到默认 "ID"（即使 headers 里没有）
    assert tc.resolve_primary_key("X", headers=headers) == "ID"


def test_per_table_priority_over_autodetect():
    tc = TableConvention(per_table_primary_keys={"X": "MyKey"})
    headers = ["道具id", "Name"]
    assert tc.resolve_primary_key("X", headers=headers) == "MyKey"
