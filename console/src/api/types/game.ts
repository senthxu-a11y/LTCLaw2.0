export interface ProjectMeta {
  name: string;
  engine: string;
  language: string;
}

export interface SvnConfig {
  root: string;
  poll_interval_seconds: number;
  jitter_seconds: number;
}

export interface PathRule {
  path: string;
  semantic: "table" | "doc" | "template";
  system?: string | null;
}

export interface FilterConfig {
  include_ext: string[];
  exclude_glob: string[];
}

export interface IDRange {
  type: string;
  start: number;
  end: number;
}

export interface TableConvention {
  header_row: number;
  comment_row?: number | null;
  primary_key_field: string;
  id_ranges: IDRange[];
}

export interface ModelSlotRef {
  provider_id: string;
  model_id: string;
}

export interface ProjectConfig {
  schema_version?: "project-config.v1";
  project: ProjectMeta;
  svn: SvnConfig;
  paths: PathRule[];
  filters: FilterConfig;
  table_convention: TableConvention;
  doc_templates: Record<string, string>;
  models: Record<string, ModelSlotRef>;
}

export interface UserGameConfig {
  my_role: "maintainer" | "consumer";
  svn_local_root?: string | null;
  svn_url?: string | null;
  svn_username?: string | null;
  svn_password?: string | null;
  svn_trust_cert?: boolean;
}

export interface GameStorageSummary {
  working_root: string;
  game_data_root: string;
  workspace_dir: string;
  user_config_path: string;
  legacy_user_config_path: string;
  svn_root?: string | null;
  project_store_dir?: string | null;
  project_config_path?: string | null;
  project_index_dir?: string | null;
  agent_store_dir: string;
  session_store_dir: string;
  workbench_dir: string;
  chroma_dir: string;
  llm_cache_dir: string;
  svn_cache_dir: string;
  proposals_dir: string;
  code_index_dir: string;
  retrieval_dir: string;
  knowledge_base_dir: string;
  session_name: string;
}

export interface ValidationIssue {
  severity: "error" | "warning";
  path: string;
  message: string;
}

export interface CommitResult {
  revision?: number | null;
  files_committed: number;
  skipped_reason?: string | null;
}

export interface KnowledgeIndexArtifact {
  path: string;
  hash?: string | null;
  count: number;
}

export interface KnowledgeManifest {
  schema_version?: "knowledge-manifest.v1";
  release_id: string;
  created_at: string;
  created_by?: string | null;
  project_root_hash?: string | null;
  source_snapshot?: string | null;
  source_snapshot_hash?: string | null;
  map_hash?: string | null;
  indexes: Record<string, KnowledgeIndexArtifact>;
}

export interface KnowledgeReleasePointer {
  schema_version?: "knowledge-release-pointer.v1";
  release_id: string;
  manifest_path: string;
  map_path: string;
  updated_at: string;
}

export type KnowledgeStatus = "active" | "deprecated" | "ignored";

export interface KnowledgeSystem {
  schema_version?: "knowledge-system.v1";
  system_id: string;
  title: string;
  description?: string | null;
  status: KnowledgeStatus;
  table_ids: string[];
  doc_ids: string[];
  script_ids: string[];
}

export interface KnowledgeTableRef {
  schema_version?: "knowledge-table-ref.v1";
  table_id: string;
  title: string;
  source_path: string;
  source_hash: string;
  system_id?: string | null;
  status: KnowledgeStatus;
}

export interface KnowledgeDocRef {
  schema_version?: "knowledge-doc-ref.v1";
  doc_id: string;
  title: string;
  source_path: string;
  source_hash: string;
  system_id?: string | null;
  status: KnowledgeStatus;
}

export interface KnowledgeScriptRef {
  schema_version?: "knowledge-script-ref.v1";
  script_id: string;
  title: string;
  source_path: string;
  source_hash: string;
  system_id?: string | null;
  status: KnowledgeStatus;
}

export interface KnowledgeRelationship {
  schema_version?: "knowledge-relationship.v1";
  relationship_id: string;
  from_ref: string;
  to_ref: string;
  relation_type: string;
  summary?: string | null;
  source_hash: string;
}

export interface KnowledgeMap {
  schema_version?: "knowledge-map.v1";
  release_id: string;
  systems: KnowledgeSystem[];
  tables: KnowledgeTableRef[];
  docs: KnowledgeDocRef[];
  scripts: KnowledgeScriptRef[];
  relationships: KnowledgeRelationship[];
  deprecated: string[];
  source_hash?: string | null;
}

