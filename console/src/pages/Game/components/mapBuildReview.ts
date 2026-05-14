import type {
  FormalKnowledgeMapResponse,
  KnowledgeMap,
  KnowledgeMapCandidateResponse,
  MapDiffReview,
} from "../../../api/types/game";

export const NO_FORMAL_MAP_MODE = "no_formal_map";

export interface KnowledgeMapSummary {
  systems: number;
  tables: number;
  docs: number;
  scripts: number;
  relationships: number;
}

export interface MapBuildArtifactState {
  key: "candidate" | "formal" | "release";
  source: string;
  status: "available" | "missing" | "not_built";
  summary: KnowledgeMapSummary;
}

export interface DiffReviewSection {
  key: "added_refs" | "removed_refs" | "changed_refs" | "unchanged_refs";
  refs: string[];
}

export function summarizeKnowledgeMap(map: KnowledgeMap | null): KnowledgeMapSummary {
  return {
    systems: map?.systems.length ?? 0,
    tables: map?.tables.length ?? 0,
    docs: map?.docs.length ?? 0,
    scripts: map?.scripts.length ?? 0,
    relationships: map?.relationships.length ?? 0,
  };
}

export function buildMapBuildArtifactStates(options: {
  sourceCandidate: KnowledgeMapCandidateResponse | null;
  formalMap: FormalKnowledgeMapResponse | null;
  releaseSnapshot: KnowledgeMapCandidateResponse | null;
}): MapBuildArtifactState[] {
  const savedFormalMap = options.formalMap?.mode === NO_FORMAL_MAP_MODE ? null : options.formalMap?.map ?? null;
  return [
    {
      key: "candidate",
      source: options.sourceCandidate?.candidate_source ?? "source_canonical",
      status: options.sourceCandidate?.map
        ? "available"
        : options.sourceCandidate
          ? "missing"
          : "not_built",
      summary: summarizeKnowledgeMap(options.sourceCandidate?.map ?? null),
    },
    {
      key: "formal",
      source: "formal_map",
      status: savedFormalMap ? "available" : "missing",
      summary: summarizeKnowledgeMap(savedFormalMap),
    },
    {
      key: "release",
      source: options.releaseSnapshot?.candidate_source ?? "release_snapshot",
      status: options.releaseSnapshot?.map ? "available" : "missing",
      summary: summarizeKnowledgeMap(options.releaseSnapshot?.map ?? null),
    },
  ];
}

export function canSaveReviewedCandidateAsFormalMap(options: {
  agentId: string | null | undefined;
  sourceCandidate: KnowledgeMapCandidateResponse | null;
  hasExplicitCapabilityContext: boolean;
  canReadMap: boolean;
  canEditMap: boolean;
}): boolean {
  if (!options.agentId || !options.sourceCandidate?.map) {
    return false;
  }
  if (!options.hasExplicitCapabilityContext) {
    return true;
  }
  return options.canReadMap && options.canEditMap;
}

export function buildDiffReviewSections(review: MapDiffReview | null | undefined): DiffReviewSection[] {
  return [
    { key: "added_refs", refs: review?.added_refs ?? [] },
    { key: "removed_refs", refs: review?.removed_refs ?? [] },
    { key: "changed_refs", refs: review?.changed_refs ?? [] },
    { key: "unchanged_refs", refs: review?.unchanged_refs ?? [] },
  ];
}