# -*- coding: utf-8 -*-
"""Unit tests for CodeIndexer (regex.v1)."""
from __future__ import annotations

from pathlib import Path

import pytest

from ltclaw_gy_x.game.code_indexer import CodeIndexer
from ltclaw_gy_x.game.models import CodeFileIndex


def _write(tmp: Path, name: str, content: str) -> Path:
    p = tmp / name
    p.write_text(content, encoding="utf-8")
    return p


@pytest.mark.asyncio
async def test_extract_basic_class_and_method(tmp_path):
    src = _write(tmp_path, "HeroSkill.cs", """\
using System;

namespace Game.Skill {
    public class HeroSkill {
        /// <summary>Calculate damage.</summary>
        public int CalcDamage(int atk) {
            return atk * 2;
        }
    }
}
""")
    idx = await CodeIndexer().index_one(src, tmp_path)
    assert isinstance(idx, CodeFileIndex)
    assert idx.namespace == "Game.Skill"
    assert "System" in idx.using
    kinds = {(s.name, s.kind) for s in idx.symbols}
    assert ("HeroSkill", "class") in kinds
    assert ("CalcDamage", "method") in kinds
    method = next(s for s in idx.symbols if s.name == "CalcDamage")
    assert method.parent == "HeroSkill"
    assert "CalcDamage" in method.signature
    assert "Calculate damage" in method.summary


@pytest.mark.asyncio
async def test_extract_table_reference_via_known_tables(tmp_path):
    src = _write(tmp_path, "HeroLogic.cs", """\
namespace Game {
    public class HeroLogic {
        void Init() {
            var t = TableManager.Get("HeroTable");
        }
    }
}
""")
    idx = await CodeIndexer().index_one(
        src, tmp_path, known_tables={"HeroTable"},
    )
    refs = [r for r in idx.references if r.target_table == "HeroTable"]
    assert refs, "should find at least one HeroTable reference"
    assert any(r.target_kind == "table" for r in refs)
    # 字符串字面量 → confirmed
    assert any(r.confidence == "confirmed" for r in refs)


@pytest.mark.asyncio
async def test_extract_field_reference(tmp_path):
    src = _write(tmp_path, "Stat.cs", """\
namespace Game {
    public class Stat {
        public int Read() {
            var hp = HeroTable.HP;
            return hp;
        }
    }
}
""")
    idx = await CodeIndexer().index_one(
        src, tmp_path,
        known_tables={"HeroTable"},
        known_fields={"HeroTable": {"HP"}},
    )
    field_refs = [
        r for r in idx.references
        if r.target_kind == "field"
        and r.target_table == "HeroTable"
        and r.target_field == "HP"
    ]
    assert len(field_refs) == 1
    assert field_refs[0].confidence == "confirmed"


@pytest.mark.asyncio
async def test_summary_from_doc_comment(tmp_path):
    src = _write(tmp_path, "Hero.cs", """\
namespace Game {
    /// <summary>Hero stats.</summary>
    public class Hero {
    }
}
""")
    idx = await CodeIndexer().index_one(src, tmp_path)
    hero = next((s for s in idx.symbols if s.name == "Hero" and s.kind == "class"), None)
    assert hero is not None
    assert "Hero stats" in hero.summary


@pytest.mark.asyncio
async def test_empty_file_returns_empty_index(tmp_path):
    src = _write(tmp_path, "Empty.cs", "")
    idx = await CodeIndexer().index_one(src, tmp_path)
    assert idx.symbols == []
    assert idx.references == []
    assert idx.source_hash.startswith("sha256:")
    assert idx.source_path.endswith("Empty.cs")


@pytest.mark.asyncio
async def test_reference_attached_to_enclosing_method(tmp_path):
    src = _write(tmp_path, "Logic.cs", """\
namespace Game {
    public class Logic {
        public void Foo() {
            var x = HeroTable.HP;
        }
    }
}
""")
    idx = await CodeIndexer().index_one(
        src, tmp_path,
        known_tables={"HeroTable"},
        known_fields={"HeroTable": {"HP"}},
    )
    foo = next((s for s in idx.symbols if s.name == "Foo"), None)
    assert foo is not None
    assert any(
        r.target_field == "HP" for r in foo.references
    ), "field ref should be attached to enclosing method Foo"


@pytest.mark.asyncio
async def test_relative_path_uses_forward_slash(tmp_path):
    sub = tmp_path / "sub" / "nested"
    sub.mkdir(parents=True)
    src = sub / "X.cs"
    src.write_text("// empty", encoding="utf-8")
    idx = await CodeIndexer().index_one(src, tmp_path)
    assert idx.source_path == "sub/nested/X.cs"
