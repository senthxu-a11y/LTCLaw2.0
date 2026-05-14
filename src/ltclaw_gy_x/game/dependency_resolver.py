"""
依赖关系解析器。

DependencyGraph 属于 technical index / impact evidence，服务于 Workbench 影响分析
与工程侧排查。它不是 Formal Map relationship，也不是 RAG 的正式知识结构来源。
"""

import logging
import re
from typing import Optional, Dict, List

from .config import ProjectConfig
from .models import TableIndex, DependencyGraph, DependencyEdge, FieldConfidence, FieldInfo

logger = logging.getLogger(__name__)


def get_dependency_graph_source_metadata() -> dict[str, object]:
    return {
        'source_type': 'dependency_graph',
        'semantic_role': 'technical_impact_evidence',
        'is_formal_map_relationship': False,
        'governs_release': False,
        'governs_rag': False,
        'governs_workbench_write': False,
    }


class DependencyResolver:
    def __init__(self, project: ProjectConfig, model_router):
        self.project = project
        self.model_router = model_router
        self.foreign_key_patterns = [
            r'(\w+)ID$',
            r'(\w+)Id$',
            r'(\w+)_ID$',
            r'(\w+)_Id$',
            r'(\w+)_id$',
            r'(\w+)Ref$',
            r'(\w+)Reference$',
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.foreign_key_patterns]

    def _extract_foreign_key_candidates(self, tables: List[TableIndex]) -> List[Dict]:
        candidates = []
        for table in tables:
            for field in table.fields:
                if field.name.lower() == table.primary_key.lower():
                    continue
                matched_pattern = False
                for pattern in self.compiled_patterns:
                    match = pattern.match(field.name)
                    if match:
                        referenced_name = match.group(1)
                        candidates.append({
                            'from_table': table.table_name,
                            'from_field': field.name,
                            'field_info': field,
                            'referenced_name': referenced_name,
                            'pattern_matched': True,
                        })
                        matched_pattern = True
                        break
                if not matched_pattern:
                    field_lower = field.name.lower()
                    if any(k in field_lower for k in ['id', 'ref', 'key']):
                        referenced_name = self._extract_table_name_from_field(field.name)
                        if referenced_name:
                            candidates.append({
                                'from_table': table.table_name,
                                'from_field': field.name,
                                'field_info': field,
                                'referenced_name': referenced_name,
                                'pattern_matched': False,
                            })
        return candidates

    def _extract_table_name_from_field(self, field_name: str) -> Optional[str]:
        suffixes = ['ID', 'Id', 'id', '_ID', '_Id', '_id', 'Ref', 'Reference', 'Key']
        clean_name = field_name
        for suffix in suffixes:
            if clean_name.endswith(suffix):
                clean_name = clean_name[:-len(suffix)]
                break
        clean_name = clean_name.replace('_', '')
        if len(clean_name) >= 2:
            return clean_name
        return None

    def _find_target_table(self, referenced_name: str, tables: List[TableIndex]) -> Optional[TableIndex]:
        table_map = {}
        for table in tables:
            table_map[table.table_name.lower()] = table
            clean_table_name = table.table_name.lower()
            if clean_table_name.endswith('table'):
                clean_table_name = clean_table_name[:-5]
                table_map[clean_table_name] = table
        referenced_lower = referenced_name.lower()
        if referenced_lower in table_map:
            return table_map[referenced_lower]
        referenced_with_table = f"{referenced_lower}table"
        if referenced_with_table in table_map:
            return table_map[referenced_with_table]
        for table_name, table in table_map.items():
            if referenced_lower in table_name or table_name in referenced_lower:
                similarity = max(len(referenced_lower), len(table_name)) / (len(referenced_lower) + len(table_name))
                if similarity > 0.4:
                    return table
        return None

    def _resolve_rule_based_dependencies(self, tables: List[TableIndex]) -> List[DependencyEdge]:
        logger.info("开始规则层依赖解析")
        edges = []
        candidates = self._extract_foreign_key_candidates(tables)
        for candidate in candidates:
            target_table = self._find_target_table(candidate['referenced_name'], tables)
            if target_table:
                target_field = target_table.primary_key
                from_field_info = candidate['field_info']
                target_field_info = next((f for f in target_table.fields if f.name == target_field), None)
                if target_field_info and self._are_types_compatible(from_field_info.type, target_field_info.type):
                    confidence = FieldConfidence.CONFIRMED if candidate['pattern_matched'] else FieldConfidence.HIGH_AI
                    edge = DependencyEdge(
                        from_table=candidate['from_table'],
                        from_field=candidate['from_field'],
                        to_table=target_table.table_name,
                        to_field=target_field,
                        confidence=confidence,
                        inferred_by="rule",
                    )
                    edges.append(edge)
        logger.info(f"规则层解析完成，发现{len(edges)}个依赖关系")
        return edges

    def _are_types_compatible(self, from_type: str, to_type: str) -> bool:
        numeric_types = {'int', 'float', 'number'}
        if from_type in numeric_types and to_type in numeric_types:
            return True
        if from_type == 'str' or to_type == 'str':
            return True
        return from_type == to_type

    async def _resolve_llm_dependencies(self, tables: List[TableIndex],
                                         ruled_edges: List[DependencyEdge]) -> List[DependencyEdge]:
        logger.info("开始LLM层依赖解析")
        resolved_fields = set()
        for edge in ruled_edges:
            resolved_fields.add(f"{edge.from_table}.{edge.from_field}")
        llm_candidates = []
        for table in tables:
            for field in table.fields:
                field_key = f"{table.table_name}.{field.name}"
                if field_key in resolved_fields or field.name.lower() == table.primary_key.lower():
                    continue
                if self._is_potential_foreign_key(field):
                    llm_candidates.append({'table': table, 'field': field})
        if not llm_candidates:
            logger.info("没有需要LLM分析的字段")
            return []
        try:
            llm_edges = await self._analyze_dependencies_with_llm(llm_candidates, tables)
            logger.info(f"LLM层解析完成，发现{len(llm_edges)}个依赖关系")
            return llm_edges
        except Exception as e:
            logger.error(f"LLM依赖分析失败: {e}")
            return []

    def _is_potential_foreign_key(self, field: FieldInfo) -> bool:
        field_name_lower = field.name.lower()
        keywords = ['id', 'ref', 'key', 'link', 'target', 'source']
        if any(k in field_name_lower for k in keywords):
            return True
        if field.type in ['int', 'float'] and len(field.name) > 2:
            return True
        if field.description and field.confidence != FieldConfidence.LOW_AI:
            desc_lower = field.description.lower()
            ref_words = ['引用', '关联', '对应', '指向', '标识', 'id', 'reference', 'link']
            if any(w in desc_lower for w in ref_words):
                return True
        return False

    async def _analyze_dependencies_with_llm(self, candidates: List[Dict],
                                              tables: List[TableIndex]) -> List[DependencyEdge]:
        if not candidates:
            return []
        try:
            prompt = self._build_dependency_analysis_prompt(candidates, tables)
            response = await self.model_router.call_model(prompt, model_type="dependency_analyzer")
            return self._parse_dependency_analysis_response(response, candidates, tables)
        except Exception as e:
            logger.error(f"LLM依赖分析调用失败: {e}")
            return []

    def _build_dependency_analysis_prompt(self, candidates: List[Dict], tables: List[TableIndex]) -> str:
        table_info = []
        for table in tables:
            fields_str = ", ".join([f"{f.name}({f.type})" for f in table.fields[:8]])
            table_info.append(f"- {table.table_name}: {fields_str}")
        candidate_info = []
        for i, candidate in enumerate(candidates[:20]):
            table = candidate['table']
            field = candidate['field']
            candidate_info.append(f"{i+1}. {table.table_name}.{field.name} ({field.type}): {field.description}")
        nl = chr(10)
        prompt = (
            "请分析以下游戏数据表字段的依赖关系。" + nl + nl +
            "数据表列表：" + nl + nl.join(table_info) + nl + nl +
            "待分析字段：" + nl + nl.join(candidate_info) + nl + nl +
            '请判断哪些字段可能是外键，引用了其他表的主键。对于每个可能的依赖关系，请以JSON格式返回：' + nl + nl +
            '{' + nl +
            '  "dependencies": [' + nl +
            '    {' + nl +
            '      "from_table": "源表名",' + nl +
            '      "from_field": "源字段名",' + nl +
            '      "to_table": "目标表名",' + nl +
            '      "to_field": "目标字段名",' + nl +
            '      "confidence": 0.0到1.0的置信度,' + nl +
            '      "reason": "判断理由"' + nl +
            '    }' + nl +
            '  ]' + nl +
            '}' + nl + nl +
            '注意：' + nl +
            '1. 只返回确信度较高的依赖关系（confidence > 0.6）' + nl +
            '2. 目标字段通常是目标表的主键' + nl +
            '3. 字段名称和描述是重要的判断依据'
        )
        return prompt

    def _parse_dependency_analysis_response(self, response, candidates: List[Dict],
                                             tables: List[TableIndex]) -> List[DependencyEdge]:
        try:
            import json
            if isinstance(response, dict):
                data = response
            else:
                response_clean = response.strip()
                if response_clean.startswith("```json"):
                    response_clean = response_clean[7:]
                if response_clean.endswith("```"):
                    response_clean = response_clean[:-3]
                data = json.loads(response_clean)
            edges = []
            dependencies = data.get("dependencies", [])
            table_map = {t.table_name.lower(): t for t in tables}
            for dep in dependencies:
                from_table = dep.get("from_table", "").strip()
                from_field = dep.get("from_field", "").strip()
                to_table = dep.get("to_table", "").strip()
                to_field = dep.get("to_field", "").strip()
                confidence_score = float(dep.get("confidence", 0))
                if (from_table.lower() not in table_map or
                    to_table.lower() not in table_map or
                    confidence_score <= 0.6):
                    continue
                if confidence_score >= 0.8:
                    confidence = FieldConfidence.HIGH_AI
                else:
                    confidence = FieldConfidence.LOW_AI
                edge = DependencyEdge(
                    from_table=from_table,
                    from_field=from_field,
                    to_table=to_table,
                    to_field=to_field,
                    confidence=confidence,
                    inferred_by="llm",
                )
                edges.append(edge)
            return edges
        except Exception as e:
            logger.error(f"解析LLM依赖分析响应失败: {e}")
            return []

    def _merge_manual_dependencies(self, new_edges: List[DependencyEdge],
                                    prev_graph: Optional[DependencyGraph]) -> List[DependencyEdge]:
        if not prev_graph:
            return new_edges
        manual_edges = [e for e in prev_graph.edges if e.inferred_by == "manual"]
        if not manual_edges:
            return new_edges

        def edge_key(e: DependencyEdge) -> str:
            return f"{e.from_table}.{e.from_field}->{e.to_table}.{e.to_field}"

        new_edges_map = {edge_key(e): e for e in new_edges}
        for me in manual_edges:
            new_edges_map[edge_key(me)] = me
        return list(new_edges_map.values())

    async def resolve(self, tables: List[TableIndex],
                      prev_graph: Optional[DependencyGraph] = None) -> DependencyGraph:
        from datetime import datetime
        logger.info(f"开始解析{len(tables)}个表的依赖关系")
        if not tables:
            return DependencyGraph(edges=[], last_updated=datetime.now())
        rule_edges = self._resolve_rule_based_dependencies(tables)
        llm_edges = await self._resolve_llm_dependencies(tables, rule_edges)
        all_edges = rule_edges + llm_edges
        deduplicated_edges = self._deduplicate_edges(all_edges)
        final_edges = self._merge_manual_dependencies(deduplicated_edges, prev_graph)
        return DependencyGraph(edges=final_edges, last_updated=datetime.now())

    def _deduplicate_edges(self, edges: List[DependencyEdge]) -> List[DependencyEdge]:
        edge_map = {}
        for edge in edges:
            key = f"{edge.from_table}.{edge.from_field}->{edge.to_table}.{edge.to_field}"
            if key not in edge_map:
                edge_map[key] = edge
            else:
                if self._compare_confidence(edge.confidence, edge_map[key].confidence) > 0:
                    edge_map[key] = edge
        return list(edge_map.values())

    def _compare_confidence(self, c1: FieldConfidence, c2: FieldConfidence) -> int:
        order = {FieldConfidence.CONFIRMED: 3, FieldConfidence.HIGH_AI: 2, FieldConfidence.LOW_AI: 1}
        s1 = order.get(c1, 0)
        s2 = order.get(c2, 0)
        if s1 > s2:
            return 1
        if s1 < s2:
            return -1
        return 0