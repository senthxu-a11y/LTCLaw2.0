import type { KnowledgeRagCitation } from "../../api/types/game";

export interface CitationWorkbenchTarget {
  table: string | null;
  row: string | null;
  field: string | null;
  citationId: string;
  citationTitle: string | null;
  citationSource: string | null;
}

export interface CitationRouteContext {
  citationId: string;
  title: string;
  source: string;
  table: string;
  row: string;
  field: string;
}

function isLikelyWorkbenchSourcePath(value?: string | null): boolean {
  if (!value) {
    return false;
  }

  const normalized = value.replace(/\\/g, "/").trim().toLowerCase();
  return /\.(xlsx|xls|csv|tsv)$/.test(normalized);
}

export function normalizeWorkbenchTableName(value?: string | null): string | null {
  if (!value) {
    return null;
  }

  const normalized = value.replace(/\\/g, "/").trim();
  if (!normalized) {
    return null;
  }

  const tail = normalized.split("/").filter(Boolean).pop() || normalized;
  const withoutQuery = tail.split("?")[0]?.trim() || tail;
  const withoutExtension = withoutQuery.replace(/\.[^.]+$/, "").trim();
  return withoutExtension || null;
}

export function buildCitationWorkbenchTarget(citation: KnowledgeRagCitation): CitationWorkbenchTarget {
  const sourcePathTable = normalizeWorkbenchTableName(citation.source_path);
  const titleMatch = (citation.title || "").trim().match(/^([A-Za-z0-9_-]+)\.([A-Za-z0-9_:-]+)$/);
  const titleTable = titleMatch?.[1] || null;
  const titleField = titleMatch?.[2] || null;
  const sourceType = (citation.source_type || "").trim().toLowerCase();
  const canUseSourcePath = isLikelyWorkbenchSourcePath(citation.source_path);
  const canUseTitleField = sourceType.includes("table") || sourceType.includes("field");

  return {
    table:
      (typeof citation.table === "string" && citation.table.trim() ? citation.table.trim() : null) ||
      (canUseSourcePath ? sourcePathTable : null) ||
      (canUseTitleField ? titleTable : null),
    row: citation.row === null || citation.row === undefined ? null : String(citation.row),
    field:
      (typeof citation.field === "string" && citation.field.trim() ? citation.field.trim() : null) ||
      (canUseTitleField ? titleField : null),
    citationId: citation.citation_id,
    citationTitle: citation.title || null,
    citationSource: citation.source_path || citation.artifact_path || null,
  };
}

export function parseCitationRouteContext(searchParams: URLSearchParams): CitationRouteContext | null {
  const table = searchParams.get("table") || searchParams.get("tableId") || "";
  const row = searchParams.get("row") || searchParams.get("rowId") || "";
  const field = searchParams.get("field") || searchParams.get("fieldKey") || "";
  const hasDeepLink = Boolean(table || row || field);

  if (searchParams.get("from") !== "rag-citation" || !hasDeepLink) {
    return null;
  }

  const title = searchParams.get("citationTitle") || "";
  const source = searchParams.get("citationSource") || "";
  const citationId = searchParams.get("citationId") || "";
  if (!title && !source && !citationId && !table && !row && !field) {
    return null;
  }

  return {
    citationId,
    title,
    source,
    table,
    row,
    field,
  };
}
