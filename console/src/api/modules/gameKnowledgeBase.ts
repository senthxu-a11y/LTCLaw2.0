import { request } from '../request';

export interface KnowledgeBaseEntry {
  id: string;
  title: string;
  category: string;
  source: string;
  created_at: string | number;
  summary: string;
  tags: string[];
  score?: number;
}

export interface KnowledgeBaseResponse {
  items: KnowledgeBaseEntry[];
  count?: number;
}

export interface KnowledgeBaseSearchRequest {
  query: string;
  top_k?: number;
  category?: string;
}

export interface KbStats {
  size: number;
  by_category: Record<string, number>;
}

export const gameKnowledgeBaseApi = {
  async listEntries(agentId: string): Promise<KnowledgeBaseResponse> {
    return request<KnowledgeBaseResponse>(`/agents/${agentId}/game-knowledge-base/entries`);
  },
  async createEntry(agentId: string, body: Partial<KnowledgeBaseEntry>): Promise<{ item: KnowledgeBaseEntry }> {
    return request(`/agents/${agentId}/game-knowledge-base/entries`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },
  async updateEntry(agentId: string, id: string, body: Partial<KnowledgeBaseEntry>): Promise<{ item: KnowledgeBaseEntry }> {
    return request(`/agents/${agentId}/game-knowledge-base/entries/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    });
  },
  async deleteEntry(agentId: string, id: string): Promise<{ deleted: string }> {
    return request(`/agents/${agentId}/game-knowledge-base/entries/${id}`, {
      method: 'DELETE',
    });
  },
  async search(agentId: string, body: KnowledgeBaseSearchRequest): Promise<KnowledgeBaseResponse & { query: string }> {
    return request(`/agents/${agentId}/game-knowledge-base/search`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },
  async stats(agentId: string): Promise<KbStats> {
    return request<KbStats>(`/agents/${agentId}/game-knowledge-base/stats`);
  },
};