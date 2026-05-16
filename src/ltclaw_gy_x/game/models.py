from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


class FieldConfidence(str, Enum):
    CONFIRMED = 'confirmed'
    HIGH_AI = 'high_ai'
    LOW_AI = 'low_ai'


class FieldInfo(BaseModel):
    name: str = Field(description='Field name')
    type: str = Field(description='Field type')
    description: str = Field(description='Field description')
    confidence: FieldConfidence = Field(description='Confidence')
    confirmed_by: Union[str, None] = Field(default=None, description='Confirmed by')
    confirmed_at: Union[datetime, None] = Field(default=None, description='Confirmed at')
    ai_raw_description: Union[str, None] = Field(default=None, description='Raw AI description')
    references: list[str] = Field(default_factory=list, description='References')
    tags: list[str] = Field(default_factory=list, description='Tags')


class TableIndex(BaseModel):
    schema_version: Literal['table-index.v1'] = Field(default='table-index.v1')
    table_name: str = Field(description='Table name')
    source_path: str = Field(description='Source path relative to svn_root')
    source_hash: str = Field(description='Source hash')
    svn_revision: int = Field(description='SVN revision')
    system: Union[str, None] = Field(default=None, description='Owning system')
    row_count: int = Field(description='Row count')
    header_row: int = Field(default=1, description='Header row')
    primary_key: str = Field(default='ID', description='Primary key field')
    ai_summary: str = Field(description='AI summary')
    ai_summary_confidence: float = Field(description='AI summary confidence')
    fields: list[FieldInfo] = Field(default_factory=list, description='Fields')
    id_ranges: list[dict] = Field(default_factory=list, description='ID ranges')
    last_indexed_at: datetime = Field(description='Last indexed at')
    indexer_model: str = Field(description='Indexer model')


CanonicalSemanticType = Literal['id', 'reference', 'number', 'text', 'bool', 'list', 'unknown']
CanonicalFactSource = Literal['raw_index_rule', 'manual', 'llm_draft']


class CanonicalField(BaseModel):
    raw_header: str = Field(description='Original header from raw index')
    canonical_header: str = Field(description='Deterministic normalized header')
    aliases: list[str] = Field(default_factory=list, description='Known header aliases including raw and canonical header')
    semantic_type: CanonicalSemanticType = Field(default='unknown', description='Deterministic semantic type classification')
    description: str = Field(default='', description='Field description inherited from raw index')
    confidence: float = Field(default=0.0, description='Deterministic confidence score in range 0..1')
    confirmed: bool = Field(default=False, description='Whether field semantics are confirmed')
    source: CanonicalFactSource = Field(default='raw_index_rule', description='How the canonical field draft was produced')
    raw_type: Optional[str] = Field(default=None, description='Original raw field type when available')


class CanonicalTableSchema(BaseModel):
    schema_version: Literal['canonical-table-schema.v1'] = Field(default='canonical-table-schema.v1')
    table_id: str = Field(description='Canonical table identifier')
    source_path: str = Field(description='Source path relative to project root')
    source_hash: str = Field(description='Source hash copied from raw table index')
    primary_key: str = Field(description='Primary key from raw table index')
    fields: list[CanonicalField] = Field(default_factory=list, description='Canonical field drafts derived from raw fields')
    updated_at: datetime = Field(description='Last update timestamp for this canonical schema draft')


class CanonicalDocFacts(BaseModel):
    schema_version: Literal['canonical-doc-facts.v1'] = Field(default='canonical-doc-facts.v1')
    doc_id: str = Field(description='Canonical document identifier')
    source_path: str = Field(description='Source path relative to project root')
    source_hash: str = Field(description='Source hash copied from raw doc index')
    title: str = Field(description='Document title')
    summary: str = Field(default='', description='Deterministic summary draft')
    chunks: list[str] = Field(default_factory=list, description='Deterministic document chunks used for release grounding')
    semantic_tags: list[str] = Field(default_factory=list, description='Deterministic semantic tags')
    related_refs: list[str] = Field(default_factory=list, description='Canonical references related to this document')
    confidence: float = Field(default=0.0, description='Deterministic confidence score in range 0..1')
    confirmed: bool = Field(default=False, description='Whether document facts are explicitly confirmed')


