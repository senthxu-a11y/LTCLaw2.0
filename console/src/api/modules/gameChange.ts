import { request } from "../request";

export interface ChangeProposalCreate {
  title: string;
  description: string;
  ops: Array<Record<string, any>>;
}

export interface ChangeProposalRecord {
  id: string;
  title: string;
  description?: string;
  status: string;
  author?: string;
  created_at: string;
  updated_at?: string;
  ops: Array<Record<string, any>>;
}

export const gameChangeApi = {
  list(agentId: string, status?: string) {
    const query = status ? `?status=${encodeURIComponent(status)}` : "";
    return request<ChangeProposalRecord[]>(`/agents/${agentId}/game/change/proposals${query}`);
  },

  get(agentId: string, id: string) {
    return request<ChangeProposalRecord>(`/agents/${agentId}/game/change/proposals/${id}`);
  },

  create(agentId: string, body: ChangeProposalCreate) {
    return request<ChangeProposalRecord>(`/agents/${agentId}/game/change/proposals`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  dryRun(agentId: string, id: string) {
    return request(`/agents/${agentId}/game/change/proposals/${id}/dry_run`, {
      method: "POST",
    });
  },

  approve(agentId: string, id: string) {
    return request(`/agents/${agentId}/game/change/proposals/${id}/approve`, {
      method: "POST",
    });
  },

  apply(agentId: string, id: string) {
    return request(`/agents/${agentId}/game/change/proposals/${id}/apply`, {
      method: "POST",
    });
  },

  commit(agentId: string, id: string) {
    return request(`/agents/${agentId}/game/change/proposals/${id}/commit`, {
      method: "POST",
    });
  },

  reject(agentId: string, id: string) {
    return request(`/agents/${agentId}/game/change/proposals/${id}/reject`, {
      method: "POST",
    });
  },

  revert(agentId: string, id: string) {
    return request(`/agents/${agentId}/game/change/proposals/${id}/revert`, {
      method: "POST",
    });
  },
};
