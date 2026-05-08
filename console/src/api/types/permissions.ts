export type FrontendCapability =
  | "knowledge.read"
  | "knowledge.build"
  | "knowledge.publish"
  | "knowledge.map.read"
  | "knowledge.map.edit"
  | "knowledge.candidate.read"
  | "knowledge.candidate.write"
  | "workbench.read"
  | "workbench.test.write"
  | "workbench.test.export";

export type FrontendCapabilityToken = FrontendCapability | "*";

export type FrontendCapabilityState = readonly FrontendCapabilityToken[] | null | undefined;

export type CapabilityName = FrontendCapability;

export type CapabilityToken = FrontendCapabilityToken;

export type CapabilityState = FrontendCapabilityState;
