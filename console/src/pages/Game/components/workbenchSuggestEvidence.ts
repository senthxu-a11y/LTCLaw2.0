import type { SuggestChange } from "../../../api/modules/gameWorkbench";

export interface WorkbenchSuggestMeta {
  evidence_refs?: string[];
  formal_context_status?: string;
}

export type SuggestEvidenceKind = "formal" | "runtime_only";

export interface SuggestEvidencePresentation {
  evidenceRefs: string[];
  confidenceText: string | null;
  validationStatus: string | null;
  sourceReleaseId: string | null;
  usesDraftOverlay: boolean;
  formalContextStatus: string | null;
  evidenceKind: SuggestEvidenceKind;
}

export interface SuggestMessagePresentation {
  evidenceRefs: string[];
  sourceReleaseId: string | null;
  usesDraftOverlay: boolean;
  formalContextStatus: string | null;
  hasFormalEvidence: boolean;
  hasRuntimeOnlySuggestion: boolean;
}

export function dedupeEvidenceRefs(refs: string[] | null | undefined): string[] {
  const seen = new Set<string>();
  const deduped: string[] = [];
  for (const ref of refs || []) {
    const normalized = String(ref || "").trim();
    if (!normalized || seen.has(normalized)) {
      continue;
    }
    seen.add(normalized);
    deduped.push(normalized);
  }
  return deduped;
}

export function formatSuggestConfidence(value: number | null | undefined): string | null {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return null;
  }
  const normalized = Math.max(0, Math.min(1, value));
  return `${Math.round(normalized * 100)}%`;
}

export function buildSuggestionEvidencePresentation(
  change: SuggestChange,
  meta?: WorkbenchSuggestMeta,
): SuggestEvidencePresentation {
  const evidenceRefs = dedupeEvidenceRefs(change.evidence_refs);
  return {
    evidenceRefs,
    confidenceText: formatSuggestConfidence(change.confidence),
    validationStatus: change.validation_status?.trim() || null,
    sourceReleaseId: change.source_release_id?.trim() || null,
    usesDraftOverlay: Boolean(change.uses_draft_overlay),
    formalContextStatus: meta?.formal_context_status?.trim() || null,
    evidenceKind: evidenceRefs.length > 0 ? "formal" : "runtime_only",
  };
}

export function buildSuggestMessagePresentation(
  suggestions: SuggestChange[] | undefined,
  meta?: WorkbenchSuggestMeta,
): SuggestMessagePresentation {
  const items = suggestions || [];
  const evidenceRefs = dedupeEvidenceRefs([
    ...(meta?.evidence_refs || []),
    ...items.flatMap((item) => item.evidence_refs || []),
  ]);
  const sourceReleaseIds = items
    .map((item) => item.source_release_id?.trim() || "")
    .filter(Boolean);
  return {
    evidenceRefs,
    sourceReleaseId: sourceReleaseIds[0] || null,
    usesDraftOverlay: items.some((item) => Boolean(item.uses_draft_overlay)),
    formalContextStatus: meta?.formal_context_status?.trim() || null,
    hasFormalEvidence: evidenceRefs.length > 0,
    hasRuntimeOnlySuggestion: items.some((item) => dedupeEvidenceRefs(item.evidence_refs).length === 0),
  };
}