class CanonicalScriptFacts(BaseModel):
    schema_version: Literal['canonical-script-facts.v1'] = Field(default='canonical-script-facts.v1')
    script_id: str = Field(description='Canonical script identifier')
    source_path: str = Field(description='Source path relative to project root')
    source_hash: str = Field(description='Source hash copied from raw code index')
    symbols: list[str] = Field(default_factory=list, description='Top-level symbol names in deterministic order')
    responsibilities: list[str] = Field(default_factory=list, description='Deterministic responsibility summaries')
    related_refs: list[str] = Field(default_factory=list, description='Canonical references related to this script')
    confidence: float = Field(default=0.0, description='Deterministic confidence score in range 0..1')
    confirmed: bool = Field(default=False, description='Whether script facts are explicitly confirmed')


class DocIndex(BaseModel):
    schema_version: Literal['doc-index.v1'] = Field(default='doc-index.v1')
    source_path: str = Field(description='Source path relative to svn_root')
    source_hash: str = Field(description='Source hash')
    svn_revision: int = Field(description='SVN revision')
    doc_type: str = Field(description='Document type')
    title: str = Field(description='Document title')
    summary: str = Field(description='Document summary')
    chunks: list[str] = Field(default_factory=list, description='Document chunks for release grounding')
    tags: list[str] = Field(default_factory=list, description='Deterministic document tags')
    related_tables: list[str] = Field(default_factory=list, description='Related tables')
    last_indexed_at: datetime = Field(description='Last indexed at')


class DependencyEdge(BaseModel):
    from_table: str = Field(description='Source table')
    from_field: str = Field(description='Source field')
    to_table: str = Field(description='Target table')
    to_field: str = Field(description='Target field')
    confidence: FieldConfidence = Field(description='Confidence')
    inferred_by: Literal['rule', 'llm', 'manual', 'code_regex'] = Field(description='Inference source')


class DependencyGraph(BaseModel):
    schema_version: Literal['dep-graph.v1'] = Field(default='dep-graph.v1')
    edges: list[DependencyEdge] = Field(default_factory=list, description='Dependency edges')
    last_updated: datetime = Field(description='Last updated at')


class SystemGroup(BaseModel):
    name: str = Field(description='System name')
    tables: list[str] = Field(default_factory=list, description='Tables in group')
    description: Union[str, None] = Field(default=None, description='Description')
    source: Literal['config', 'ai', 'manual'] = Field(description='Group source')


class ChangeSet(BaseModel):
    from_rev: int = Field(description='From revision')
    to_rev: int = Field(description='To revision')
    added: list[str] = Field(default_factory=list, description='Added files')
    modified: list[str] = Field(default_factory=list, description='Modified files')
    deleted: list[str] = Field(default_factory=list, description='Deleted files')


class CommitResult(BaseModel):
    revision: Union[int, None] = Field(default=None, description='Committed revision')
    files_committed: int = Field(default=0, description='Committed file count')
    skipped_reason: Union[str, None] = Field(default=None, description='Skip reason')


class FieldPatch(BaseModel):
    description: Union[str, None] = Field(default=None, description='Patched description')
    confidence: Union[FieldConfidence, None] = Field(default=None, description='Patched confidence')
    confirmed_by: Union[str, None] = Field(default=None, description='Confirmed by')


class SvnStatus(BaseModel):
    current_revision: int = Field(description='Current revision')
    last_polled_at: Union[datetime, None] = Field(default=None, description='Last polled at')
    next_poll_at: Union[datetime, None] = Field(default=None, description='Next poll at')
    running: bool = Field(default=False, description='Watcher running')
    my_role: str = Field(description='Current role')
    configured: bool = Field(description='Whether configured')


