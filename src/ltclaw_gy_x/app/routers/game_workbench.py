# -*- coding: utf-8 -*-
"""Game numeric workbench preview HTTP API endpoints."""
from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from ...app.agent_context import get_agent_for_request
from ...app.capabilities import require_capability
from ...app.workspace.workspace import Workspace
from ...game.change_proposal import ChangeOp, ChangeProposal
from ...game.dependency_resolver import get_dependency_graph_source_metadata
from ...game.workbench_suggest_context import (
    build_workbench_suggest_formal_context,
    build_workbench_suggest_prompt,
    validate_workbench_suggest_payload,
)
from ...game.workbench_source_write_service import (
    WorkbenchSourceWriteOp,
    WorkbenchSourceWriteService,
)


class PreviewChange(BaseModel):
    table: str
    row_id: str | int
    field: str
    new_value: Any = None


class PreviewRequest(BaseModel):
    changes: list[PreviewChange] = []


class SourceWriteRequest(BaseModel):
    ops: list[WorkbenchSourceWriteOp] = Field(default_factory=list)
    reason: str = Field(default="")


class ChatTurn(BaseModel):
    role: str
    content: str


class SuggestRequest(BaseModel):
    user_intent: str
    context_tables: list[str] = []
    current_pending: list[PreviewChange] = []
    chat_history: list[ChatTurn] = []


router = APIRouter(prefix="/game/workbench", tags=["game-workbench"])


def _impact_source_metadata() -> dict[str, Any]:
    return dict(get_dependency_graph_source_metadata())


def _service(workspace: Workspace):
    svc = workspace.service_manager.services.get("game_service")
    if svc is None:
        raise HTTPException(status_code=404, detail="Game service not available")
    return svc


def _change_applier(svc):
    applier = getattr(svc, "change_applier", None)
    if applier is None:
        raise HTTPException(status_code=412, detail="Change applier not available")
    return applier


def _project_root_or_none(game_service) -> Path | None:
    runtime_root = getattr(game_service, '_runtime_svn_root', None)
    if callable(runtime_root):
        root = runtime_root()
        if root is not None:
            return Path(root)
    user_config = getattr(game_service, 'user_config', None)
    local_root = getattr(user_config, 'svn_local_root', None)
    if local_root:
        return Path(local_root).expanduser()
    project_config = getattr(game_service, 'project_config', None)
    svn_config = getattr(project_config, 'svn', None)
    project_root = getattr(svn_config, 'root', None)
    if project_root and '://' not in str(project_root):
        return Path(project_root).expanduser()
    return None


def _make_key(change: PreviewChange) -> tuple[str, str, str]:
    return (change.table, str(change.row_id), change.field)


def _preview_key(preview: dict[str, Any]) -> tuple[str, str, str]:
    op = preview.get("op", {}) or {}
    return (
        str(op.get("table", "")),
        str(op.get("row_id", "")),
        str(op.get("field", "")),
    )


def _compute_reverse_impacts(
    svc: Any,
    targets: list[tuple[str, str | None]],
    max_depth: int = 3,
) -> list[dict[str, Any]]:
    """对一组 (table, field) 目标做反向影响 BFS, 返回扁平 impacts 列表。

    与 /game/index/impact 同语义: DependencyEdge(from→to) 表示 from 引用 to,
    所以 to 被改动时, from 是潜在下游。
    """
    committer = getattr(svc, "index_committer", None)
    if committer is None:
        return []
    try:
        dep = committer.load_dependency_graph()
    except Exception:  # noqa: BLE001
        dep = None
    if dep is None:
        return []

    by_to: dict[str, list[Any]] = {}
    for e in getattr(dep, "edges", []) or []:
        by_to.setdefault(e.to_table, []).append(e)

    seen: set[tuple[str, str, str, str]] = set()
    impacts: list[dict[str, Any]] = []
    source_metadata = _impact_source_metadata()

    for target_table, target_field in targets:
        queue: list[tuple[str, str | None, int]] = [(target_table, target_field, 0)]
        while queue:
            cur_table, cur_field, depth = queue.pop(0)
            if depth >= max_depth:
                continue
            for edge in by_to.get(cur_table, []):
                if cur_field is not None and edge.to_field != cur_field:
                    continue
                key = (target_table, str(target_field), edge.from_table, edge.from_field)
                if key in seen:
                    continue
                seen.add(key)
                conf = getattr(edge.confidence, "value", str(edge.confidence))
                impacts.append({
                    "source_table": target_table,
                    "source_field": target_field,
                    "from_table": edge.from_table,
                    "from_field": edge.from_field,
                    "to_table": edge.to_table,
                    "to_field": edge.to_field,
                    "confidence": conf,
                    "inferred_by": edge.inferred_by,
                    "depth": depth + 1,
                    "source_type": source_metadata["source_type"],
                    "semantic_role": source_metadata["semantic_role"],
                    "is_formal_map_relationship": source_metadata["is_formal_map_relationship"],
                })
                queue.append((edge.from_table, None, depth + 1))
    return impacts


