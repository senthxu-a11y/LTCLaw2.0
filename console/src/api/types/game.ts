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
  svn_username?: string | null;
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