class TablePage(BaseModel):
    total: int = Field(description='Total items')
    page: int = Field(description='Current page')
    size: int = Field(description='Page size')
    items: list[TableIndex] = Field(default_factory=list, description='Items')


class DependencySnapshot(BaseModel):
    upstream: list[DependencyEdge] = Field(default_factory=list, description='Upstream dependencies')
    downstream: list[DependencyEdge] = Field(default_factory=list, description='Downstream dependencies')


class CodeSymbolReference(BaseModel):
    target_kind: Literal['table', 'field', 'symbol'] = Field(description='Reference kind')
    target_table: Optional[str] = Field(default=None, description='Target table')
    target_field: Optional[str] = Field(default=None, description='Target field')
    target_symbol: Optional[str] = Field(default=None, description='Target symbol')
    line: int = Field(description='Line number')
    snippet: str = Field(default='', description='Snippet')
    confidence: Literal['confirmed', 'inferred'] = Field(default='inferred', description='Confidence')


class CodeSymbol(BaseModel):
    name: str = Field(description='Symbol name')
    kind: Literal['class', 'interface', 'struct', 'enum', 'method', 'field', 'property'] = Field(description='Symbol kind')
    parent: Optional[str] = Field(default=None, description='Parent symbol')
    signature: str = Field(default='', description='Signature')
    line_start: int = Field(default=0, description='Start line')
    line_end: int = Field(default=0, description='End line')
    references: list[CodeSymbolReference] = Field(default_factory=list, description='Nested references')
    summary: str = Field(default='', description='Summary')


class CodeFileIndex(BaseModel):
    schema_version: Literal['code-index.v1'] = Field(default='code-index.v1')
    source_path: str = Field(description='Source path relative to svn_root')
    source_hash: str = Field(description='Source hash')
    svn_revision: int = Field(default=0, description='SVN revision')
    namespace: Optional[str] = Field(default=None, description='Namespace')
    using: list[str] = Field(default_factory=list, description='Using statements')
    symbols: list[CodeSymbol] = Field(default_factory=list, description='Symbols')
    references: list[CodeSymbolReference] = Field(default_factory=list, description='File references')
    last_indexed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description='Last indexed at')
    indexer_version: str = Field(default='regex.v1', description='Indexer version')


class KnowledgeIndexArtifact(BaseModel):
    path: str = Field(description='Relative release asset path')
    hash: Optional[str] = Field(default=None, description='Artifact hash')
    count: int = Field(default=0, description='Artifact record count')


KnowledgeStatus = Literal['active', 'deprecated', 'ignored']
ReleaseBuildMode = Literal['strict', 'bootstrap']
ReleaseBuildStatus = Literal['ready', 'bootstrap_warning']
ReleaseMapSource = Literal['provided', 'formal_map', 'current_release', 'bootstrap_current_indexes']
KnowledgeMapCandidateSource = Literal['release_snapshot', 'source_canonical']
MapDiffBaseSource = Literal['formal_map', 'current_release', 'none']


class KnowledgeSystem(BaseModel):
    schema_version: Literal['knowledge-system.v1'] = Field(default='knowledge-system.v1')
    system_id: str = Field(description='System identifier')
    title: str = Field(description='System title')
    description: Optional[str] = Field(default=None, description='System description')
    status: KnowledgeStatus = Field(default='active', description='Lifecycle status')
    table_ids: list[str] = Field(default_factory=list, description='Related table ids')
    doc_ids: list[str] = Field(default_factory=list, description='Related document ids')
    script_ids: list[str] = Field(default_factory=list, description='Related script ids')


class KnowledgeTableRef(BaseModel):
    schema_version: Literal['knowledge-table-ref.v1'] = Field(default='knowledge-table-ref.v1')
    table_id: str = Field(description='Table identifier')
    title: str = Field(description='Table title')
    source_path: str = Field(description='Relative local-project path')
    source_hash: str = Field(description='Source hash')
    system_id: Optional[str] = Field(default=None, description='Owning system id')
    status: KnowledgeStatus = Field(default='active', description='Lifecycle status')