@router.post("/preview")
async def preview_workbench_changes(
    body: PreviewRequest,
    workspace: Workspace = Depends(get_agent_for_request),
) -> dict[str, Any]:
    svc = _service(workspace)
    applier = _change_applier(svc)
    impact_source = _impact_source_metadata()

    if not body.changes:
        return {"items": [], "impacts": [], "affected_tables": [], "impacts_metadata": impact_source}

    proposal = ChangeProposal(
        title="__workbench_preview__",
        description="",
        ops=[
            ChangeOp(
                op="update_cell",
                table=c.table,
                row_id=c.row_id,
                field=c.field,
                new_value=c.new_value,
            )
            for c in body.changes
        ],
        status="approved",
    )

    try:
        previews = await applier.dry_run(proposal)
    except Exception as exc:
        message = str(exc) or exc.__class__.__name__
        return {
            "items": [
                {
                    "table": c.table,
                    "row_id": c.row_id,
                    "field": c.field,
                    "old_value": None,
                    "new_value": c.new_value,
                    "ok": False,
                    "error": message,
                }
                for c in body.changes
            ],
            "impacts": [],
            "affected_tables": [],
            "impacts_metadata": impact_source,
        }

    buckets: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for preview in previews:
        buckets.setdefault(_preview_key(preview), []).append(preview)

    items: list[dict[str, Any]] = []
    for index, change in enumerate(body.changes):
        bucket = buckets.get(_make_key(change))
        preview = bucket.pop(0) if bucket else (
            previews[index] if index < len(previews) else None
        )
        if preview is None:
            items.append(
                {
                    "table": change.table,
                    "row_id": change.row_id,
                    "field": change.field,
                    "old_value": None,
                    "new_value": change.new_value,
                    "ok": False,
                    "error": "missing dry-run result",
                }
            )
            continue
        items.append(
            {
                "table": change.table,
                "row_id": change.row_id,
                "field": change.field,
                "old_value": preview.get("before"),
                "new_value": change.new_value,
                "ok": bool(preview.get("ok")),
                "error": preview.get("reason"),
            }
        )

    # 反向影响: 仅对 ok 项的去重 (table, field) 目标做 BFS
    targets_seen: set[tuple[str, str]] = set()
    targets: list[tuple[str, str | None]] = []
    for it in items:
        if not it["ok"]:
            continue
        k = (it["table"], it["field"])
        if k in targets_seen:
            continue
        targets_seen.add(k)
        targets.append((it["table"], it["field"]))
    impacts = _compute_reverse_impacts(svc, targets) if targets else []
    affected_tables = sorted({i["from_table"] for i in impacts})

    return {
        "items": items,
        "impacts": impacts,
        "affected_tables": affected_tables,
        "impacts_metadata": impact_source,
    }


@router.post("/source-write")
async def write_workbench_changes_to_source(
    request: Request,
    body: SourceWriteRequest,
    workspace: Workspace = Depends(get_agent_for_request),
) -> dict[str, Any]:
    require_capability(request, "workbench.source.write")
    svc = _service(workspace)
    applier = _change_applier(svc)
    source_write_service = WorkbenchSourceWriteService(
        change_applier=applier,
        workspace_dir=getattr(workspace, "workspace_dir", getattr(applier, "svn_root", ".")),
        agent_id=(getattr(workspace, "agent_id", None) or getattr(request.state, "agent_id", "") or ""),
    )
    outcome = await source_write_service.write(ops=body.ops, reason=body.reason)
    if not outcome.ok:
        raise HTTPException(status_code=outcome.status_code, detail=outcome.payload)
    return outcome.payload


def _strip_json_fences(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s[3:]
        if s.endswith("```"):
            s = s[:-3]
    return s.strip()


def _to_plain(obj: Any) -> Any:
    """递归把 BaseModel / Enum / SimpleNamespace / 含 __dict__ 对象转为纯 dict/list/标量。

    用途: 让 _table_to_dict / _field_to_dict 在生产 (pydantic) 与测试 (SimpleNamespace)
    fixture 下统一行为。Enum / 类 enum (单 value 属性) 对象转为其字符串值。
    """
    import enum as _enum
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, _enum.Enum):
        return obj.value
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump(mode="json")
        except Exception:  # noqa: BLE001
            pass
    if isinstance(obj, dict):
        return {k: _to_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_plain(x) for x in obj]
    if hasattr(obj, "__dict__"):
        d = {k: v for k, v in vars(obj).items() if not k.startswith("_")}
        # enum-like 对象 (仅一个 value 属性) → 返回其 value
        if list(d.keys()) == ["value"]:
            return _to_plain(d["value"])
        return {k: _to_plain(v) for k, v in d.items()}
    return obj


def _table_to_dict(tinfo: Any) -> dict[str, Any]:
    out = _to_plain(tinfo)
    if isinstance(out, dict):
        return out
    return {}


def _field_to_dict(f: Any) -> dict[str, Any] | None:
    out = _to_plain(f)
    if isinstance(out, dict):
        return out
    return None


