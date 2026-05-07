import { request } from '../request';
import type {
  KnowledgeIndexArtifact,
  KnowledgeManifest,
  KnowledgeReleasePointer,
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

function isNoCurrentReleaseError(error: unknown): boolean {
  return error instanceof Error && error.message.includes(NO_CURRENT_RELEASE_DETAIL);
}

export const gameKnowledgeReleaseApi = {
  async listReleases(agentId: string): Promise<KnowledgeManifest[]> {
    return request<KnowledgeManifest[]>(`/agents/${agentId}/game/knowledge/releases`);
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
};