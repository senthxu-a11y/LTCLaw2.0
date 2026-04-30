import { request } from "../request";

export interface FieldChange {
  table: string;
  row_id: string | number;
  field: string;
  new_value: unknown;
}

export interface PreviewItem {
  table: string;
  row_id: string | number;
  field: string;
  old_value: unknown;
  new_value: unknown;
  ok: boolean;
  error?: string | null;
}

export interface PreviewResponse {
  items: PreviewItem[];
}

export interface SuggestChange {
  table: string;
  row_id: string | number;
  field: string;
  new_value: unknown;
  reason?: string;
}

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

export interface SuggestContextSummary {
  main_tables?: string[];
  related_tables?: string[];
  matched_columns?: Record<string, string[]>;
  query_terms?: string[];
}

export interface SuggestResponse {
  message: string;
  changes: SuggestChange[];
  raw?: string;
  context_summary?: SuggestContextSummary;
}

// ---- AI Suggestion Panel (规则化结构化建议) ---------------------------

export interface AvailableIdRange {
  type: string;
  start: number;
  end: number;
  actual_min: number | null;
  actual_max: number | null;
  used_count: number;
  next_available: number | null;
  remaining: number;
}

export interface NumericStats {
  count: number;
  min: number;
  max: number;
  avg: number;
  p25: number;
  p50: number;
  p75: number;
}

export interface ReferenceSample {
  id: string | number | null;
  name?: string | number | null;
  value: number;
}

export interface ReusableResource {
  from_table: string;
  from_field: string;
  to_field: string;
  confidence: string;
  inferred_by: string;
}

export interface PendingConfirmField {
  name: string;
  type: string;
  confidence: string;
  description: string;
}

export interface AiSuggestPanelResponse {
  table: string;
  field: string | null;
  field_meta: {
    name: string;
    type: string;
    confidence: string;
    description: string;
  } | null;
  primary_key: string;
  available_ids: AvailableIdRange[];
  numeric_stats: NumericStats | null;
  suggested_range: [number, number] | null;
  samples: ReferenceSample[];
  reusable_resources: ReusableResource[];
  pending_confirms: PendingConfirmField[];
  summary: string;
}

// ---- Workbench Context (多表打包上下文) -------------------------------

export interface WorkbenchContextField {
  key: string;
  label: string;
  type?: string;
  description?: string;
}

export interface WorkbenchContextRecord {
  id: string | number;
  fields: { key: string; value: unknown }[];
}

export interface WorkbenchContextTable {
  tableId: string;
  tableName: string;
  system: string | null;
  primaryKey: string;
  fields: WorkbenchContextField[];
  records: WorkbenchContextRecord[];
  rowCount: number;
}

export interface WorkbenchContextResponse {
  tables: WorkbenchContextTable[];
  focusField: { table: string; field: string } | null;
}

// ---- DamageChain (伤害链路 Phase-1 stub) ------------------------------

export interface DamageVariable {
  name: string;
  value: number;
  sourceTable: string;
  isChanged: boolean;
}

export interface DamageChainResponse {
  formula: string;
  variables: DamageVariable[];
  resultBefore: number;
  resultAfter: number;
  deltaPercent: number;
}

export interface DamageChainRequest {
  formulaKey?: string;
  changes: FieldChange[];
}

export const gameWorkbenchApi = {
  preview(agentId: string, changes: FieldChange[]) {
    return request<PreviewResponse>(
      `/agents/${agentId}/game/workbench/preview`,
      {
        method: "POST",
        body: JSON.stringify({ changes }),
      },
    );
  },
  suggest(
    agentId: string,
    user_intent: string,
    context_tables: string[],
    current_pending: FieldChange[],
    chat_history: ChatTurn[] = [],
  ) {
    return request<SuggestResponse>(
      `/agents/${agentId}/game/workbench/suggest`,
      {
        method: "POST",
        body: JSON.stringify({
          user_intent,
          context_tables,
          current_pending,
          chat_history,
        }),
      },
    );
  },
  aiSuggestPanel(agentId: string, table: string, field?: string) {
    const qs = new URLSearchParams({ table });
    if (field) qs.set("field", field);
    return request<AiSuggestPanelResponse>(
      `/agents/${agentId}/game/workbench/ai-suggest?${qs.toString()}`,
      { method: "GET" },
    );
  },
  context(
    agentId: string,
    opts: {
      tableIds: string[];
      focusTable?: string;
      focusField?: string;
      limitPerTable?: number;
    },
  ) {
    const qs = new URLSearchParams();
    for (const t of opts.tableIds) qs.append("tableIds", t);
    if (opts.focusTable) qs.set("focusTable", opts.focusTable);
    if (opts.focusField) qs.set("focusField", opts.focusField);
    if (opts.limitPerTable != null)
      qs.set("limitPerTable", String(opts.limitPerTable));
    return request<WorkbenchContextResponse>(
      `/agents/${agentId}/game/workbench/context?${qs.toString()}`,
      { method: "GET" },
    );
  },
  damageChain(agentId: string, body: DamageChainRequest) {
    return request<DamageChainResponse>(
      `/agents/${agentId}/game/workbench/damage-chain`,
      {
        method: "POST",
        body: JSON.stringify({
          formulaKey: body.formulaKey ?? "default",
          changes: body.changes,
        }),
      },
    );
  },
};
