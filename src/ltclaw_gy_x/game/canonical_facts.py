from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Iterable

from .models import (
    CanonicalDocFacts,
    CanonicalField,
    CanonicalScriptFacts,
    CanonicalTableSchema,
    CodeFileIndex,
    CodeSymbolReference,
    DocIndex,
    FieldConfidence,
    FieldInfo,
    TableIndex,
)


_WORD_BOUNDARY_RE = re.compile(r"([a-z0-9])([A-Z])")
_NON_ALNUM_RE = re.compile(r"[^0-9A-Za-z_]+")
_MULTI_UNDERSCORE_RE = re.compile(r"_+")


def normalize_canonical_header(raw_header: str) -> str:
    text = str(raw_header or "").strip()
    text = _WORD_BOUNDARY_RE.sub(r"\1_\2", text)
    text = text.replace("-", "_").replace("/", "_").replace(" ", "_")
    text = _NON_ALNUM_RE.sub("_", text)
    text = _MULTI_UNDERSCORE_RE.sub("_", text).strip("_").lower()
    return text or "field"


def map_field_confidence_score(confidence: FieldConfidence) -> float:
    mapping = {
        FieldConfidence.CONFIRMED: 1.0,
        FieldConfidence.HIGH_AI: 0.75,
        FieldConfidence.LOW_AI: 0.4,
    }
    return mapping[confidence]


def infer_canonical_semantic_type(field: FieldInfo, *, primary_key: str | None = None) -> str:
    normalized_name = normalize_canonical_header(field.name)
    normalized_type = str(field.type or "").strip().lower()
    normalized_primary_key = normalize_canonical_header(primary_key or "") if primary_key else None

    if normalized_primary_key and normalized_name == normalized_primary_key:
        return "id"
    if normalized_name == "id" or normalized_name.endswith("_id"):
        return "id"
    if any(token in normalized_name for token in ("_ref", "reference", "_key")):
        return "reference"
    if normalized_type in {"bool", "boolean"}:
        return "bool"
    if normalized_type in {"list", "array"}:
        return "list"
    if normalized_type in {"int", "integer", "float", "double", "decimal", "number"}:
        return "number"
    if normalized_type in {"str", "string", "text"}:
        return "text"
    return "unknown"


def build_canonical_field(field: FieldInfo, *, primary_key: str | None = None, confirmed: bool | None = None) -> CanonicalField:
    canonical_header = normalize_canonical_header(field.name)
    aliases: list[str] = []
    for candidate in (field.name, canonical_header):
        value = str(candidate or "").strip()
        if value and value not in aliases:
            aliases.append(value)
    is_confirmed = field.confidence == FieldConfidence.CONFIRMED if confirmed is None else confirmed
    return CanonicalField(
        raw_header=field.name,
        canonical_header=canonical_header,
        aliases=aliases,
        semantic_type=infer_canonical_semantic_type(field, primary_key=primary_key),
        description=field.description,
        confidence=map_field_confidence_score(field.confidence),
        confirmed=is_confirmed,
        source='raw_index_rule',
        raw_type=field.type,
    )


def build_canonical_table_schema(table_index: TableIndex) -> CanonicalTableSchema:
    return CanonicalTableSchema(
        table_id=table_index.table_name,
        source_path=table_index.source_path,
        source_hash=table_index.source_hash,
        primary_key=table_index.primary_key,
        fields=[
            build_canonical_field(field, primary_key=table_index.primary_key)
            for field in table_index.fields
        ],
        updated_at=table_index.last_indexed_at,
    )


def build_canonical_doc_facts(doc_index: DocIndex, *, confirmed: bool = False) -> CanonicalDocFacts:
    semantic_tags = [tag for tag in [str(doc_index.doc_type or "").strip().lower()] if tag]
    related_refs = sorted({f"table:{table_name}" for table_name in doc_index.related_tables if str(table_name).strip()})
    confidence = 1.0 if confirmed else 0.75
    return CanonicalDocFacts(
        doc_id=_stable_doc_id(doc_index.source_path),
        source_path=doc_index.source_path,
        source_hash=doc_index.source_hash,
        title=doc_index.title,
        summary=doc_index.summary,
        semantic_tags=semantic_tags,
        related_refs=related_refs,
        confidence=confidence,
        confirmed=confirmed,
    )


def build_canonical_script_facts(code_index: CodeFileIndex, *, confirmed: bool = False) -> CanonicalScriptFacts:
    responsibilities = [summary for summary in _iter_unique_strings(symbol.summary for symbol in code_index.symbols) if summary]
    symbols = [name for name in _iter_unique_strings(symbol.name for symbol in code_index.symbols) if name]
    related_refs = sorted(_collect_script_related_refs(code_index))
    confidence = 1.0 if confirmed else 0.75
    return CanonicalScriptFacts(
        script_id=_stable_script_id(code_index.source_path),
        source_path=code_index.source_path,
        source_hash=code_index.source_hash,
        symbols=symbols,
        responsibilities=responsibilities,
        related_refs=related_refs,
        confidence=confidence,
        confirmed=confirmed,
    )


def _collect_script_related_refs(code_index: CodeFileIndex) -> set[str]:
    refs: set[str] = set()
    for reference in [*code_index.references, *[nested for symbol in code_index.symbols for nested in symbol.references]]:
        refs.update(_reference_to_related_refs(reference))
    return refs


def _reference_to_related_refs(reference: CodeSymbolReference) -> set[str]:
    refs: set[str] = set()
    if reference.target_table:
        refs.add(f"table:{reference.target_table}")
    if reference.target_field and reference.target_table:
        refs.add(f"field:{reference.target_table}.{reference.target_field}")
    if reference.target_symbol:
        refs.add(f"symbol:{reference.target_symbol}")
    return refs


def _iter_unique_strings(values: Iterable[str | None]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _stable_doc_id(source_path: str) -> str:
    return 'doc-' + hashlib.sha1(source_path.encode('utf-8')).hexdigest()[:12]


def _stable_script_id(source_path: str) -> str:
    stem = Path(str(source_path or '')).stem.strip()
    normalized = _NON_ALNUM_RE.sub('_', stem).strip('_')
    if normalized:
        return normalized
    return 'script_' + hashlib.sha1(source_path.encode('utf-8')).hexdigest()[:12]