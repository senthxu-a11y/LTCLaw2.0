# -*- coding: utf-8 -*-
"""C# (.cs) code indexer — regex.v1.

正则驱动的轻量 C# 解析器：抽取命名空间、using、类/接口/结构/枚举、方法、字段/属性，
并基于已知的表/字段集合反向定位代码中对策划数据的引用。

不依赖 Roslyn / 任何 .NET SDK；适用于策划工作台 P2 reverse-impact 场景。
"""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import Iterable, Mapping, Optional

from .models import CodeFileIndex, CodeSymbol, CodeSymbolReference

logger = logging.getLogger(__name__)


# ─────────────────────────── 编译期正则 ────────────────────────────
_RE_USING = re.compile(r"\busing\s+([A-Za-z0-9_.]+)\s*;")
_RE_NAMESPACE = re.compile(r"\bnamespace\s+([A-Za-z0-9_.]+)")

# 类/接口/结构体/枚举：行级匹配，捕获 kind + name
_RE_TYPE = re.compile(
    r"^\s*(?:public|internal|private|protected|sealed|static|abstract|partial|\s)*"
    r"\s*(class|interface|struct|enum)\s+(\w+)"
)

# 方法（忽略以 // 开头的注释行；要求行末有 { 或 ; 或紧随其后的 {）
_RE_METHOD = re.compile(
    r"^\s*(?:public|private|protected|internal|static|virtual|override|async|sealed|\s)+"
    r"\s+([A-Za-z0-9_<>,\s\[\]]+?)\s+(\w+)\s*\(([^)]*)\)\s*(?:where[^{}]*)?\s*\{?\s*$"
)

# 字段/属性
_RE_FIELD = re.compile(
    r"^\s*(?:public|private|protected|internal|static|readonly|const|\s)+"
    r"\s+([A-Za-z0-9_<>,\[\]]+)\s+(\w+)\s*[=;{]"
)

# 文档注释 /// <summary>...</summary>
_RE_SUMMARY_INLINE = re.compile(r"<summary>(.*?)</summary>", re.IGNORECASE | re.DOTALL)


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _trim(line: str, max_len: int = 80) -> str:
    s = line.strip()
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s


def _summary_from_doc_above(lines: list[str], idx: int) -> str:
    """从目标行上方的 /// XML 注释或 // 注释提取摘要（向上最多扫 5 行）。"""
    summary_parts: list[str] = []
    i = idx - 1
    scanned = 0
    while i >= 0 and scanned < 5:
        raw = lines[i].strip()
        if not raw:
            break
        if raw.startswith("///"):
            text = raw[3:].strip()
            if text:
                summary_parts.append(text)
        elif raw.startswith("//"):
            text = raw[2:].strip()
            if text:
                summary_parts.append(text)
        else:
            break
        i -= 1
        scanned += 1
    if not summary_parts:
        return ""
    summary_parts.reverse()
    joined = " ".join(summary_parts)
    # 提取 <summary>...</summary> 内容
    m = _RE_SUMMARY_INLINE.search(joined)
    if m:
        return m.group(1).strip()
    # 去掉多余 XML 标签
    cleaned = re.sub(r"<[^>]+>", "", joined).strip()
    return cleaned[:200]


