import type {
  ColdStartJobState,
  ProjectSetupStatusResponse,
  ProjectTableSourceEntry,
  ProjectTableSourceDiscoveryResponse,
} from "../../../api/types/game";


const ACTIVE_COLD_START_JOB_PREFIX = "ltclaw_cold_start_active_job:";

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
  if (discovery) {
    return getAvailableColdStartTables(discovery).length <= 0;
  }
  const summary = getProjectSetupDiscoverySummary(setupStatus, discovery);
  return (summary.available_table_count ?? 0) <= 0;
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
  return !isProjectSetupBuildBlocked(setupStatus, discovery);
}

export function getColdStartActiveJobStorageKey(agentId: string): string {
  return `${ACTIVE_COLD_START_JOB_PREFIX}${agentId}`;
}

export function loadColdStartActiveJobId(agentId: string): string {
  if (typeof localStorage === "undefined") {
    return "";
  }
  return localStorage.getItem(getColdStartActiveJobStorageKey(agentId)) || "";
}

export function saveColdStartActiveJobId(agentId: string, jobId: string): void {
  if (typeof localStorage === "undefined") {
    return;
  }
  if (jobId) {
    localStorage.setItem(getColdStartActiveJobStorageKey(agentId), jobId);
    return;
  }
  localStorage.removeItem(getColdStartActiveJobStorageKey(agentId));
}

export function clearColdStartActiveJobId(agentId: string): void {
  saveColdStartActiveJobId(agentId, "");
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