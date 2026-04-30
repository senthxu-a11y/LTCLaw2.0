import { request } from '../request';

export interface KnowledgeBaseEntry {
  id: string;
  title: string;
  category: string;
  source: string;
  created_at: string;
  summary: string;
  tags: string[];
}

export interface KnowledgeBaseResponse {
  items: KnowledgeBaseEntry[];
}

export const gameKnowledgeBaseApi = {
  async listEntries(agentId: string): Promise<KnowledgeBaseResponse> {
    return request<KnowledgeBaseResponse>(`/agents/${agentId}/game-knowledge-base/entries`);
  },
};