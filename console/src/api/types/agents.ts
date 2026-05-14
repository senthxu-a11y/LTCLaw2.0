// Multi-agent management types

import type { ModelSlotConfig } from "./provider";
import type { FrontendCapabilityToken } from "./permissions";

export type LocalAgentRole = "viewer" | "planner" | "source_writer" | "admin";

export interface LocalAgentProfileSummary {
  agent_id: string;
  display_name: string;
  role: LocalAgentRole;
  capabilities: FrontendCapabilityToken[];
  note?: string;
}

export interface AgentSummary {
  id: string;
  name: string;
  display_name?: string;
  description: string;
  workspace_dir: string;
  enabled: boolean;
  role?: LocalAgentRole;
  active_model?: ModelSlotConfig | null;
  capabilities?: FrontendCapabilityToken[];
  agent_profile?: LocalAgentProfileSummary;
}

export interface AgentListResponse {
  agents: AgentSummary[];
}

export interface ReorderAgentsResponse {
  success: boolean;
  agent_ids: string[];
}

export interface AgentProfileConfig {
  id: string;
  name: string;
  display_name?: string;
  description?: string;
  workspace_dir?: string;
  role?: LocalAgentRole;
  capabilities?: FrontendCapabilityToken[];
  agent_profile?: LocalAgentProfileSummary;
  approval_level?: string;
  active_model?: ModelSlotConfig | null;
  channels?: unknown;
  mcp?: unknown;
  heartbeat?: unknown;
  running?: unknown;
  llm_routing?: unknown;
  system_prompt_files?: string[];
  tools?: unknown;
  security?: unknown;
}

export interface CreateAgentRequest {
  id?: string;
  name: string;
  description?: string;
  workspace_dir?: string;
  language?: string;
  skill_names?: string[];
  active_model?: ModelSlotConfig | null;
}

export interface AgentProfileRef {
  id: string;
  workspace_dir: string;
}
