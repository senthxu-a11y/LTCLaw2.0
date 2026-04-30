"""历史归档器: 比较前后 TableIndex 快照，按阈值生成历史条目并写 jsonl。

阈值（spec §5）：满足任一即记录变更：
- 字段增删（fields name 集合变化）
- 行数变化 ≥ 1
- ai_summary 变化 (字段值变化代理：T5 P0 简化为 ai_summary 不同；
  完整字段值 5% 变化在没有原表数据快照时无法精确判断)
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

from .models import TableIndex

logger = logging.getLogger(__name__)


@dataclass
class HistoryEntry:
    table_name: str
    timestamp: str
    revision_before: int
    revision_after: int
    changes: List[str] = field(default_factory=list)
    fields_added: List[str] = field(default_factory=list)
    fields_removed: List[str] = field(default_factory=list)
    row_count_before: int = 0
    row_count_after: int = 0
    summary_changed: bool = False

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def _field_names(t: TableIndex) -> set:
    out = set()
    for f in (t.fields or []):
        name = getattr(f, "name", None)
        if name is None and isinstance(f, dict):
            name = f.get("name")
        if name:
            out.add(name)
    return out


def record_change(before: Optional[TableIndex], after: TableIndex) -> Optional[HistoryEntry]:
    """对比两个快照；满足阈值返回 HistoryEntry，否则 None。"""
    after_fields = _field_names(after)
    before_fields = _field_names(before) if before is not None else set()
    added = sorted(after_fields - before_fields)
    removed = sorted(before_fields - after_fields)
    rc_before = before.row_count if before is not None else 0
    rc_after = after.row_count
    summary_changed = bool(before is not None and (before.ai_summary or "") != (after.ai_summary or ""))
    row_delta = abs(rc_after - rc_before)

    triggers: List[str] = []
    if before is None:
        triggers.append("created")
    if added:
        triggers.append("fields_added")
    if removed:
        triggers.append("fields_removed")
    if before is not None and row_delta >= 1:
        triggers.append("row_count_delta")
    if summary_changed:
        triggers.append("summary_changed")

    if not triggers:
        return None

    return HistoryEntry(
        table_name=after.table_name,
        timestamp=datetime.now().isoformat(),
        revision_before=before.svn_revision if before is not None else 0,
        revision_after=after.svn_revision,
        changes=triggers,
        fields_added=added,
        fields_removed=removed,
        row_count_before=rc_before,
        row_count_after=rc_after,
        summary_changed=summary_changed,
    )


def append_entry(history_dir: Path, entry: HistoryEntry, day: Optional[datetime] = None) -> Path:
    """追加 entry 到 history/<TableName>/<YYYY-MM-DD>.jsonl，返回写入的文件路径。"""
    day = day or datetime.now()
    table_dir = history_dir / entry.table_name
    table_dir.mkdir(parents=True, exist_ok=True)
    target = table_dir / f"{day.strftime('%Y-%m-%d')}.jsonl"
    with target.open("a", encoding="utf-8") as fp:
        fp.write(entry.to_json() + "\n")
    return target


def diff_and_archive(
    before_tables: Iterable[TableIndex],
    after_tables: Iterable[TableIndex],
    history_dir: Path,
) -> List[HistoryEntry]:
    """批量比对前后两组 TableIndex，写出所有触发阈值的 HistoryEntry。"""
    by_name_before = {t.table_name: t for t in before_tables}
    written: List[HistoryEntry] = []
    for after in after_tables:
        entry = record_change(by_name_before.get(after.table_name), after)
        if entry is not None:
            try:
                append_entry(history_dir, entry)
                written.append(entry)
            except Exception as e:
                logger.warning(f"写入历史条目失败 ({entry.table_name}): {e}")
    return written


def flush_daily(history_dir: Path, days_to_keep: int = 30, now: Optional[datetime] = None) -> int:
    """把 days_to_keep 天前的明细 jsonl 聚合到 weekly/<YYYY-WW>.json，返回处理的明细文件数。"""
    if not history_dir.exists():
        return 0
    now = now or datetime.now()
    cutoff = now.timestamp() - days_to_keep * 86400
    weekly_dir = history_dir / "weekly"
    weekly_dir.mkdir(parents=True, exist_ok=True)
    processed = 0
    for table_dir in history_dir.iterdir():
        if not table_dir.is_dir() or table_dir.name == "weekly" or table_dir.name == "milestone":
            continue
        for jf in list(table_dir.glob("*.jsonl")):
            try:
                day_str = jf.stem
                day_ts = datetime.strptime(day_str, "%Y-%m-%d").timestamp()
            except ValueError:
                continue
            if day_ts >= cutoff:
                continue
            try:
                day_dt = datetime.strptime(day_str, "%Y-%m-%d")
                iso_year, iso_week, _ = day_dt.isocalendar()
                weekly_file = weekly_dir / f"{iso_year}-W{iso_week:02d}.json"
                bucket = []
                if weekly_file.exists():
                    try:
                        bucket = json.loads(weekly_file.read_text(encoding="utf-8"))
                    except Exception:
                        bucket = []
                for line in jf.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        bucket.append(json.loads(line))
                    except Exception:
                        continue
                weekly_file.write_text(json.dumps(bucket, ensure_ascii=False, indent=2), encoding="utf-8")
                jf.unlink()
                processed += 1
            except Exception as e:
                logger.warning(f"聚合 {jf} 失败: {e}")
    return processed


def flush_weekly_to_milestone(history_dir: Path, milestone_tags: Iterable[str]) -> int:
    """把 weekly/*.json 中匹配 milestone_tags 的归到 milestone/，永久保留。返回搬运文件数。"""
    weekly_dir = history_dir / "weekly"
    if not weekly_dir.exists():
        return 0
    milestone_dir = history_dir / "milestone"
    milestone_dir.mkdir(parents=True, exist_ok=True)
    tags = set(milestone_tags or [])
    moved = 0
    for wf in list(weekly_dir.glob("*.json")):
        if not tags or wf.stem in tags:
            target = milestone_dir / wf.name
            try:
                wf.replace(target)
                moved += 1
            except Exception as e:
                logger.warning(f"搬运里程碑 {wf} 失败: {e}")
    return moved
