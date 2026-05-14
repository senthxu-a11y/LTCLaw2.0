import type { FrontendCapability, FrontendCapabilityToken } from "../../../api/types/permissions";
import type {
  FormalKnowledgeMapResponse,
  GameStorageSummary,
  KnowledgeReleaseHistoryItem,
} from "../../../api/types/game";

export interface AdminStatusCard {
  key:
    | "project_bundle_path"
    | "source_config_path"
    | "current_release_id"
    | "current_map_hash"
    | "formal_map_status"
    | "rag_status"
    | "current_knowledge_version";
  label: string;
  value: string;
  tone: "default" | "success" | "warning";
}

export interface AdminActionDescriptor {
  key:
    | "candidate_map_review"
    | "save_formal_map"
    | "build_release"
    | "publish_set_current";
  label: string;
  path: string;
  requiredCapabilities: FrontendCapability[];
  enabled: boolean;
}

export interface AdminPanelStatusInput {
  storageSummary: GameStorageSummary | null;
  currentRelease: KnowledgeReleaseHistoryItem | null;
  formalMap: FormalKnowledgeMapResponse | null;
  ragStatus: string;
}

const ADMIN_CAPABILITIES: FrontendCapability[] = [
  "knowledge.build",
  "knowledge.publish",
  "knowledge.map.read",
  "knowledge.map.edit",
  "knowledge.candidate.read",
  "knowledge.candidate.write",
];

function hasCapability(
  capabilities: readonly FrontendCapabilityToken[] | null | undefined,
  capability: FrontendCapability,
): boolean {
  if (capabilities == null) {
    return true;
  }
  return capabilities.includes("*") || capabilities.includes(capability);
}

export function hasAnyAdminCapability(
  capabilities: readonly FrontendCapabilityToken[] | null | undefined,
  hasExplicitCapabilityContext: boolean,
): boolean {
  if (!hasExplicitCapabilityContext) {
    return true;
  }
  return ADMIN_CAPABILITIES.some((capability) => hasCapability(capabilities, capability));
}

export function buildAdminPanelActions(
  capabilities: readonly FrontendCapabilityToken[] | null | undefined,
  hasExplicitCapabilityContext: boolean,
): AdminActionDescriptor[] {
  if (!hasAnyAdminCapability(capabilities, hasExplicitCapabilityContext)) {
    return [];
  }

  const actions: Array<Omit<AdminActionDescriptor, "enabled">> = [
    {
      key: "candidate_map_review",
      label: "Candidate Map Review / Map Diff Review",
      path: "/game/map",
      requiredCapabilities: ["knowledge.candidate.read", "knowledge.candidate.write", "knowledge.map.read"],
    },
    {
      key: "save_formal_map",
      label: "Save Formal Map",
      path: "/game/map",
      requiredCapabilities: ["knowledge.map.read", "knowledge.map.edit"],
    },
    {
      key: "build_release",
      label: "Build Release",
      path: "/game/knowledge",
      requiredCapabilities: ["knowledge.build"],
    },
    {
      key: "publish_set_current",
      label: "Publish / Set Current",
      path: "/game/knowledge",
      requiredCapabilities: ["knowledge.publish"],
    },
  ];

  return actions.map((action) => ({
    ...action,
    enabled: action.requiredCapabilities.every((capability) => hasCapability(capabilities, capability)),
  }));
}

export function buildAdminStatusCards(input: AdminPanelStatusInput): AdminStatusCard[] {
  const bundlePath = input.storageSummary?.project_bundle_root || input.storageSummary?.project_store_dir || "-";
  const sourceConfigPath = input.storageSummary?.project_source_config_path || "-";
  const currentReleaseId = input.currentRelease?.release_id || "-";
  const formalMode = input.formalMap?.mode || "unavailable";
  const mapHash = input.formalMap?.map_hash || "-";
  const currentKnowledgeVersion = input.currentRelease?.release_id || "-";

  return [
    {
      key: "project_bundle_path",
      label: "Project bundle path",
      value: bundlePath,
      tone: bundlePath === "-" ? "warning" : "default",
    },
    {
      key: "source_config_path",
      label: "Source config path",
      value: sourceConfigPath,
      tone: sourceConfigPath === "-" ? "warning" : "default",
    },
    {
      key: "current_release_id",
      label: "Current Release ID",
      value: currentReleaseId,
      tone: currentReleaseId === "-" ? "warning" : "success",
    },
    {
      key: "current_map_hash",
      label: "Current Map hash",
      value: mapHash,
      tone: mapHash === "-" ? "warning" : "success",
    },
    {
      key: "formal_map_status",
      label: "Formal Map status",
      value: formalMode,
      tone: formalMode === "formal_map" || formalMode === "formal_map_saved" ? "success" : "warning",
    },
    {
      key: "rag_status",
      label: "RAG status",
      value: input.ragStatus,
      tone: input.ragStatus === "ready" ? "success" : "warning",
    },
    {
      key: "current_knowledge_version",
      label: "Current knowledge version",
      value: currentKnowledgeVersion,
      tone: currentKnowledgeVersion === "-" ? "warning" : "success",
    },
  ];
}