# 名称类列识别启发：用于行索引瘦身，避免向 LLM 发整张表
_NAME_KEYWORDS = (
    "name", "title", "label", "desc", "description",
    "名", "称", "标题", "描述",
)


def _is_name_like_header(header: str) -> bool:
    if not header:
        return False
    h = header.lower()
    return any(kw in h for kw in _NAME_KEYWORDS)


def _has_cjk(text: str) -> bool:
    for ch in text:
        c = ord(ch)
        if 0x4E00 <= c <= 0x9FFF or 0x3400 <= c <= 0x4DBF or 0x3040 <= c <= 0x30FF:
            return True
    return False


def _column_looks_like_name(rows: list[list[Any]], col: int, sample: int = 30) -> bool:
    """抽样判断该列是否像"名称类"列：含 CJK 或短英文标识。"""
    seen_non_empty = 0
    for row in rows:
        if col >= len(row):
            continue
        v = row[col]
        if v is None:
            continue
        s = str(v).strip()
        if not s:
            continue
        seen_non_empty += 1
        if seen_non_empty > sample:
            break
        # 纯数字列跳过
        try:
            float(s)
            continue
        except (TypeError, ValueError):
            pass
        if _has_cjk(s):
            return True
    return False


def _extract_query_terms(text: str) -> list[str]:
    """从用户问题里抽列匹配用的关键词：英文单词(3+) + 中文连续段(2+ 含 2-gram)。"""
    if not text:
        return []
    s = text.lower()
    out: list[str] = []
    for m in re.finditer(r"[a-z][a-z0-9_]{2,}", s):
        out.append(m.group(0))
    for m in re.finditer(r"[\u4e00-\u9fff\u3400-\u4dbf]{2,}", s):
        run = m.group(0)
        out.append(run)
        if len(run) >= 3:
            for i in range(len(run) - 1):
                out.append(run[i : i + 2])
    seen: set[str] = set()
    res: list[str] = []
    for t in out:
        if t and t not in seen:
            seen.add(t)
            res.append(t)
    return res


def _match_relevant_columns(
    headers: list[str],
    fields_meta: list[dict[str, Any]],
    terms: list[str],
    limit: int = 6,
) -> list[str]:
    """根据问题关键词命中表头名 / 字段描述, 返回相关列名(保持表头顺序)。"""
    if not terms or not headers:
        return []
    desc_by_name: dict[str, str] = {}
    for f in fields_meta:
        n = (f.get("name") or "").strip().lower()
        if n:
            desc_by_name[n] = str(f.get("desc") or "").lower()
    matched: list[str] = []
    for h in headers:
        if not h:
            continue
        hl = h.lower()
        d = desc_by_name.get(hl, "")
        hit = False
        for t in terms:
            if not t:
                continue
            if t in hl or (len(hl) >= 2 and hl in t):
                hit = True
                break
            if d and t in d:
                hit = True
                break
        if hit:
            matched.append(h)
            if len(matched) >= limit:
                break
    return matched


def _build_row_index(
    headers: list[str],
    rows: list[list[Any]],
    primary_key: str | None,
    extra_columns: list[str] | None = None,
) -> tuple[list[str], list[dict[str, Any]]]:
    """从原始行抽出 primary_key + 名称类列 + 关键词命中列, 形成精简行索引。

    返回 (selected_headers, rows[dict])。
    """
    if not headers:
        return [], []
    pk_lower = (primary_key or "").lower()
    selected_idx: list[int] = []
    selected_headers: list[str] = []
    seen: set[int] = set()
    # 1) primary_key（大小写不敏感; 兼容 ID 默认值）
    for i, h in enumerate(headers):
        if h and h.lower() == pk_lower and i not in seen:
            selected_idx.append(i)
            selected_headers.append(h)
            seen.add(i)
            break
    if not selected_idx:
        selected_idx.append(0)
        selected_headers.append(headers[0] if headers else "id")
        seen.add(0)

    name_cap = 4  # PK 之外最多 4 个名称类列
    name_added = 0
    # 2) 表头关键词命中的列
    for i, h in enumerate(headers):
        if i in seen:
            continue
        if _is_name_like_header(h):
            selected_idx.append(i)
            selected_headers.append(h)
            seen.add(i)
            name_added += 1
            if name_added >= name_cap:
                break
    # 3) 兜底：内容含 CJK 的列（覆盖像 "Column_1" 这种实际中文名列）
    if name_added < name_cap:
        for i, h in enumerate(headers):
            if i in seen:
                continue
            if _column_looks_like_name(rows, i):
                selected_idx.append(i)
                selected_headers.append(h)
                seen.add(i)
                name_added += 1
                if name_added >= name_cap:
                    break

    # 4) 用户问题关键词命中的额外列(P0-3 列召回)
    if extra_columns:
        wanted_lower = {c.lower() for c in extra_columns if c}
        for i, h in enumerate(headers):
            if i in seen:
                continue
            if h and h.lower() in wanted_lower:
                selected_idx.append(i)
                selected_headers.append(h)
                seen.add(i)

    out: list[dict[str, Any]] = []
    for row in rows:
        rec: dict[str, Any] = {}
        for col, h in zip(selected_idx, selected_headers):
            if col < len(row):
                v = row[col]
                if isinstance(v, str) and len(v) > 60:
                    v = v[:60] + "…"
                rec[h] = v
        out.append(rec)
    return selected_headers, out


