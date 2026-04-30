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
};