export interface KnowledgeMapCandidateResponse {
  mode: "candidate_map";
  map: KnowledgeMap | null;
  release_id: string | null;
}

export interface FormalKnowledgeMapResponse {
  mode: "no_formal_map" | "formal_map" | "formal_map_saved";
  map: KnowledgeMap | null;
  map_hash: string | null;
  updated_at: string | null;
  updated_by: string | null;
}

export interface ReleaseCandidateListItem {
  candidate_id: string;
  test_plan_id: string;
  title: string;
  status: "pending" | "accepted" | "rejected";
  selected: boolean;
  source_refs: string[];
  created_at: string;
}

export interface KnowledgeRagCitation {
  citation_id: string;
  release_id?: string | null;
  source_type?: string | null;
  artifact_path?: string | null;
  source_path?: string | null;
  title?: string | null;
  row?: number | null;
}

export interface KnowledgeRagAnswerResponse {
  mode: "answer" | "no_current_release" | "insufficient_context";
  answer: string;
  release_id: string | null;
  citations: KnowledgeRagCitation[];
  warnings: string[];
}

export type FieldConfidence = "confirmed" | "high_ai" | "low_ai";

export interface FieldInfo {
  name: string;
  type: string;
  description: string;
  confidence: FieldConfidence;
  confirmed_by?: string | null;
  confirmed_at?: string | null;
  ai_raw_description?: string | null;
  references: string[];
  tags: string[];
}

export interface FieldPatch {
  description?: string | null;
  confidence?: FieldConfidence | null;
  confirmed_by?: string | null;
}

export interface TableIndex {
  schema_version?: "table-index.v1";
  table_name: string;
  source_path: string;
  source_hash: string;
  svn_revision: number;
  system?: string | null;
  row_count: number;
  header_row: number;
  primary_key: string;
  ai_summary: string;
  ai_summary_confidence: number;
  fields: FieldInfo[];
  id_ranges: Array<Record<string, unknown>>;
  last_indexed_at: string;
  indexer_model: string;
}

export type StructuredQueryResultMode = "exact_table" | "exact_field" | "semantic_stub" | "not_configured" | "unknown";

export type StructuredQueryStatus = "success" | "empty" | "unavailable" | "error";

export interface StructuredQueryRequest {
  query: string;
}

export interface StructuredQueryTableItem {
  kind: "table";
  table_name: string;
  source_path: string;
  system?: string | null;
  row_count: number;
  primary_key: string;
  summary?: string | null;
}

export interface StructuredQueryFieldItem {
  kind: "field";
  table_name: string;
  field_name: string;
  field_type: string;
  description?: string | null;
  confidence: FieldConfidence;
  references: string[];
  tags: string[];
}

export type StructuredQueryItem = StructuredQueryTableItem | StructuredQueryFieldItem;

export interface StructuredQueryResponse {
  query: string;
  request_mode: "auto";
  result_mode: StructuredQueryResultMode;
  status: StructuredQueryStatus;
  message: string | null;
  warnings: string[];
  items: StructuredQueryItem[];
  error: string | null;
}

export interface SystemGroup {
  name: string;
  tables: string[];
  description?: string | null;
  source: "config" | "ai" | "manual";
}

export interface ChangeSet {
  from_rev: number;
  to_rev: number;
  added: string[];
  modified: string[];
  deleted: string[];
}

export interface SvnWatcherStats {
  check_count: number;
  change_count: number;
  error_count: number;
}

export interface SvnStatusResponse {
  configured: boolean;
  running: boolean;
  poll_interval?: number;
  watch_paths?: string[];
  last_checked_revision?: number | null;
  last_check_time?: string | null;
  uptime_seconds?: number | null;
  stats?: SvnWatcherStats;
  has_callback?: boolean;
  my_role?: "maintainer" | "consumer";
  current_rev?: number | null;
  last_polled_at?: string | null;
  next_poll_at?: string | null;
}

export interface RecentSvnChangeItem {
  id: string;
  revision: number;
  from_rev?: number;
  author: string;
  timestamp: string;
  message: string;
  paths: string[];
  action: "A" | "M" | "D";
}

export interface RecentSvnChangesResponse {
  items: RecentSvnChangeItem[];
  count: number;
}

export interface DependencyItem {
  table: string;
  field: string;
  target_field?: string;
  source_field?: string;
  confidence: number;
}

export interface DependenciesResponse {
  upstream: DependencyItem[];
  downstream: DependencyItem[];
}

export interface PaginatedTableIndexesResponse {
  items: TableIndex[];
  total: number;
  page: number;
  size: number;
  error?: string;
}
