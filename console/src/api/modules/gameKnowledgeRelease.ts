import { request } from '../request';
import type {
  FormalKnowledgeMapResponse,
  KnowledgeMap,
  KnowledgeRagAnswerResponse,
  KnowledgeMapCandidateResponse,
  KnowledgeIndexArtifact,
  KnowledgeManifest,
  KnowledgeReleasePointer,
  KnowledgeReleaseStatusResponse,
  ReleaseCandidateListItem,
} from '../types/game';

const NO_CURRENT_RELEASE_DETAIL = 'No current knowledge release is set';

export interface BuildKnowledgeReleaseFromCurrentIndexesRequest {
  release_id: string;
  release_notes?: string;
  candidate_ids?: string[];
}

export interface BuildKnowledgeReleaseResponse {
  release_dir: string;
  manifest: KnowledgeManifest;
  knowledge_map: Record<string, unknown>;
  artifacts: Record<string, KnowledgeIndexArtifact>;
}

export interface KnowledgeRagAnswerRequest {
  query: string;
  max_chunks?: number;
  max_chars?: number;
}

export interface BuildSourceCandidateRequest {
  use_existing_formal_map_as_hint?: boolean;
}

function isNoCurrentReleaseError(error: unknown): boolean {
  return error instanceof Error && error.message.includes(NO_CURRENT_RELEASE_DETAIL);
}

export const gameKnowledgeReleaseApi = {
  async listReleases(agentId: string): Promise<KnowledgeManifest[]> {
    return request<KnowledgeManifest[]>(`/agents/${agentId}/game/knowledge/releases`);
  },

  async getReleaseStatus(agentId: string): Promise<KnowledgeReleaseStatusResponse> {
    return request<KnowledgeReleaseStatusResponse>(`/agents/${agentId}/game/knowledge/releases/status`);
  },

  async listBuildCandidates(agentId: string): Promise<ReleaseCandidateListItem[]> {
    const params = new URLSearchParams({
      status: 'accepted',
      selected: 'true',
    });
    return request<ReleaseCandidateListItem[]>(`/agents/${agentId}/game/knowledge/release-candidates?${params.toString()}`);
  },

  async getCurrentRelease(agentId: string): Promise<KnowledgeManifest | null> {
    try {
      return await request<KnowledgeManifest>(`/agents/${agentId}/game/knowledge/releases/current`);
    } catch (error) {
      if (isNoCurrentReleaseError(error)) {
        return null;
      }
      throw error;
    }
  },

  async setCurrentRelease(agentId: string, releaseId: string): Promise<KnowledgeReleasePointer> {
    return request<KnowledgeReleasePointer>(`/agents/${agentId}/game/knowledge/releases/${encodeURIComponent(releaseId)}/current`, {
      method: 'POST',
    });
  },

  async buildReleaseFromCurrentIndexes(
    agentId: string,
    payload: BuildKnowledgeReleaseFromCurrentIndexesRequest,
  ): Promise<BuildKnowledgeReleaseResponse> {
    return request<BuildKnowledgeReleaseResponse>(`/agents/${agentId}/game/knowledge/releases/build-from-current-indexes`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getMapCandidate(agentId: string): Promise<KnowledgeMapCandidateResponse> {
    return request<KnowledgeMapCandidateResponse>(`/agents/${agentId}/game/knowledge/map/candidate`);
  },

  async buildMapCandidateFromSource(
    agentId: string,
    payload: BuildSourceCandidateRequest = {},
  ): Promise<KnowledgeMapCandidateResponse> {
    return request<KnowledgeMapCandidateResponse>(`/agents/${agentId}/game/knowledge/map/candidate/from-source`, {
      method: 'POST',
      body: JSON.stringify({
        use_existing_formal_map_as_hint: payload.use_existing_formal_map_as_hint ?? true,
      }),
    });
  },

  async getFormalMap(agentId: string): Promise<FormalKnowledgeMapResponse> {
    return request<FormalKnowledgeMapResponse>(`/agents/${agentId}/game/knowledge/map`);
  },

  async answerRagQuestion(agentId: string, payload: KnowledgeRagAnswerRequest): Promise<KnowledgeRagAnswerResponse> {
    return request<KnowledgeRagAnswerResponse>(`/agents/${agentId}/game/knowledge/rag/answer`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async saveFormalMap(agentId: string, map: KnowledgeMap, updatedBy?: string): Promise<FormalKnowledgeMapResponse> {
    return request<FormalKnowledgeMapResponse>(`/agents/${agentId}/game/knowledge/map`, {
      method: 'PUT',
      body: JSON.stringify({ map, updated_by: updatedBy ?? null }),
    });
  },
};