class KnowledgeDocRef(BaseModel):
    schema_version: Literal['knowledge-doc-ref.v1'] = Field(default='knowledge-doc-ref.v1')
    doc_id: str = Field(description='Document identifier')
    title: str = Field(description='Document title')
    source_path: str = Field(description='Relative local-project path')
    source_hash: str = Field(description='Source hash')
    system_id: Optional[str] = Field(default=None, description='Owning system id')
    status: KnowledgeStatus = Field(default='active', description='Lifecycle status')


class KnowledgeScriptRef(BaseModel):
    schema_version: Literal['knowledge-script-ref.v1'] = Field(default='knowledge-script-ref.v1')
    script_id: str = Field(description='Script identifier')
    title: str = Field(description='Script title')
    source_path: str = Field(description='Relative local-project path')
    source_hash: str = Field(description='Source hash')
    system_id: Optional[str] = Field(default=None, description='Owning system id')
    status: KnowledgeStatus = Field(default='active', description='Lifecycle status')


class KnowledgeRelationship(BaseModel):
    schema_version: Literal['knowledge-relationship.v1'] = Field(default='knowledge-relationship.v1')
    relationship_id: str = Field(description='Relationship identifier')
    from_ref: str = Field(description='Source reference id')
    to_ref: str = Field(description='Target reference id')
    relation_type: str = Field(description='Relationship type')
    summary: Optional[str] = Field(default=None, description='Relationship summary')
    source_hash: str = Field(description='Relationship source hash')


class KnowledgeManifest(BaseModel):
    schema_version: Literal['knowledge-manifest.v1'] = Field(default='knowledge-manifest.v1')
    release_id: str = Field(description='Knowledge release id')
    created_at: datetime = Field(description='Creation time')
    created_by: Optional[str] = Field(default=None, description='Release creator')
    build_mode: ReleaseBuildMode = Field(default='strict', description='Release build mode used for this snapshot')
    status: ReleaseBuildStatus = Field(default='ready', description='Release build status marker')
    map_source: ReleaseMapSource = Field(default='provided', description='Knowledge map source used for release snapshot')
    warnings: list[str] = Field(default_factory=list, description='Build warnings that must be surfaced to callers')
    project_root_hash: Optional[str] = Field(default=None, description='Project root hash')
    source_snapshot: Optional[str] = Field(default=None, description='Legacy source snapshot')
    source_snapshot_hash: Optional[str] = Field(default=None, description='Stable source snapshot hash')
    map_hash: Optional[str] = Field(default=None, description='Map hash')
    indexes: dict[str, KnowledgeIndexArtifact] = Field(default_factory=dict, description='Index artifacts')
    systems: list[KnowledgeSystem] = Field(default_factory=list, description='Systems')
    tables: list[KnowledgeTableRef] = Field(default_factory=list, description='Tables')
    docs: list[KnowledgeDocRef] = Field(default_factory=list, description='Docs')
    scripts: list[KnowledgeScriptRef] = Field(default_factory=list, description='Scripts')


class KnowledgeMap(BaseModel):
    schema_version: Literal['knowledge-map.v1'] = Field(default='knowledge-map.v1')
    release_id: str = Field(description='Knowledge release id')
    systems: list[KnowledgeSystem] = Field(default_factory=list, description='Systems')
    tables: list[KnowledgeTableRef] = Field(default_factory=list, description='Tables')
    docs: list[KnowledgeDocRef] = Field(default_factory=list, description='Docs')
    scripts: list[KnowledgeScriptRef] = Field(default_factory=list, description='Scripts')
    relationships: list[KnowledgeRelationship] = Field(default_factory=list, description='Relationships')
    deprecated: list[str] = Field(default_factory=list, description='Deprecated refs')
    source_hash: Optional[str] = Field(default=None, description='Optional source hash')


