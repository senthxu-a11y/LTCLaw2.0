import { request } from '../request';

export interface DocLibraryDocument {
  id: string;
  title: string;
  type: string;
  status: string;
  updated_at: string;
  author: string;
  category: string;
  tags: string[];
}

export interface DocLibraryResponse {
  items: DocLibraryDocument[];
}

export const gameDocLibraryApi = {
  async listDocuments(agentId: string): Promise<DocLibraryResponse> {
    return request<DocLibraryResponse>(`/agents/${agentId}/game-doc-library/documents`);
  },
};