import { create } from "zustand";
import { persist } from "zustand/middleware";

import type {
  ColdStartJobState,
  FrontendRuntimeInfo,
  GameStorageSummary,
  LocalAgentProfile,
  ProjectCapabilityStatus,
  ProjectSetupStatusResponse,
  ProjectTableSourceDiscoveryResponse,
  WorkspaceRootStatus,
} from "../api/types/game";

export interface ProjectSetupRuntimeCache {
  workspaceRootStatus: WorkspaceRootStatus | null;
  setupStatus: ProjectSetupStatusResponse | null;
  projectCapabilityStatus: ProjectCapabilityStatus | null;
  workspaceAgentProfile: LocalAgentProfile | null;
  storageSummary: GameStorageSummary | null;
  discoveryResult: ProjectTableSourceDiscoveryResponse | null;
  coldStartJob: ColdStartJobState | null;
  activeColdStartJobId: string;
  frontendRuntimeInfo: FrontendRuntimeInfo | null;
  lastUpdatedAt: number;
}

interface ProjectSetupStore {
  runtimeByAgent: Record<string, ProjectSetupRuntimeCache>;
  upsertRuntimeCache: (agentId: string, patch: Partial<ProjectSetupRuntimeCache>) => void;
  clearRuntimeCache: (agentId: string) => void;
  getRuntimeCache: (agentId: string) => ProjectSetupRuntimeCache | null;
}

const storage = {
  getItem: (name: string) => {
    try {
      const value = localStorage.getItem(name);
      return value ? JSON.parse(value) : null;
    } catch (error) {
      console.error(`Failed to parse project setup storage "${name}":`, error);
      localStorage.removeItem(name);
      return null;
    }
  },
  setItem: (name: string, value: unknown) => {
    try {
      localStorage.setItem(name, JSON.stringify(value));
    } catch (error) {
      console.error(`Failed to save project setup storage "${name}":`, error);
    }
  },
  removeItem: (name: string) => {
    localStorage.removeItem(name);
  },
};

export const useProjectSetupStore = create<ProjectSetupStore>()(
  persist(
    (set, get) => ({
      runtimeByAgent: {},

      upsertRuntimeCache: (agentId, patch) =>
        set((state) => ({
          runtimeByAgent: {
            ...state.runtimeByAgent,
            [agentId]: {
              workspaceRootStatus: null,
              setupStatus: null,
              projectCapabilityStatus: null,
              workspaceAgentProfile: null,
              storageSummary: null,
              discoveryResult: null,
              coldStartJob: null,
              activeColdStartJobId: "",
              frontendRuntimeInfo: null,
              ...state.runtimeByAgent[agentId],
              ...patch,
              lastUpdatedAt: Date.now(),
            },
          },
        })),

      clearRuntimeCache: (agentId) =>
        set((state) => {
          const next = { ...state.runtimeByAgent };
          delete next[agentId];
          return { runtimeByAgent: next };
        }),

      getRuntimeCache: (agentId) => get().runtimeByAgent[agentId] ?? null,
    }),
    {
      name: "ltclaw_gy_x-project-setup-runtime",
      storage,
    },
  ),
);