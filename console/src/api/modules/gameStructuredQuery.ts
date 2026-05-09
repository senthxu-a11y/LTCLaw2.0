import { request } from '../request';
import type {
  FieldConfidence,
  StructuredQueryItem,
  StructuredQueryResponse,
  StructuredQueryResultMode,
  StructuredQueryTableItem,
} from '../types/game';

type RawStructuredQueryMode = Exclude<StructuredQueryResultMode, 'unknown'>;

interface RawStructuredQueryResponse {
  mode?: unknown;
  results?: unknown;
}

const KNOWN_MODES: RawStructuredQueryMode[] = ['exact_table', 'exact_field', 'semantic_stub', 'not_configured'];
const FALLBACK_FIELD_CONFIDENCE: FieldConfidence = 'low_ai';

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}

function isKnownMode(value: unknown): value is RawStructuredQueryMode {
  return typeof value === 'string' && KNOWN_MODES.includes(value as RawStructuredQueryMode);
}

function toStringOrNull(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value : null;
}

function toStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === 'string' && item.trim().length > 0);
}

function toNumber(value: unknown, fallback: number = 0): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function toFieldConfidence(value: unknown): FieldConfidence {
  return value === 'confirmed' || value === 'high_ai' || value === 'low_ai' ? value : FALLBACK_FIELD_CONFIDENCE;
}

function normalizeTableItem(value: unknown): StructuredQueryTableItem | null {
  if (!isRecord(value)) {
    return null;
  }

  const tableName = toStringOrNull(value.table_name);
  const sourcePath = toStringOrNull(value.source_path);
  const primaryKey = toStringOrNull(value.primary_key);

  if (!tableName || !sourcePath || !primaryKey) {
    return null;
  }

  return {
    kind: 'table',
    table_name: tableName,
    source_path: sourcePath,
    system: toStringOrNull(value.system),
    row_count: toNumber(value.row_count),
    primary_key: primaryKey,
    summary: toStringOrNull(value.ai_summary),
  };
}

function normalizeFieldItem(value: unknown): StructuredQueryItem | null {
  if (!isRecord(value)) {
    return null;
  }

  const tableName = toStringOrNull(value.table);
  const fieldValue = isRecord(value.field) ? value.field : null;
  const fieldName = fieldValue ? toStringOrNull(fieldValue.name) : null;
  const fieldType = fieldValue ? toStringOrNull(fieldValue.type) : null;

  if (!tableName || !fieldValue || !fieldName || !fieldType) {
    return null;
  }

  return {
    kind: 'field',
    table_name: tableName,
    field_name: fieldName,
    field_type: fieldType,
    description: toStringOrNull(fieldValue.description),
    confidence: toFieldConfidence(fieldValue.confidence),
    references: toStringArray(fieldValue.references),
    tags: toStringArray(fieldValue.tags),
  };
}

function normalizeItems(mode: StructuredQueryResultMode, results: unknown): StructuredQueryItem[] {
  if (!Array.isArray(results)) {
    return [];
  }

  if (mode === 'exact_table') {
    return results.map(normalizeTableItem).filter((item): item is StructuredQueryTableItem => item !== null);
  }

  if (mode === 'exact_field') {
    return results.map(normalizeFieldItem).filter((item): item is StructuredQueryItem => item !== null);
  }

  return [];
}

function buildNormalizedResponse(
  query: string,
  resultMode: StructuredQueryResultMode,
  items: StructuredQueryItem[],
): StructuredQueryResponse {
  if (resultMode === 'exact_table') {
    return {
      query,
      request_mode: 'auto',
      result_mode: resultMode,
      status: items.length > 0 ? 'success' : 'empty',
      message: items.length > 0 ? 'Showing exact table matches from the current structured index.' : 'No exact table matches were returned for this query.',
      warnings: [],
      items,
      error: null,
    };
  }

  if (resultMode === 'exact_field') {
    return {
      query,
      request_mode: 'auto',
      result_mode: resultMode,
      status: items.length > 0 ? 'success' : 'empty',
      message: items.length > 0 ? 'Showing exact field matches from the current structured index.' : 'No exact field matches were returned for this query.',
      warnings: [],
      items,
      error: null,
    };
  }

  if (resultMode === 'semantic_stub') {
    return {
      query,
      request_mode: 'auto',
      result_mode: resultMode,
      status: 'empty',
      message: 'No exact structured result was found for this query.',
      warnings: [],
      items: [],
      error: null,
    };
  }

  if (resultMode === 'not_configured') {
    return {
      query,
      request_mode: 'auto',
      result_mode: resultMode,
      status: 'unavailable',
      message: 'Structured query is unavailable because the current project index is not configured.',
      warnings: [],
      items: [],
      error: null,
    };
  }

  return {
    query,
    request_mode: 'auto',
    result_mode: 'unknown',
    status: 'error',
    message: 'Structured query returned an unsupported response.',
    warnings: [],
    items: [],
    error: 'Structured query returned an unsupported response.',
  };
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Structured query failed.';
}

export const gameStructuredQueryApi = {
  async submit(agentId: string, query: string): Promise<StructuredQueryResponse> {
    try {
      const response = await request<RawStructuredQueryResponse>(`/agents/${agentId}/game/index/query`, {
        method: 'POST',
        body: JSON.stringify({ q: query, mode: 'auto' }),
      });

      const resultMode: StructuredQueryResultMode = isKnownMode(response?.mode) ? response.mode : 'unknown';
      const items = normalizeItems(resultMode, response?.results);
      return buildNormalizedResponse(query, resultMode, items);
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      return {
        query,
        request_mode: 'auto',
        result_mode: 'unknown',
        status: 'error',
        message: errorMessage,
        warnings: [],
        items: [],
        error: errorMessage,
      };
    }
  },
};