class MapDiffReview(BaseModel):
    base_map_source: MapDiffBaseSource = Field(description='Review base map source')
    candidate_source: KnowledgeMapCandidateSource = Field(description='Candidate map source')
    added_refs: list[str] = Field(default_factory=list, description='References present only in candidate map')
    removed_refs: list[str] = Field(default_factory=list, description='References present only in base map')
    changed_refs: list[str] = Field(default_factory=list, description='References present in both maps but with changed lightweight metadata')
    unchanged_refs: list[str] = Field(default_factory=list, description='References present in both maps with unchanged lightweight metadata')
    warnings: list[str] = Field(default_factory=list, description='Review warnings')


class KnowledgeMapCandidateResult(BaseModel):
    mode: str = Field(default='candidate_map', description='Candidate response mode')
    map: KnowledgeMap | None = Field(default=None, description='Candidate knowledge map, if any')
    release_id: str | None = Field(default=None, description='Candidate map release id when applicable')
    candidate_source: KnowledgeMapCandidateSource = Field(description='Candidate map source marker')
    is_formal_map: bool = Field(default=False, description='Candidate maps are never formal maps')
    source_release_id: str | None = Field(default=None, description='Release id used for release snapshot candidates')
    uses_existing_formal_map_as_hint: bool | None = Field(default=None, description='Whether an existing formal map was used only as a hint')
    warnings: list[str] = Field(default_factory=list, description='Candidate build warnings')
    diff_review: MapDiffReview | None = Field(default=None, description='Optional lightweight diff review summary')


class KnowledgeReleasePointer(BaseModel):
    schema_version: Literal['knowledge-release-pointer.v1'] = Field(default='knowledge-release-pointer.v1')
    release_id: str = Field(description='Current knowledge release id')
    manifest_path: str = Field(default='manifest.json', description='Manifest relative path')
    map_path: str = Field(default='map.json', description='Map relative path')
    updated_at: datetime = Field(description='Last update time')


class WorkbenchTestPlanChange(BaseModel):
    operation: Literal['update_cell'] = Field(default='update_cell')
    table: str = Field(description='Table name')
    primary_key: dict[str, str] = Field(description='Primary key selector')
    field: str = Field(description='Field name')
    before: str = Field(description='Before value')
    after: str = Field(description='After value')
    source_path: str = Field(description='Path relative to the local project directory')


class WorkbenchTestPlan(BaseModel):
    schema_version: Literal['workbench-test-plan.v1'] = Field(default='workbench-test-plan.v1')
    id: str = Field(description='Test plan id')
    status: Literal['draft', 'testing', 'kept', 'discarded'] = Field(description='Plan status')
    title: str = Field(description='Plan title')
    project_key: Optional[str] = Field(default=None, description='Owning project key')
    release_scope: Optional[str] = Field(default=None, description='Release scope marker')
    test_scope: Optional[str] = Field(default=None, description='Test scope marker')
    source_refs: list[str] = Field(default_factory=list, description='Source paths relative to the local project directory')
    changes: list[WorkbenchTestPlanChange] = Field(default_factory=list, description='Planned changes')
    created_at: datetime = Field(description='Creation time')
    created_by: Optional[str] = Field(default=None, description='Creator')
    engine_test_ref: Optional[str] = Field(default=None, description='Engine test reference')


class ReleaseCandidate(BaseModel):
    schema_version: Literal['release-candidate.v1'] = Field(default='release-candidate.v1')
    candidate_id: str = Field(description='Release candidate id')
    test_plan_id: str = Field(description='Source test plan id')
    status: Literal['pending', 'accepted', 'rejected'] = Field(default='pending', description='Candidate status')
    title: str = Field(description='Candidate title')
    project_key: Optional[str] = Field(default=None, description='Owning project key')
    source_refs: list[str] = Field(default_factory=list, description='Source paths relative to the local project directory')
    source_hash: str = Field(description='Candidate source hash')
    selected: bool = Field(default=False, description='Selected for build')
    created_at: datetime = Field(description='Creation time')
