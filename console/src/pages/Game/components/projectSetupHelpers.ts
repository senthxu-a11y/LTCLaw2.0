import type {
  ColdStartJobState,
  EffectiveProjectSetupReadiness,
  ProjectSetupStatusResponse,
  ProjectTableSourceEntry,
  ProjectTableSourceDiscoveryResponse,
} from "../../../api/types/game";


const ACTIVE_COLD_START_JOB_PREFIX = "ltclaw.game.projectSetup.activeJob.";
const PROJECT_SETUP_DISCOVERY_CACHE_PREFIX = "ltclaw_project_setup_discovery:";

export function splitProjectSetupLines(value: string): string[] {
  return value
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function joinProjectSetupLines(values: string[] | null | undefined): string {
  return (values ?? []).join("\n");
}

export function getProjectSetupDiscoverySummary(
  setupStatus: ProjectSetupStatusResponse | null,
  discovery: ProjectTableSourceDiscoveryResponse | null,
) {
  if (discovery) {
    return {
      status: "scanned" as const,
      ...discovery.summary,
    };
  }
  return {
    status: setupStatus?.discovery.status ?? "not_scanned",
    discovered_table_count: setupStatus?.discovery.discovered_table_count ?? 0,
    available_table_count: setupStatus?.discovery.available_table_count ?? 0,
    excluded_table_count: setupStatus?.discovery.excluded_table_count ?? 0,
    unsupported_table_count: setupStatus?.discovery.unsupported_table_count ?? 0,
    error_count: setupStatus?.discovery.error_count ?? 0,
  };
}

export function getAvailableColdStartTables(
  discovery: ProjectTableSourceDiscoveryResponse | null,
): ProjectTableSourceEntry[] {
  return discovery?.table_files.filter((item) => item.cold_start_supported) ?? [];
}

export function isProjectSetupBuildBlocked(
  setupStatus: ProjectSetupStatusResponse | null,
  discovery: ProjectTableSourceDiscoveryResponse | null,
): boolean {
  return getEffectiveProjectSetupBuildReadiness(setupStatus, discovery).blocking_reason !== null;
}

export function getEffectiveProjectSetupBuildReadiness(
  setupStatus: ProjectSetupStatusResponse | null,
  discovery: ProjectTableSourceDiscoveryResponse | null,
): EffectiveProjectSetupReadiness {
  if (discovery) {
    const availableCount = getAvailableColdStartTables(discovery).length;
    if (availableCount > 0) {
      return {
        blocking_reason: null,
        next_action: "ready_for_rule_only_cold_start",
        source: "discovery",
      };
    }
    return {
      blocking_reason: "no_table_sources_found",
      next_action: String(discovery.next_action || "run_source_discovery"),
      source: "discovery",
    };
  }

  return {
    blocking_reason: setupStatus?.build_readiness.blocking_reason ?? "project_root_not_configured",
    next_action: setupStatus?.build_readiness.next_action ?? "set_project_root",
    source: "setup_status",
  };
}

export function isProjectSetupProjectRootDirty(
  inputValue: string,
  setupStatus: ProjectSetupStatusResponse | null,
): boolean {
  const currentValue = inputValue.trim();
  const effectiveValue = (setupStatus?.project_root ?? "").trim();
  return currentValue.length > 0 && currentValue !== effectiveValue;
}

export function buildProjectSetupDiagnosticsText(input: {
  setupStatus: ProjectSetupStatusResponse | null;
  discovery: ProjectTableSourceDiscoveryResponse | null;
  coldStartJob?: ColdStartJobState | null;
}): string {
  return JSON.stringify(
    {
      setup_status: input.setupStatus,
      discovery: input.discovery,
      effective_readiness: getEffectiveProjectSetupBuildReadiness(input.setupStatus, input.discovery),
      cold_start_job: input.coldStartJob ?? null,
    },
    null,
    2,
  );
}

export function canStartRuleOnlyColdStartBuild(
  setupStatus: ProjectSetupStatusResponse | null,
  discovery: ProjectTableSourceDiscoveryResponse | null,
): boolean {
  if (!setupStatus?.project_root || !setupStatus.project_root_exists) {
    return false;
  }
  if ((setupStatus.tables_config.roots ?? []).length <= 0) {
    return false;
  }
  const readiness = getEffectiveProjectSetupBuildReadiness(setupStatus, discovery);
  return readiness.blocking_reason === null;
}

export function getProjectSetupProjectIdentity(setupStatus: ProjectSetupStatusResponse | null): string {
  return (
    (setupStatus?.project_key ?? "").trim() ||
    (setupStatus?.project_root ?? "").trim() ||
    (setupStatus?.active_workspace_project_root ?? "").trim()
  );
}

export function getColdStartActiveJobStorageKey(
  setupStatus: ProjectSetupStatusResponse | null,
  fallbackProjectIdentity = "",
): string {
  const projectIdentity = getProjectSetupProjectIdentity(setupStatus) || fallbackProjectIdentity.trim();
  return projectIdentity ? `${ACTIVE_COLD_START_JOB_PREFIX}${projectIdentity}` : "";
}

export function getProjectSetupDiscoveryCacheKey(
  setupStatus: ProjectSetupStatusResponse | null,
): string {
  const workspaceRoot = (setupStatus?.active_workspace_root ?? "").trim() || "__legacy_workspace__";
  const projectIdentity =
    (setupStatus?.project_key ?? "").trim() ||
    (setupStatus?.project_root ?? "").trim() ||
    (setupStatus?.active_workspace_project_root ?? "").trim();

  if (!projectIdentity) {
    return "";
  }

  return `${PROJECT_SETUP_DISCOVERY_CACHE_PREFIX}${workspaceRoot}::${projectIdentity}`;
}

export function loadProjectSetupCachedDiscovery(
  setupStatus: ProjectSetupStatusResponse | null,
): ProjectTableSourceDiscoveryResponse | null {
  if (typeof localStorage === "undefined") {
    return null;
  }
  const cacheKey = getProjectSetupDiscoveryCacheKey(setupStatus);
  if (!cacheKey) {
    return null;
  }
  const payload = localStorage.getItem(cacheKey);
  if (!payload) {
    return null;
  }
  try {
    return JSON.parse(payload) as ProjectTableSourceDiscoveryResponse;
  } catch {
    localStorage.removeItem(cacheKey);
    return null;
  }
}

export function saveProjectSetupCachedDiscovery(
  setupStatus: ProjectSetupStatusResponse | null,
  discovery: ProjectTableSourceDiscoveryResponse | null,
): void {
  if (typeof localStorage === "undefined") {
    return;
  }
  const cacheKey = getProjectSetupDiscoveryCacheKey(setupStatus);
  if (!cacheKey || !discovery) {
    return;
  }
  localStorage.setItem(cacheKey, JSON.stringify(discovery));
}

export function clearProjectSetupCachedDiscovery(
  setupStatus: ProjectSetupStatusResponse | null,
): void {
  if (typeof localStorage === "undefined") {
    return;
  }
  const cacheKey = getProjectSetupDiscoveryCacheKey(setupStatus);
  if (!cacheKey) {
    return;
  }
  localStorage.removeItem(cacheKey);
}

export function loadColdStartActiveJobId(
  setupStatus: ProjectSetupStatusResponse | null,
  fallbackProjectIdentity = "",
): string {
  if (typeof localStorage === "undefined") {
    return "";
  }
  const key = getColdStartActiveJobStorageKey(setupStatus, fallbackProjectIdentity);
  return key ? localStorage.getItem(key) || "" : "";
}

export function saveColdStartActiveJobId(
  setupStatus: ProjectSetupStatusResponse | null,
  jobId: string,
  fallbackProjectIdentity = "",
): void {
  if (typeof localStorage === "undefined") {
    return;
  }
  const key = getColdStartActiveJobStorageKey(setupStatus, fallbackProjectIdentity);
  if (!key) {
    return;
  }
  if (jobId) {
    localStorage.setItem(key, jobId);
    return;
  }
  localStorage.removeItem(key);
}

export function clearColdStartActiveJobId(
  setupStatus: ProjectSetupStatusResponse | null,
  fallbackProjectIdentity = "",
): void {
  saveColdStartActiveJobId(setupStatus, "", fallbackProjectIdentity);
}

export function toColdStartProgressView(job: ColdStartJobState | null) {
  if (!job) {
    return {
      percent: 0,
      statusTone: "normal",
      isTerminal: false,
      isRunning: false,
      canCancel: false,
      canRetry: false,
      candidateTableCount: 0,
    } as const;
  }

  const isTerminal = ["succeeded", "failed", "cancelled"].includes(job.status);
  const isRunning = ["pending", "running"].includes(job.status);
  const statusTone = job.status === "succeeded"
    ? "success"
    : job.status === "failed"
      ? "exception"
      : job.status === "cancelled"
        ? "normal"
        : "active";

  return {
    percent: Math.max(0, Math.min(100, job.progress || 0)),
    statusTone,
    isTerminal,
    isRunning,
    canCancel: isRunning,
    canRetry: job.status === "failed" || job.status === "cancelled",
    candidateTableCount: job.counts?.candidate_table_count ?? 0,
  } as const;
}
