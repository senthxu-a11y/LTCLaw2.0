import type { KnowledgeRagAnswerResponse, KnowledgeRagCitation } from "../../api/types/game";

export interface RecentRagQuestionItem {
  query: string;
  mode: KnowledgeRagAnswerResponse["mode"];
  askedAt: number;
}

export interface RagCitationGroup {
  key: string;
  label: string;
  citations: KnowledgeRagCitation[];
}

export const STRUCTURED_FACT_WARNING = "For exact numeric or row-level facts, use the structured query flow.";
export const CHANGE_QUERY_WARNING = "For change proposals or edits, use the workbench flow.";

const INSUFFICIENT_CONTEXT_NEXT_STEP_HINT_KEYS = [
  "gameProject.ragNextStepHintNarrowCurrentRelease",
  "gameProject.ragNextStepHintUseStructuredQuery",
  "gameProject.ragNextStepHintUseWorkbench",
  "gameProject.ragNextStepHintCheckReleaseEvidence",
];

export function formatCitationValue(value?: string | number | null): string {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  return String(value);
}

export function buildRecentRagQuestions(
  current: RecentRagQuestionItem[],
  query: string,
  mode: KnowledgeRagAnswerResponse["mode"],
  now: number,
  limit: number,
): RecentRagQuestionItem[] {
  const normalizedQuery = query.trim();
  if (!normalizedQuery) {
    return current;
  }

  const nextItem: RecentRagQuestionItem = {
    query: normalizedQuery,
    mode,
    askedAt: now,
  };

  return [nextItem, ...current.filter((item) => item.query !== normalizedQuery)].slice(0, limit);
}

export function buildCopyableRagText(answer: KnowledgeRagAnswerResponse): string {
  const lines = [
    `mode: ${answer.mode}`,
    `release_id: ${answer.release_id || "-"}`,
  ];

  if (answer.answer) {
    lines.push("", "Answer:", answer.answer);
  }

  if (answer.warnings.length > 0) {
    lines.push("", "Warnings:", ...answer.warnings.map((warning) => `- ${warning}`));
  }

  if (answer.citations.length > 0) {
    lines.push(
      "",
      "Citations:",
      ...answer.citations.map((citation) => {
        const label = citation.title || citation.citation_id;
        return [
          `- ${label}`,
          `  source_path: ${formatCitationValue(citation.source_path)}`,
          `  artifact_path: ${formatCitationValue(citation.artifact_path)}`,
          `  row: ${formatCitationValue(citation.row)}`,
          `  release_id: ${formatCitationValue(citation.release_id)}`,
        ].join("\n");
      }),
    );
  }

  return lines.join("\n");
}

export function getRagDisplayState(answer: KnowledgeRagAnswerResponse): KnowledgeRagAnswerResponse["mode"] {
  if (answer.mode === "no_current_release") {
    return "no_current_release";
  }
  if (answer.mode === "insufficient_context") {
    return "insufficient_context";
  }
  return "answer";
}

export function getRagNextStepHintKeys(answer: KnowledgeRagAnswerResponse): string[] {
  if (getRagDisplayState(answer) !== "insufficient_context") {
    return [];
  }
  return INSUFFICIENT_CONTEXT_NEXT_STEP_HINT_KEYS;
}

export function groupRagCitations(citations: KnowledgeRagCitation[]): RagCitationGroup[] {
  const groups = new Map<string, RagCitationGroup>();

  for (const citation of citations) {
    const normalizedSourceType = String(citation.source_type || "").trim();
    const groupKey = normalizedSourceType || "other";
    const existingGroup = groups.get(groupKey);

    if (existingGroup) {
      existingGroup.citations.push(citation);
      continue;
    }

    groups.set(groupKey, {
      key: groupKey,
      label: normalizedSourceType || "other",
      citations: [citation],
    });
  }

  return Array.from(groups.values()).map((group) => ({
    ...group,
    citations: [...group.citations].sort((left, right) => {
      const leftSourcePath = formatCitationValue(left.source_path);
      const rightSourcePath = formatCitationValue(right.source_path);
      if (leftSourcePath !== rightSourcePath) {
        return leftSourcePath.localeCompare(rightSourcePath);
      }

      const leftRow = left.row ?? Number.MAX_SAFE_INTEGER;
      const rightRow = right.row ?? Number.MAX_SAFE_INTEGER;
      if (leftRow !== rightRow) {
        return leftRow - rightRow;
      }

      const leftTitle = formatCitationValue(left.title || left.citation_id);
      const rightTitle = formatCitationValue(right.title || right.citation_id);
      if (leftTitle !== rightTitle) {
        return leftTitle.localeCompare(rightTitle);
      }

      return left.citation_id.localeCompare(right.citation_id);
    }),
  }));
}

export function isStructuredOrWorkbenchWarning(warning: string): boolean {
  return warning === STRUCTURED_FACT_WARNING || warning === CHANGE_QUERY_WARNING;
}