@router.post("/suggest")
async def suggest_workbench_changes(
    request: Request,
    body: SuggestRequest,
    workspace: Workspace = Depends(get_agent_for_request),
) -> dict[str, Any]:
    """Ask the active LLM to suggest concrete field changes for the given intent."""
    import json as _json
    import logging

    logger = logging.getLogger(__name__)

    require_capability(request, "workbench.read")
    require_capability(request, "knowledge.read")

    svc = _service(workspace)
    intent = (body.user_intent or "").strip()
    if not intent:
        raise HTTPException(status_code=400, detail="user_intent is required")

    query_terms = _extract_query_terms(intent)

    tables_meta: list[dict[str, Any]] = []
    related_meta: list[dict[str, Any]] = []
    related_seen: set[str] = set()
    qr = getattr(svc, "query_router", None)
    applier = getattr(svc, "change_applier", None)
    main_tables: set[str] = set(body.context_tables[:8])

    if qr is not None:
        for tname in body.context_tables[:8]:
            try:
                tinfo = await qr.get_table(tname)
            except Exception:
                tinfo = None
            if not tinfo:
                continue
            tdata = _table_to_dict(tinfo)
            primary_key = tdata.get("primary_key") or "ID"
            ai_summary = tdata.get("ai_summary") or ""
            fields_raw = tdata.get("fields") or []
            fields_dump: list[dict[str, Any]] = []
            for f in fields_raw[:80]:
                fd = _field_to_dict(f)
                if fd is None:
                    continue
                fields_dump.append({
                    "name": fd.get("name"),
                    "type": fd.get("type"),
                    "desc": fd.get("desc") or fd.get("description") or "",
                })

            row_index_headers: list[str] = []
            row_index: list[dict[str, Any]] = []
            sample_total = 0
            matched_cols: list[str] = []
            # 一次性读全表(已按表头/注释行裁剪), 仅向 LLM 暴露 PK + 名称列 + 命中列
            if applier is not None:
                try:
                    page = await asyncio.to_thread(
                        applier.read_rows, tname, 0, 5000
                    )
                    headers = page.get("headers") or []
                    rows = page.get("rows") or []
                    sample_total = page.get("total") or len(rows)
                    matched_cols = _match_relevant_columns(
                        headers, fields_dump, query_terms
                    )
                    # P0-3+: 大表先按 query_terms 命中行预过滤, 再做行索引裁剪,
                    # 避免被 5000 / 1500 截断误伤目标行。
                    if rows and query_terms:
                        terms_lower = [t.lower() for t in query_terms if t]
                        # 优先扫描 PK + 命中列, 退化时全行扫描
                        scan_idx: list[int] = []
                        if primary_key:
                            for i, h in enumerate(headers):
                                if h and h.lower() == primary_key.lower():
                                    scan_idx.append(i)
                                    break
                        for h in matched_cols:
                            try:
                                scan_idx.append(headers.index(h))
                            except ValueError:
                                pass
                        scan_idx = list(dict.fromkeys(scan_idx))
                        hits: list[list[Any]] = []
                        misses: list[list[Any]] = []
                        for r in rows:
                            cells = (
                                [r[i] for i in scan_idx if i < len(r)]
                                if scan_idx
                                else r
                            )
                            blob = " ".join(
                                str(c) for c in cells if c is not None
                            ).lower()
                            if any(t in blob for t in terms_lower):
                                hits.append(r)
                            else:
                                misses.append(r)
                        # 命中行优先, 不足额时再用未命中行兜底, 总数封顶 1500
                        cap = 1500
                        if len(hits) >= cap:
                            rows = hits[:cap]
                        else:
                            rows = hits + misses[: cap - len(hits)]
                    row_index_headers, row_index = _build_row_index(
                        headers, rows, primary_key, extra_columns=matched_cols
                    )
                    if len(row_index) > 1500:
                        row_index = row_index[:1500]
                except Exception as _exc:
                    logger.warning("read_rows failed for %s: %s", tname, _exc)

            tables_meta.append({
                "table": tname,
                "primary_key": primary_key,
                "ai_summary": ai_summary,
                "fields": fields_dump,
                "row_index_columns": row_index_headers,
                "matched_columns": matched_cols,
                "row_index_total": sample_total,
                "row_index": row_index,
            })

            # P0-2: 跨表联查 - 顺着 dependency_graph 把直接相关表的 schema 带进来(不带行)
            try:
                dep = await qr.dependencies_of(tname)
            except Exception:
                dep = None
            if isinstance(dep, dict):
                for direction in ("upstream", "downstream"):
                    for edge in (dep.get(direction) or [])[:6]:
                        rt = (edge or {}).get("table")
                        if not rt or rt in main_tables or rt in related_seen:
                            continue
                        related_seen.add(rt)
                        try:
                            r_tinfo = await qr.get_table(rt)
                        except Exception:
                            r_tinfo = None
                        if not r_tinfo:
                            continue
                        r_data = _table_to_dict(r_tinfo)
                        r_fields_raw = r_data.get("fields") or []
                        r_fields_dump: list[dict[str, Any]] = []
                        for f in r_fields_raw[:40]:
                            fd = _field_to_dict(f)
                            if fd is None:
                                continue
                            r_fields_dump.append({
                                "name": fd.get("name"),
                                "type": fd.get("type"),
                                "desc": fd.get("desc")
                                or fd.get("description")
                                or "",
                            })
                        related_meta.append({
                            "table": rt,
                            "primary_key": r_data.get("primary_key") or "ID",
                            "ai_summary": r_data.get("ai_summary") or "",
                            "fields": r_fields_dump,
                            "via": {
                                "from_table": tname,
                                "direction": direction,
                                "field": edge.get("field"),
                                "target_field": edge.get("target_field")
                                or edge.get("source_field"),
                                "confidence": edge.get("confidence"),
                            },
                        })
                        if len(related_meta) >= 8:
                            break
                    if len(related_meta) >= 8:
                        break

    pending_dump = [
        {
            "table": p.table,
            "row_id": p.row_id,
            "field": p.field,
            "new_value": p.new_value,
        }
        for p in body.current_pending
    ]
    formal_context = build_workbench_suggest_formal_context(
        _project_root_or_none(svc),
        intent,
    )

    # 多轮上下文(P0-5 顺手做): 取最近 6 轮
    history_dump: list[dict[str, str]] = []
    for turn in (body.chat_history or [])[-6:]:
        role = (turn.role or "").strip().lower()
        if role not in ("user", "assistant"):
            continue
        content = (turn.content or "").strip()
        if not content:
            continue
        if len(content) > 600:
            content = content[:600] + "…"
        history_dump.append({"role": role, "content": content})

    prompt = build_workbench_suggest_prompt(
        user_intent=intent,
        tables_meta=tables_meta,
        related_meta=related_meta,
        chat_history=history_dump,
        draft_overlay=pending_dump,
        formal_context=formal_context,
    )

    router_obj = svc._model_router() if hasattr(svc, "_model_router") else None
    if router_obj is None or not hasattr(router_obj, "call_model_result"):
        raise HTTPException(status_code=412, detail="No active model router")

    result = await router_obj.call_model_result(prompt, model_type="workbench_suggest")
    if not result.ok:
        logger.warning("game_workbench.suggest unified model router failed: %s", result)
        raise HTTPException(status_code=502, detail={"error_code": result.error_code, "message": result.message})

    raw = (result.text or "").strip()

    parsed: dict[str, Any] | None = None
    try:
        parsed = _json.loads(_strip_json_fences(raw))
    except Exception:
        try:
            i, j = raw.find("{"), raw.rfind("}")
            if i >= 0 and j > i:
                parsed = _json.loads(raw[i : j + 1])
        except Exception:
            parsed = None

    if not isinstance(parsed, dict):
        logger.warning("game_workbench.suggest returned invalid JSON payload: %r", raw[:400])
        raise HTTPException(
            status_code=502,
            detail={
                "error_code": "invalid_model_output",
                "message": "Workbench suggest model returned invalid JSON.",
                "raw": raw,
            },
        )

    validated = validate_workbench_suggest_payload(
        parsed,
        tables_meta=tables_meta,
        formal_context=formal_context,
        draft_overlay=pending_dump,
    )

    return {
        "message": validated["message"],
        "changes": validated["changes"],
        "evidence_refs": validated["evidence_refs"],
        "formal_context_status": validated["formal_context_status"],
        "context_summary": {
            "main_tables": [m.get("table") for m in tables_meta],
            "related_tables": [m.get("table") for m in related_meta],
            "matched_columns": {
                m.get("table"): m.get("matched_columns") or []
                for m in tables_meta
            },
            "query_terms": query_terms,
        },
    }


