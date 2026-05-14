import { request } from '../request';
import type { 
  ColdStartJobCreateResponse,
  ColdStartJobState,
  ProjectConfig, 
  ProjectSetupStatusResponse,
  ProjectTableSourceDiscoveryResponse,
  ProjectTablesSourceConfig,
  SaveProjectRootResponse,
  SaveProjectTablesSourceResponse,
  UserGameConfig, 
  GameStorageSummary,
  ValidationIssue,
  CommitResult,
  TableIndex,
  FieldPatch,
  SystemGroup,
  ChangeSet,
  SvnStatusResponse,
  RecentSvnChangesResponse,
  PaginatedTableIndexesResponse,
  DependenciesResponse,
} from '../types/game';

export const gameApi = {
  // Project configuration
  async getProjectConfig(agentId: string): Promise<ProjectConfig | null> {
    return request<ProjectConfig | null>(`/agents/${agentId}/game/project/config`);
  },
  
  async saveProjectConfig(agentId: string, config: ProjectConfig): Promise<{ message: string }> {
    return request<{ message: string }>(`/agents/${agentId}/game/project/config`, {
      method: "PUT",
      body: JSON.stringify(config),
    });
  },
  
  async deleteProjectConfig(agentId: string): Promise<{ message: string }> {
    return request<{ message: string }>(`/agents/${agentId}/game/project/config`, {
      method: "DELETE",
    });
  },
  
  async commitProjectConfig(agentId: string, message?: string): Promise<CommitResult> {
    return request<CommitResult>(`/agents/${agentId}/game/project/config/commit`, {
      method: "POST",
      body: JSON.stringify({ message }),
    });
  },
  
  async validateProjectConfig(agentId: string): Promise<ValidationIssue[]> {
    return request<ValidationIssue[]>(`/agents/${agentId}/game/project/validate`);
  },
  
  async getUserConfig(agentId: string): Promise<UserGameConfig> {
    return request<UserGameConfig>(`/agents/${agentId}/game/project/user_config`);
  },

  async getProjectSetupStatus(agentId: string): Promise<ProjectSetupStatusResponse> {
    return request<ProjectSetupStatusResponse>(`/agents/${agentId}/game/project/setup-status`);
  },

  async saveProjectRoot(agentId: string, projectRoot: string): Promise<SaveProjectRootResponse> {
    return request<SaveProjectRootResponse>(`/agents/${agentId}/game/project/root`, {
      method: "PUT",
      body: JSON.stringify({ project_root: projectRoot }),
    });
  },

  async saveProjectTablesSource(
    agentId: string,
    config: ProjectTablesSourceConfig,
  ): Promise<SaveProjectTablesSourceResponse> {
    return request<SaveProjectTablesSourceResponse>(`/agents/${agentId}/game/project/sources/tables`, {
      method: "PUT",
      body: JSON.stringify(config),
    });
  },

  async discoverProjectTableSources(agentId: string): Promise<ProjectTableSourceDiscoveryResponse> {
    return request<ProjectTableSourceDiscoveryResponse>(`/agents/${agentId}/game/project/sources/discover`, {
      method: "POST",
    });
  },

  async createColdStartJob(
    agentId: string,
    body: { timeout_seconds?: number } = {},
  ): Promise<ColdStartJobCreateResponse> {
    return request<ColdStartJobCreateResponse>(`/agents/${agentId}/game/knowledge/map/cold-start-jobs`, {
      method: "POST",
      body: JSON.stringify({ timeout_seconds: body.timeout_seconds ?? 300 }),
    });
  },

  async getColdStartJob(agentId: string, jobId: string): Promise<ColdStartJobState> {
    return request<ColdStartJobState>(`/agents/${agentId}/game/knowledge/map/cold-start-jobs/${encodeURIComponent(jobId)}`);
  },

  async cancelColdStartJob(agentId: string, jobId: string): Promise<ColdStartJobState> {
    return request<ColdStartJobState>(`/agents/${agentId}/game/knowledge/map/cold-start-jobs/${encodeURIComponent(jobId)}/cancel`, {
      method: "POST",
    });
  },
  
  async saveUserConfig(agentId: string, config: UserGameConfig): Promise<{ message: string }> {
    return request<{ message: string }>(`/agents/${agentId}/game/project/user_config`, {
      method: "PUT",
      body: JSON.stringify(config),
    });
  },

  async getStorageSummary(agentId: string): Promise<GameStorageSummary> {
    return request<GameStorageSummary>(`/agents/${agentId}/game/project/storage`);
  },

  // SVN operations
  async getSvnStatus(agentId: string): Promise<SvnStatusResponse> {
    return request<SvnStatusResponse>(`/agents/${agentId}/game/svn/status`);
  },
  
  async triggerSync(agentId: string): Promise<ChangeSet | { disabled: true; reason: string; configured?: boolean }> {
    return request<ChangeSet | { disabled: true; reason: string; configured?: boolean }>(`/agents/${agentId}/game/svn/sync`, {
      method: "POST",
    });
  },
  
  async getSvnLogRecent(agentId: string, limit: number = 200) {
    return request(`/agents/${agentId}/game/svn/log/recent?limit=${limit}`);
  },

  async getSvnChangesRecent(agentId: string, limit: number = 50): Promise<RecentSvnChangesResponse> {
    return request<RecentSvnChangesResponse>(`/agents/${agentId}/game/svn/changes/recent?limit=${limit}`);
  },
  
  subscribeSvnLog(agentId: string, onMessage: (data: any) => void): EventSource {
    const eventSource = new EventSource(`/api/agents/${agentId}/game/svn/log/stream`);
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        console.warn('Failed to parse SSE data:', event.data);
      }
    };
    return eventSource;
  },

  // Index operations
  async listSystems(agentId: string): Promise<SystemGroup[]> {
    return request<SystemGroup[]>(`/agents/${agentId}/game/index/systems`);
  },
  
  async listTables(agentId: string, params?: {
    system?: string;
    query?: string;
    page?: number;
    size?: number;
  }): Promise<PaginatedTableIndexesResponse> {
    const searchParams = new URLSearchParams();
    if (params?.system) searchParams.append('system', params.system);
    if (params?.query) searchParams.append('query', params.query);
    if (params?.page) searchParams.append('page', params.page.toString());
    if (params?.size) searchParams.append('size', params.size.toString());
    
    const queryStr = searchParams.toString();
    const url = `/agents/${agentId}/game/index/tables${queryStr ? '?' + queryStr : ''}`;
    return request<PaginatedTableIndexesResponse>(url);
  },
  
  async getTable(agentId: string, name: string): Promise<TableIndex> {
    return request<TableIndex>(`/agents/${agentId}/game/index/tables/${name}`);
  },
  
  async patchField(agentId: string, table: string, field: string, patch: FieldPatch) {
    return request(`/agents/${agentId}/game/index/tables/${table}/fields/${field}`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    });
  },
  
  async getDependencies(agentId: string, table: string): Promise<DependenciesResponse> {
    return request<DependenciesResponse>(`/agents/${agentId}/game/index/dependencies/${table}`);
  },
  
  async findField(agentId: string, name: string) {
    return request(`/agents/${agentId}/game/index/find_field?name=${encodeURIComponent(name)}`);
  },
  
  async query(agentId: string, q: string, mode: string = "auto") {
    return request(`/agents/${agentId}/game/index/query`, {
      method: "POST",
      body: JSON.stringify({ q, mode }),
    });
  },

  async getIndexStatus(agentId: string): Promise<{ configured: boolean; table_count?: number }> {
    return request(`/agents/${agentId}/game/index/status`);
  },

  async rebuildIndex(agentId: string): Promise<{ revision: number; scanned_files: string[]; indexed: number }> {
    return request(`/agents/${agentId}/game/index/rebuild`, {
      method: "POST",
    });
  },

  async getTableRows(
    agentId: string,
    name: string,
    offset: number = 0,
    limit: number = 100,
  ): Promise<{
    headers: string[];
    rows: (string | number | boolean)[][];
    total: number;
    header_row: number;
    comment_row: number | null;
    source: string;
  }> {
    return request(
      `/agents/${agentId}/game/index/tables/${encodeURIComponent(name)}/rows?offset=${offset}&limit=${limit}`,
    );
  },

  async reverseImpact(
    agentId: string,
    table: string,
    field?: string,
    maxDepth: number = 3,
  ): Promise<{
    target: { table: string; field: string | null };
    max_depth: number;
    tables: string[];
    impacts: Array<{
      from_table: string;
      from_field: string;
      to_table: string;
      to_field: string;
      confidence: string;
      inferred_by: string;
      depth: number;
      path: string[];
    }>;
    total: number;
  }> {
    const qs = new URLSearchParams({ table, max_depth: String(maxDepth) });
    if (field) qs.set("field", field);
    return request(
      `/agents/${agentId}/game/index/impact?${qs.toString()}`,
    );
  },
};
