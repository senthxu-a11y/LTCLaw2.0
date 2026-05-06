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
  path?: string;
}

export interface DocLibraryResponse {
  items: DocLibraryDocument[];
  categories: string[];
  count: number;
}

export interface DocLibraryDocumentDetail {
  item: DocLibraryDocument;
  content: string;
  preview_kind: "markdown" | "text" | "unsupported";
  truncated: boolean;
}

export interface UpdateDocLibraryDocumentResponse extends DocLibraryDocumentDetail {
  kb_entry_id?: string | null;
}

export const gameDocLibraryApi = {
  async listDocuments(agentId: string): Promise<DocLibraryResponse> {
    return request<DocLibraryResponse>(`/agents/${agentId}/game-doc-library/documents`);
  },

  async getDocument(agentId: string, docId: string): Promise<DocLibraryDocumentDetail> {
    return request<DocLibraryDocumentDetail>(
      `/agents/${agentId}/game-doc-library/documents/${encodeURIComponent(docId)}`,
    );
  },

  async updateDocument(
    agentId: string,
    docId: string,
    body: { status: string },
  ): Promise<UpdateDocLibraryDocumentResponse> {
    return request<UpdateDocLibraryDocumentResponse>(
      `/agents/${agentId}/game-doc-library/documents/${encodeURIComponent(docId)}`,
      {
        method: "PATCH",
        body: JSON.stringify(body),
      },
    );
  },
};