class CodeIndexer:
    """正则版 .cs 索引器（regex.v1）"""

    async def index_one(
        self,
        source_path: Path,
        svn_root: Path,
        svn_revision: int = 0,
        known_tables: Optional[Iterable[str]] = None,
        known_fields: Optional[Mapping[str, set[str]]] = None,
    ) -> CodeFileIndex:
        """为单个 .cs 文件生成 CodeFileIndex。

        Args:
            source_path: 文件绝对路径。
            svn_root: SVN 根目录（用于计算相对路径）。
            svn_revision: 可选的 SVN 修订号。
            known_tables: 已知的表名集合（用于识别代码中的表引用）。
            known_fields: 已知的 {表名 -> 字段集合}（识别 `Table.Field` 形式的字段访问）。

        Returns:
            CodeFileIndex 对象（始终返回，错误时 symbols/references 为空）。
        """
        try:
            raw_bytes = source_path.read_bytes()
        except FileNotFoundError:
            raw_bytes = b""

        try:
            text = raw_bytes.decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            text = ""

        try:
            rel = str(source_path.relative_to(svn_root))
        except ValueError:
            rel = str(source_path)

        rel = rel.replace("\\", "/")
        lines = text.split("\n")

        namespace = self._extract_namespace(lines)
        using_list = self._extract_using(lines)
        symbols = self._extract_symbols(lines)
        file_refs = self._extract_references(
            lines, known_tables=known_tables, known_fields=known_fields,
        )

        # 把文件级引用归并到包含它的符号上（按行号区间）
        for ref in file_refs:
            owner = self._find_enclosing_symbol(symbols, ref.line)
            if owner is not None:
                owner.references.append(ref)

        return CodeFileIndex(
            source_path=rel,
            source_hash=_sha256(raw_bytes),
            svn_revision=svn_revision,
            namespace=namespace,
            using=using_list,
            symbols=symbols,
            references=file_refs,
        )

    # ───── 抽取子流程 ─────

    def _extract_namespace(self, lines: list[str]) -> Optional[str]:
        for line in lines[:200]:
            m = _RE_NAMESPACE.search(line)
            if m:
                return m.group(1)
        return None

    def _extract_using(self, lines: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for line in lines[:200]:
            m = _RE_USING.search(line)
            if m:
                ns = m.group(1)
                if ns not in seen:
                    out.append(ns)
                    seen.add(ns)
        return out

    def _extract_symbols(self, lines: list[str]) -> list[CodeSymbol]:
        symbols: list[CodeSymbol] = []
        # 用栈维护当前作用域链；每个元素 (symbol_name, exit_brace_depth_after)
        scope_stack: list[tuple[str, int]] = []
        brace_depth = 0

        for idx, raw in enumerate(lines):
            line = raw.rstrip()
            stripped = line.strip()
            # 跳过注释行
            if stripped.startswith("//"):
                # 仍要计入大括号
                brace_depth += line.count("{") - line.count("}")
                continue

            # 类/接口/结构/枚举
            tm = _RE_TYPE.match(line)
            if tm:
                kind = tm.group(1)
                name = tm.group(2)
                summary = _summary_from_doc_above(lines, idx)
                parent = scope_stack[-1][0] if scope_stack else None
                sym = CodeSymbol(
                    name=name,
                    kind=kind,
                    parent=parent,
                    signature=_trim(line),
                    line_start=idx,
                    line_end=idx,
                    summary=summary,
                )
                symbols.append(sym)
                # 推入作用域（同行可能有 `{`，brace_depth 之后才会 +1）
                if "{" in line:
                    scope_stack.append((name, brace_depth + 1))
                else:
                    scope_stack.append((name, brace_depth + 1))
                brace_depth += line.count("{") - line.count("}")
                continue

            # 方法
            mm = _RE_METHOD.match(line)
            if mm and not stripped.startswith("if ") and not stripped.startswith("for ") \
                    and not stripped.startswith("while ") and not stripped.startswith("switch "):
                method_name = mm.group(2)
                # 排除 C# 关键字
                if method_name in {"if", "for", "while", "switch", "return", "using", "lock", "foreach"}:
                    brace_depth += line.count("{") - line.count("}")
                    continue
                parent = scope_stack[-1][0] if scope_stack else None
                summary = _summary_from_doc_above(lines, idx)
                symbols.append(CodeSymbol(
                    name=method_name,
                    kind="method",
                    parent=parent,
                    signature=_trim(line),
                    line_start=idx,
                    line_end=idx,
                    summary=summary,
                ))
                # 若签名行以 `{` 结尾, 入栈以便在 `}` 时更新 line_end
                if "{" in line:
                    scope_stack.append((method_name, brace_depth + 1))
                brace_depth += line.count("{") - line.count("}")
                continue

            # 字段/属性（粗匹配；排除带 `(` 的方法行）
            fm = _RE_FIELD.match(line)
            if fm and "(" not in line:
                # 仅当作用域顶部是类/结构/接口时才视为字段；method 内部的 `var x = ...` 应忽略
                top_kind: Optional[str] = None
                if scope_stack:
                    top_name = scope_stack[-1][0]
                    for s in reversed(symbols):
                        if s.name == top_name:
                            top_kind = s.kind
                            break
                if top_kind not in ("class", "struct", "interface"):
                    brace_depth += line.count("{") - line.count("}")
                    continue
                field_name = fm.group(2)
                kind = "property" if "{" in line else "field"
                parent = scope_stack[-1][0] if scope_stack else None
                symbols.append(CodeSymbol(
                    name=field_name,
                    kind=kind,
                    parent=parent,
                    signature=_trim(line),
                    line_start=idx,
                    line_end=idx,
                    summary=_summary_from_doc_above(lines, idx),
                ))
                brace_depth += line.count("{") - line.count("}")
                continue

            # 普通行：仅维护括号深度 + 弹栈
            brace_depth += line.count("{") - line.count("}")
            while scope_stack and brace_depth < scope_stack[-1][1]:
                # 退出作用域，更新对应符号的 line_end
                exiting_name, _ = scope_stack.pop()
                for s in reversed(symbols):
                    if s.name == exiting_name and s.line_end <= idx:
                        s.line_end = idx
                        break

        return symbols

    def _extract_references(
        self,
        lines: list[str],
        known_tables: Optional[Iterable[str]] = None,
        known_fields: Optional[Mapping[str, set[str]]] = None,
    ) -> list[CodeSymbolReference]:
        refs: list[CodeSymbolReference] = []
        if not known_tables and not known_fields:
            return refs

        tables = list(dict.fromkeys(known_tables or []))
        # 字段反查
        field_map: Mapping[str, set[str]] = known_fields or {}

        # 预编译每个表的 word-boundary 模式
        table_patterns = {t: re.compile(r"\b" + re.escape(t) + r"\b") for t in tables}

        # 已发出的 (table, field, line) 三元组去重
        seen: set[tuple[Optional[str], Optional[str], int]] = set()

        for line_idx, raw in enumerate(lines):
            line = raw.rstrip()[:5000]  # 安全截断
            if not line:
                continue
            stripped = line.strip()
            if stripped.startswith("//"):
                continue

            # 1. 优先识别 Table.Field 形式
            for table_name, fields in field_map.items():
                for m in re.finditer(
                    r"\b" + re.escape(table_name) + r"\.(\w+)", line,
                ):
                    fname = m.group(1)
                    if fname in fields:
                        key = (table_name, fname, line_idx)
                        if key in seen:
                            continue
                        seen.add(key)
                        refs.append(CodeSymbolReference(
                            target_kind="field",
                            target_table=table_name,
                            target_field=fname,
                            line=line_idx,
                            snippet=_trim(line),
                            confidence="confirmed",
                        ))

            # 2. 识别表名（标识符或字符串字面量）
            for table_name, pat in table_patterns.items():
                if not pat.search(line):
                    continue
                # 已经作为字段引用被记录的行就不再额外发表级引用
                already = any(
                    k[0] == table_name and k[2] == line_idx for k in seen
                )
                if already:
                    continue
                # 字符串字面量 → confirmed；裸标识符 → inferred
                in_string = (f'"{table_name}"' in line) or (f"'{table_name}'" in line)
                conf = "confirmed" if in_string else "inferred"
                key = (table_name, None, line_idx)
                if key in seen:
                    continue
                seen.add(key)
                refs.append(CodeSymbolReference(
                    target_kind="table",
                    target_table=table_name,
                    line=line_idx,
                    snippet=_trim(line),
                    confidence=conf,
                ))

        return refs

    @staticmethod
    def _find_enclosing_symbol(symbols: list[CodeSymbol], line: int) -> Optional[CodeSymbol]:
        """找到最贴近 line 的 method/property 级符号。"""
        candidate: Optional[CodeSymbol] = None
        for s in symbols:
            if s.line_start <= line <= max(s.line_end, s.line_start):
                if s.kind in ("method", "property", "field"):
                    candidate = s
        return candidate
