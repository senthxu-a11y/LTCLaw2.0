"""
表格索引器
"""

import asyncio
import csv
import hashlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import openpyxl

from .config import ProjectConfig
from .models import FieldConfidence, FieldInfo, TableIndex

logger = logging.getLogger(__name__)


class TableIndexer:
    def __init__(self, project: ProjectConfig, model_router, cache_dir: Path):
        self.project = project
        self.model_router = model_router
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.field_cache_dir = self.cache_dir / "fields"
        self.summary_cache_dir = self.cache_dir / "summaries"
        self.field_cache_dir.mkdir(parents=True, exist_ok=True)
        self.summary_cache_dir.mkdir(parents=True, exist_ok=True)

    def _calculate_file_hash(self, file_path: Path) -> str:
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
        except Exception as e:
            logger.error(f"计算文件hash失败: {file_path}, {e}")
            fallback = f"{file_path}_{file_path.stat().st_mtime}".encode()
            sha256_hash.update(fallback)
        return f"sha256:{sha256_hash.hexdigest()}"

    def _infer_field_type(self, values: list) -> str:
        if not values:
            return "str"
        non_empty = [v for v in values if v is not None and str(v).strip()]
        if not non_empty:
            return "str"
        numeric_count = 0
        for value in non_empty:
            try:
                if isinstance(value, (int, float)):
                    numeric_count += 1
                elif isinstance(value, str):
                    if "." in value:
                        float(value)
                    else:
                        int(value)
                    numeric_count += 1
            except (ValueError, TypeError):
                pass
        if numeric_count / len(non_empty) >= 0.8:
            has_float = False
            for value in non_empty[:10]:
                try:
                    if isinstance(value, float) or (isinstance(value, str) and "." in value):
                        has_float = True
                        break
                except Exception:
                    pass
            return "float" if has_float else "int"
        bool_keywords = {"true", "false", "是", "否", "yes", "no", "1", "0"}
        bool_count = sum(1 for v in non_empty if str(v).lower().strip() in bool_keywords)
        if bool_count / len(non_empty) >= 0.8:
            return "bool"
        list_count = sum(1 for v in non_empty if any(s in str(v) for s in [",", ";", "|"]))
        if list_count / len(non_empty) >= 0.5:
            return "list"
        return "str"

    def _is_blank_llm_response(self, response: Any) -> bool:
        if response is None:
            return True
        if isinstance(response, dict):
            return not any(str(v).strip() for v in response.values() if v is not None)
        return not str(response).strip()

    async def _describe_fields_with_llm(self, table_name: str, fields_data: list) -> dict:
        if not fields_data:
            return {}
        try:
            prompt = self._build_field_description_prompt(table_name, fields_data)
            response = await self.model_router.call_model(prompt, model_type="field_describer")
            if self._is_blank_llm_response(response):
                raise ValueError(f"字段描述模型返回空响应: {table_name}")
            return self._parse_field_description_response(response, fields_data)
        except Exception as e:
            logger.error(f"LLM字段描述生成失败: {e}")
            return {f["name"]: {"description": f"{f['name']}字段", "confidence": 0.1} for f in fields_data}

    def _build_field_description_prompt(self, table_name: str, fields_data: list) -> str:
        nl = chr(10)
        fields_info = []
        for f in fields_data:
            sample_str = ", ".join(str(v) for v in f["sample_values"][:3])
            fields_info.append(f"- {f['name']} ({f['type']}): 示例值 [{sample_str}]")
        return (
            f'请分析游戏数据表"{table_name}"的字段含义。' + nl + nl +
            "字段信息:" + nl + nl.join(fields_info) + nl + nl +
            '以JSON格式返回 {"字段名": {"description": "...", "confidence": 0.0-1.0}}。'
        )

    def _parse_field_description_response(self, response, fields_data: list) -> dict:
        try:
            if isinstance(response, dict):
                data = response
            else:
                rc = response.strip()
                if rc.startswith("```json"):
                    rc = rc[7:]
                if rc.endswith("```"):
                    rc = rc[:-3]
                data = json.loads(rc)
            result = {}
            for f in fields_data:
                name = f["name"]
                if name in data:
                    fd = data[name]
                    description = str(fd.get("description", "")).strip()
                    confidence = fd.get("confidence", 0.5)
                    if not description:
                        description = f"{name}字段"
                        confidence = 0.1
                    result[name] = {
                        "description": description,
                        "confidence": min(1.0, max(0.0, confidence)),
                    }
                else:
                    result[name] = {"description": f"{name}字段", "confidence": 0.1}
            return result
        except Exception as e:
            logger.error(f"解析LLM响应失败: {e}")
            return {f["name"]: {"description": f"{f['name']}字段", "confidence": 0.1} for f in fields_data}

    async def _generate_table_summary(self, table_name: str, fields, sample_rows) -> tuple:
        try:
            nl = chr(10)
            fields_desc = [f"- {f.name}: {f.description}" for f in fields[:10]]
            sample_desc = []
            for i, row in enumerate(sample_rows[:3]):
                sample_desc.append(f"第{i+1}行: {dict(list(row.items())[:5])}")
            prompt = (
                f'请为游戏数据表"{table_name}"生成一句话中文摘要。' + nl +
                "字段:" + nl + nl.join(fields_desc) + nl +
                "样本:" + nl + nl.join(sample_desc)
            )
            response = await self.model_router.call_model(prompt, model_type="table_summarizer")
            if self._is_blank_llm_response(response):
                raise ValueError(f"表摘要模型返回空响应: {table_name}")
            if isinstance(response, dict):
                summary = response.get("summary", response.get("text", str(response)))
            else:
                summary = str(response).strip()
            summary = summary.replace("**", "").replace("*", "").strip()
            if not summary:
                raise ValueError(f"表摘要解析为空: {table_name}")
            return summary, 0.8
        except Exception as e:
            logger.error(f"生成表格摘要失败: {e}")
            return f"{table_name}数据配置表", 0.1

    def _read_excel_file(self, file_path: Path) -> tuple:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        for ws in wb.worksheets:
            data = [list(row) for row in ws.iter_rows(values_only=True)]
            if any(cell is not None and str(cell).strip() for row in data for cell in row):
                return data, len(data)
        return [], 0

    def _read_csv_file(self, file_path: Path) -> tuple:
        encodings = ["utf-8-sig", "utf-8", "gbk", "gb2312"]
        content = None
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        if content is None:
            raise ValueError("无法解码CSV文件")
        try:
            delimiter = csv.Sniffer().sniff(content[:1024]).delimiter
        except Exception:
            delimiter = ","
        reader = csv.reader(content.splitlines(), delimiter=delimiter)
        data = [row for row in reader]
        return data, len(data)

    def _build_rule_only_field_descriptions(self, fields_data: list, txt_docs: dict[str, str]) -> dict:
        descriptions = {}
        for field_data in fields_data:
            name = field_data["name"]
            descriptions[name] = {
                "description": txt_docs.get(name, f"{name}字段"),
                "confidence": 0.1,
            }
        return descriptions

    def _build_rule_only_summary(self, table_name: str) -> tuple[str, float]:
        return f"{table_name}数据配置表", 0.1

    def _analyze_id_ranges(self, primary_key_values: list) -> list:
        if not primary_key_values:
            return []
        numeric_ids = []
        for v in primary_key_values:
            try:
                if isinstance(v, (int, float)):
                    numeric_ids.append(int(v))
                elif isinstance(v, str) and v.strip().isdigit():
                    numeric_ids.append(int(v.strip()))
            except (ValueError, TypeError):
                pass
        if not numeric_ids:
            return []
        ranges = []
        for r in self.project.table_convention.id_ranges:
            matching = [i for i in numeric_ids if r.start <= i <= r.end]
            if matching:
                ranges.append({
                    "type": r.type,
                    "start": r.start,
                    "end": r.end,
                    "count": len(matching),
                    "actual_min": min(matching),
                    "actual_max": max(matching),
                })
        return ranges

    def _read_txt_file(self, source: Path) -> tuple[list[list[Any]], dict[str, str]]:
        """Read a TAB-separated txt table.

        Supported forms:
        - First non-comment row is a plain TAB header row.
        - Legacy ┇-encoded header cells are still normalized when present.

        Lines starting with # or // are ignored. Blank lines are ignored.
        Returns (rows_with_normalized_header, field_doc_map).
        """
        raw_bytes = source.read_bytes()
        if raw_bytes.startswith(b"\xef\xbb\xbf"):
            raw_bytes = raw_bytes[3:]
        text: Optional[str] = None
        for enc in ("utf-8", "gbk", "gb2312"):
            try:
                text = raw_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if text is None:
            raise ValueError(f"unable to decode txt file: {source}")
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        filtered_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            filtered_lines.append(line)
        rows: list[list[Any]] = [line.split("\t") for line in filtered_lines]
        docs: dict[str, str] = {}
        if rows:
            header_cells = rows[0]
            norm: list[str] = []
            uses_encoded_header = False
            for i, cell in enumerate(header_cells):
                cell_s = (cell or "").strip()
                name = ""
                doc = ""
                if "┇" in cell_s:
                    uses_encoded_header = True
                    name, _, meta = cell_s.partition("┇")
                    name = name.strip()
                    for seg in meta.split(";"):
                        seg = seg.strip()
                        if seg.startswith("Doc="):
                            doc = seg[4:].strip()
                            break
                else:
                    name = cell_s
                if not name:
                    name = f"Column_{i}"
                norm.append(name)
                if doc:
                    docs[name] = doc
            rows[0] = norm
            if uses_encoded_header and len(rows) > 1:
                label_row = rows[1]
                if len(label_row) == len(norm) and not any("┇" in str(cell or "") for cell in label_row):
                    rows = [rows[0], *rows[2:]]
        return rows, docs

    def _determine_system_from_path(self, source_path: Path) -> Optional[str]:
        path_str = str(source_path).replace("\\", "/")
        for rule in self.project.paths:
            if rule.semantic == "table" and rule.system:
                pattern = rule.path.replace("**", "*").replace("*", ".*")
                if re.match(pattern, path_str, re.IGNORECASE):
                    return rule.system
        return None

    async def index_one(
        self,
        source: Path,
        svn_root: Path,
        svn_revision: int,
        prev: Optional[TableIndex] = None,
        rule_only: bool = False,
    ) -> TableIndex:
        logger.info(f"开始索引表格: {source}")
        file_hash = self._calculate_file_hash(source)
        if prev and prev.source_hash == file_hash:
            prev.svn_revision = svn_revision
            return prev
        suffix = source.suffix.lower()
        txt_docs: dict[str, str] = {}
        if suffix in [".xlsx", ".xls"]:
            raw_data, _ = self._read_excel_file(source)
        elif suffix == ".csv":
            raw_data, _ = self._read_csv_file(source)
        elif suffix == ".txt":
            raw_data, txt_docs = self._read_txt_file(source)
        else:
            raise ValueError(f"不支持的文件格式: {suffix}")
        if not raw_data:
            raise ValueError(f"文件为空: {source}")
        header_row_idx = self.project.table_convention.header_row - 1
        if len(raw_data) <= header_row_idx:
            raise ValueError(f"文件行数不足: {source}")
        if len(raw_data) <= header_row_idx + 1:
            raise ValueError(f"文件行数不足: {source}")
        headers = [
            str(c).strip() if c is not None else f"Column_{i}"
            for i, c in enumerate(raw_data[header_row_idx])
        ]
        if suffix == ".txt":
            headers = [h if h else f"Column_{i}" for i, h in enumerate(headers)]
        else:
            valid_count = 0
            for h in headers:
                if h and h != "None":
                    valid_count += 1
                else:
                    break
            headers = headers[:valid_count]
        if not headers:
            raise ValueError(f"未找到有效表头: {source}")
        data_start = header_row_idx + 1
        comment_row = self.project.table_convention.comment_row
        if comment_row is not None and comment_row > self.project.table_convention.header_row:
            data_start = comment_row
        data_rows = raw_data[data_start:]
        data_rows = [row[: len(headers)] for row in data_rows]
        data_rows = [row for row in data_rows if any(c is not None and str(c).strip() for c in row)]
        row_count = len(data_rows)
        fields_data = []
        for i, header in enumerate(headers):
            column_values = [row[i] if i < len(row) else None for row in data_rows]
            ftype = self._infer_field_type(column_values)
            samples = []
            for v in column_values[:10]:
                if v is not None and str(v).strip():
                    samples.append(str(v).strip())
            fields_data.append({"name": header, "type": ftype, "sample_values": samples})
        table_name = source.stem
        if rule_only:
            descs = self._build_rule_only_field_descriptions(fields_data, txt_docs)
        elif txt_docs:
            missing = [fd for fd in fields_data if fd["name"] not in txt_docs]
            llm_descs = (
                await self._describe_fields_with_llm(table_name, missing) if missing else {}
            )
            descs = {}
            for fd in fields_data:
                name = fd["name"]
                if name in txt_docs:
                    descs[name] = {"description": txt_docs[name], "confidence": 0.9}
                elif name in llm_descs:
                    descs[name] = llm_descs[name]
        else:
            descs = await self._describe_fields_with_llm(table_name, fields_data)
        fields = []
        for fd in fields_data:
            name = fd["name"]
            di = descs.get(name, {"description": f"{name}字段", "confidence": 0.1})
            score = di["confidence"]
            confidence = FieldConfidence.HIGH_AI if score >= 0.4 else FieldConfidence.LOW_AI
            fields.append(
                FieldInfo(
                    name=name,
                    type=fd["type"],
                    description=di["description"],
                    confidence=confidence,
                    ai_raw_description=di["description"],
                )
            )
        primary_key = self.project.table_convention.resolve_primary_key(
            table_name=table_name,
            headers=headers,
        )
        pk_index = None
        for i, h in enumerate(headers):
            if h.lower() == primary_key.lower():
                pk_index = i
                break
        pk_values = []
        if pk_index is not None:
            pk_values = [row[pk_index] if pk_index < len(row) else None for row in data_rows]
        id_ranges = self._analyze_id_ranges(pk_values)
        relative_path = source.relative_to(svn_root) if source.is_absolute() else source
        system = self._determine_system_from_path(relative_path)
        sample_rows = []
        for row in data_rows[:5]:
            d = {}
            for i, v in enumerate(row):
                if i < len(headers):
                    d[headers[i]] = v
            sample_rows.append(d)
        if rule_only:
            summary, summary_conf = self._build_rule_only_summary(table_name)
        else:
            summary, summary_conf = await self._generate_table_summary(table_name, fields, sample_rows)
        return TableIndex(
            table_name=table_name,
            source_path=str(relative_path).replace("\\", "/"),
            source_hash=file_hash,
            svn_revision=svn_revision,
            system=system,
            row_count=row_count,
            header_row=self.project.table_convention.header_row,
            primary_key=primary_key,
            ai_summary=summary,
            ai_summary_confidence=summary_conf,
            fields=fields,
            id_ranges=id_ranges,
            last_indexed_at=datetime.now(),
            indexer_model='rule_only' if rule_only else self._get_indexer_model_name(),
        )

    def _get_indexer_model_name(self) -> str:
        try:
            ref = self.project.models.get("field_describer")
            if ref:
                return f"{ref.provider_id}/{ref.model_id}"
            return "unknown_model"
        except Exception:
            return "unknown_model"

    async def index_batch(self, sources: list, svn_root: Path, svn_revision: int, rule_only: bool = False) -> list:
        if not sources:
            return []
        logger.info(f"开始批量索引: {len(sources)}个文件")
        semaphore = asyncio.Semaphore(3)

        async def _one(src: Path):
            async with semaphore:
                try:
                    return await self.index_one(src, svn_root, svn_revision, rule_only=rule_only)
                except Exception as e:
                    logger.error(f"索引文件失败: {src}, {e}")
                    return None

        results = await asyncio.gather(*[_one(s) for s in sources], return_exceptions=True)
        out = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                logger.error(f"索引任务异常: {sources[i]}, {r}")
            elif r is not None:
                out.append(r)
        return out