# ---------------------------------------------------------------------------
# AI Suggestion Panel (rule-based, no LLM)
# ---------------------------------------------------------------------------

def _quantile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    pos = q * (len(sorted_vals) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return float(sorted_vals[lo]) * (1 - frac) + float(sorted_vals[hi]) * frac


def _coerce_float(v: Any) -> float | None:
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _pk_int(v: Any) -> int | None:
    if isinstance(v, int) and not isinstance(v, bool):
        return v
    if isinstance(v, float):
        return int(v) if v.is_integer() else None
    if isinstance(v, str):
        s = v.strip()
        if s.isdigit():
            return int(s)
    return None


@router.get("/ai-suggest")
async def ai_suggest_panel(
    table: str,
    field: str | None = None,
    workspace: Workspace = Depends(get_agent_for_request),
) -> dict[str, Any]:
    """Return rule-based structured AI hints for a target table/field.

    Frontend AISuggestionPanel uses this to render:
      - available_id / id_ranges       (from TableIndex.id_ranges + actual rows)
      - reference_values (numeric)     (min/p25/p50/p75/max/avg + samples)
      - suggested_range                (p25..p75 if numeric)
      - reusable_resources             (foreign-key candidates from dep graph)
      - pending_confirms               (fields with confidence != confirmed)

    No LLM call is performed. Designed to be cheap (<50ms) and deterministic.
    """
    svc = _service(workspace)
    committer = getattr(svc, "index_committer", None)
    if committer is None:
        raise HTTPException(status_code=412, detail="Index committer not available")

    tables = committer.load_table_indexes() or []
    target = next(
        (t for t in tables if (getattr(t, "table_name", None) or "") == table),
        None,
    )
    if target is None:
        raise HTTPException(status_code=404, detail=f"Table '{table}' not found")

    target_dict = _table_to_dict(target)
    fields_meta = [_field_to_dict(f) for f in target_dict.get("fields", []) or []]
    fields_meta = [f for f in fields_meta if f]

    # ---- 1. id_ranges + 下一个可用 ID -----------------------------------
    available_ids: list[dict[str, Any]] = []
    used_ids: set[int] = set()
    applier = getattr(svc, "change_applier", None)
    primary_key = target_dict.get("primary_key") or "ID"
    if applier is not None:
        try:
            data = await asyncio.to_thread(applier.read_rows, table, 0, 5000)
        except Exception:
            data = {"headers": [], "rows": []}
        headers = data.get("headers", []) or []
        rows = data.get("rows", []) or []
        pk_idx = 0
        for i, h in enumerate(headers):
            if h and str(h).lower() == str(primary_key).lower():
                pk_idx = i
                break
        for r in rows:
            if pk_idx < len(r):
                pk_int = _pk_int(r[pk_idx])
                if pk_int is not None:
                    used_ids.add(pk_int)

    for rng in target_dict.get("id_ranges", []) or []:
        try:
            start = int(rng.get("start"))
            end = int(rng.get("end"))
        except (TypeError, ValueError):
            continue
        # 找该段内第一个未占用的 id（从 actual_max+1 起，回退到 start）
        actual_max = rng.get("actual_max")
        next_id: int | None = None
        if isinstance(actual_max, int) and start <= actual_max < end:
            cand = actual_max + 1
            while cand <= end:
                if cand not in used_ids:
                    next_id = cand
                    break
                cand += 1
        if next_id is None:
            for cand in range(start, end + 1):
                if cand not in used_ids:
                    next_id = cand
                    break
        available_ids.append({
            "type": rng.get("type"),
            "start": start,
            "end": end,
            "actual_min": rng.get("actual_min"),
            "actual_max": actual_max,
            "used_count": rng.get("count", 0),
            "next_available": next_id,
            "remaining": (end - start + 1) - int(rng.get("count") or 0),
        })

    # ---- 2. 数值字段：分位数 + 建议区间 + 抽样 --------------------------
    numeric_stats: dict[str, Any] | None = None
    suggested_range: list[float] | None = None
    samples: list[dict[str, Any]] = []
    if field and applier is not None:
        try:
            data = await asyncio.to_thread(applier.read_rows, table, 0, 5000)
        except Exception:
            data = {"headers": [], "rows": []}
        headers = data.get("headers", []) or []
        rows = data.get("rows", []) or []
        col_idx = -1
        for i, h in enumerate(headers):
            if h and str(h) == field:
                col_idx = i
                break
        if col_idx >= 0:
            vals: list[float] = []
            pk_idx = 0
            name_idx = -1
            for i, h in enumerate(headers):
                if h and str(h).lower() == str(primary_key).lower():
                    pk_idx = i
                if name_idx < 0 and _is_name_like_header(str(h or "")):
                    name_idx = i
            for r in rows:
                if col_idx < len(r):
                    fv = _coerce_float(r[col_idx])
                    if fv is not None:
                        vals.append(fv)
            if vals:
                vs = sorted(vals)
                p25 = _quantile(vs, 0.25)
                p50 = _quantile(vs, 0.50)
                p75 = _quantile(vs, 0.75)
                avg = sum(vs) / len(vs)
                numeric_stats = {
                    "count": len(vs),
                    "min": vs[0],
                    "max": vs[-1],
                    "avg": round(avg, 4),
                    "p25": p25,
                    "p50": p50,
                    "p75": p75,
                }
                suggested_range = [p25, p75]
                # 取靠近 p50 的若干样本（最多 5 条）
                with_dist = sorted(
                    enumerate(vals),
                    key=lambda kv: abs(kv[1] - p50),
                )[:5]
                for idx, v in with_dist:
                    if idx < len(rows):
                        row = rows[idx]
                        rec: dict[str, Any] = {
                            "id": row[pk_idx] if pk_idx < len(row) else None,
                            "value": v,
                        }
                        if name_idx >= 0 and name_idx < len(row):
                            rec["name"] = row[name_idx]
                        samples.append(rec)

    # ---- 3. 反向依赖：哪些表/字段引用本表 -------------------------------
    reusable_resources: list[dict[str, Any]] = []
    try:
        dep = committer.load_dependency_graph()
    except Exception:
        dep = None
    if dep is not None:
        for edge in getattr(dep, "edges", []) or []:
            try:
                if edge.to_table == table:
                    reusable_resources.append({
                        "from_table": edge.from_table,
                        "from_field": edge.from_field,
                        "to_field": edge.to_field,
                        "confidence": getattr(edge.confidence, "value", str(edge.confidence)),
                        "inferred_by": edge.inferred_by,
                    })
            except Exception:
                continue

    # ---- 4. 待确认 Checklist -------------------------------------------
    pending_confirms: list[dict[str, Any]] = []
    for f in fields_meta:
        conf = (f.get("confidence") or "").lower()
        if conf and conf != "confirmed":
            pending_confirms.append({
                "name": f.get("name"),
                "type": f.get("type"),
                "confidence": conf,
                "description": f.get("description") or "",
            })

    # ---- 5. 当前 field 元信息 ------------------------------------------
    field_meta: dict[str, Any] | None = None
    if field:
        for f in fields_meta:
            if f.get("name") == field:
                field_meta = {
                    "name": f.get("name"),
                    "type": f.get("type"),
                    "confidence": f.get("confidence"),
                    "description": f.get("description") or "",
                }
                break

    return {
        "table": table,
        "field": field,
        "field_meta": field_meta,
        "primary_key": primary_key,
        "available_ids": available_ids,
        "numeric_stats": numeric_stats,
        "suggested_range": suggested_range,
        "samples": samples,
        "reusable_resources": reusable_resources[:20],
        "pending_confirms": pending_confirms,
        "summary": _build_panel_summary(
            target_dict, available_ids, numeric_stats, len(reusable_resources),
            len(pending_confirms),
        ),
    }


def _build_panel_summary(
    target: dict[str, Any],
    avail: list[dict[str, Any]],
    stats: dict[str, Any] | None,
    ref_count: int,
    pending_count: int,
) -> str:
    parts: list[str] = []
    parts.append(f"表 {target.get('table_name')}: {target.get('row_count', 0)} 行")
    if avail:
        free = [a for a in avail if a.get("next_available") is not None]
        if free:
            parts.append(
                f"可分配 ID: " + ", ".join(
                    f"{a['type']}:{a['next_available']}" for a in free[:3]
                )
            )
    if stats:
        parts.append(
            f"建议区间 {stats['p25']:g}~{stats['p75']:g} (中位 {stats['p50']:g})"
        )
    if ref_count:
        parts.append(f"被 {ref_count} 处引用")
    if pending_count:
        parts.append(f"{pending_count} 字段待确认")
    return " · ".join(parts)


# ──────────────────────── /context endpoint ─────────────────────────


class WorkbenchContextField(BaseModel):
    key: str
    label: str
    type: str = ""
    description: str = ""


class WorkbenchContextRecord(BaseModel):
    id: Any
    fields: list[dict[str, Any]] = Field(default_factory=list)


class WorkbenchContextTable(BaseModel):
    tableId: str
    tableName: str
    system: str | None = None
    primaryKey: str = "ID"
    fields: list[WorkbenchContextField] = Field(default_factory=list)
    records: list[WorkbenchContextRecord] = Field(default_factory=list)
    rowCount: int = 0


class WorkbenchContextResponse(BaseModel):
    tables: list[WorkbenchContextTable] = Field(default_factory=list)
    focusField: dict[str, str] | None = None


@router.get("/context", response_model=WorkbenchContextResponse)
async def get_workbench_context(
    table_ids: list[str] = Query(default_factory=list, alias="tableIds"),
    focus_table: str | None = Query(default=None, alias="focusTable"),
    focus_field: str | None = Query(default=None, alias="focusField"),
    limit_per_table: int = Query(default=50, ge=1, le=500, alias="limitPerTable"),
    workspace: Workspace = Depends(get_agent_for_request),
) -> WorkbenchContextResponse:
    """Multi-table workbench context bundle: schema + first N records per table."""
    svc = _service(workspace)
    qr = getattr(svc, "query_router", None)
    applier = getattr(svc, "change_applier", None)
    if qr is None or applier is None:
        raise HTTPException(
            status_code=412,
            detail="Query router or change applier not available",
        )

    tables_out: list[WorkbenchContextTable] = []
    for tid in table_ids:
        try:
            tinfo = await qr.get_table(tid)
        except Exception:  # noqa: BLE001
            tinfo = None
        if tinfo is None:
            continue

        fields_meta = getattr(tinfo, "fields", []) or []
        fields_out = [
            WorkbenchContextField(
                key=getattr(f, "name", ""),
                label=getattr(f, "name", ""),
                type=getattr(f, "type", "") or "",
                description=getattr(f, "description", "") or "",
            )
            for f in fields_meta
            if getattr(f, "name", None)
        ]
        primary_key = getattr(tinfo, "primary_key", "ID") or "ID"

        # 读取行（read_rows 是同步,需 to_thread）
        try:
            data = await asyncio.to_thread(
                applier.read_rows, tid, 0, limit_per_table,
            )
        except Exception:  # noqa: BLE001
            data = {"headers": [], "rows": [], "total": 0}
        headers: list[str] = data.get("headers", []) or []
        raw_rows: list[list[Any]] = data.get("rows", []) or []

        records_out: list[WorkbenchContextRecord] = []
        pk_idx = headers.index(primary_key) if primary_key in headers else None
        for i, row in enumerate(raw_rows):
            row_id: Any
            if pk_idx is not None and pk_idx < len(row):
                row_id = row[pk_idx]
            else:
                row_id = i + 1
            field_values = [
                {"key": headers[j] if j < len(headers) else f"col_{j}", "value": v}
                for j, v in enumerate(row)
            ]
            records_out.append(WorkbenchContextRecord(id=row_id, fields=field_values))

        tables_out.append(WorkbenchContextTable(
            tableId=tid,
            tableName=getattr(tinfo, "table_name", tid),
            system=getattr(tinfo, "system", None),
            primaryKey=primary_key,
            fields=fields_out,
            records=records_out,
            rowCount=int(getattr(tinfo, "row_count", len(raw_rows)) or len(raw_rows)),
        ))

    focus_payload: dict[str, str] | None = None
    if focus_table and focus_field:
        focus_payload = {"table": focus_table, "field": focus_field}

    return WorkbenchContextResponse(tables=tables_out, focusField=focus_payload)


# ─────────────────── /damage-chain endpoint (Phase-1 stub) ───────────────────


class DamageVariable(BaseModel):
    name: str
    value: float
    sourceTable: str = ""
    isChanged: bool = False


class DamageChainModel(BaseModel):
    formula: str
    variables: list[DamageVariable] = Field(default_factory=list)
    resultBefore: float = 0.0
    resultAfter: float = 0.0
    deltaPercent: float = 0.0


class DamageChainRequest(BaseModel):
    formulaKey: str = "default"
    changes: list[PreviewChange] = Field(default_factory=list)


@router.post("/damage-chain", response_model=DamageChainModel)
async def compute_damage_chain(
    body: DamageChainRequest,
    workspace: Workspace = Depends(get_agent_for_request),
) -> DamageChainModel:
    """Phase-1 stub: deterministic damage-chain projection.

    替换为真正的公式引擎之前, 暂用固定模板:
    `Result = ATK * DamageCoeff * (1 - DefenseRatio)`
    其中 ATK/DamageCoeff/DefenseRatio 可被 changes[] 中同名 field 覆盖。
    """
    if body.formulaKey != "default":
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported formulaKey: {body.formulaKey}",
        )

    # 默认变量
    defaults: dict[str, dict[str, Any]] = {
        "ATK": {"value": 100.0, "sourceTable": "HeroTable"},
        "DamageCoeff": {"value": 1.0, "sourceTable": "SkillTable"},
        "DefenseRatio": {"value": 0.3, "sourceTable": "EnemyTable"},
    }

    # 用 changes 覆盖
    overrides: dict[str, tuple[float, str]] = {}
    for ch in body.changes:
        if ch.field in defaults:
            try:
                v = float(ch.new_value) if ch.new_value is not None else None
            except (TypeError, ValueError):
                v = None
            if v is not None:
                overrides[ch.field] = (v, ch.table or defaults[ch.field]["sourceTable"])

    variables: list[DamageVariable] = []
    after_vals: dict[str, float] = {}
    before_vals: dict[str, float] = {}
    for name, meta in defaults.items():
        before_v = float(meta["value"])
        if name in overrides:
            after_v, src = overrides[name]
            variables.append(DamageVariable(
                name=name, value=after_v, sourceTable=src, isChanged=True,
            ))
        else:
            after_v = before_v
            variables.append(DamageVariable(
                name=name, value=before_v, sourceTable=meta["sourceTable"],
                isChanged=False,
            ))
        before_vals[name] = before_v
        after_vals[name] = after_v

    formula = "ATK * DamageCoeff * (1 - DefenseRatio)"
    result_before = before_vals["ATK"] * before_vals["DamageCoeff"] * (
        1 - before_vals["DefenseRatio"]
    )
    result_after = after_vals["ATK"] * after_vals["DamageCoeff"] * (
        1 - after_vals["DefenseRatio"]
    )
    delta_pct = (
        (result_after - result_before) / result_before * 100.0
        if result_before != 0 else 0.0
    )

    return DamageChainModel(
        formula=formula,
        variables=variables,
        resultBefore=round(result_before, 4),
        resultAfter=round(result_after, 4),
        deltaPercent=round(delta_pct, 2),
    )
