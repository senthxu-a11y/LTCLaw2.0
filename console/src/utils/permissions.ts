import type { FrontendCapability, FrontendCapabilityToken } from "@/api/types/permissions";

export function hasCapability(
  capabilities: FrontendCapabilityToken[] | null | undefined,
  capability: FrontendCapability,
): boolean {
  if (capabilities == null) {
    return true;
  }
  return capabilities.includes("*") || capabilities.includes(capability);
}

export function canUseGovernanceAction(
  capabilities: FrontendCapabilityToken[] | null | undefined,
  capability: FrontendCapability,
): boolean {
  return hasCapability(capabilities, capability);
}

export function hasCapabilityContext(
  capabilities: FrontendCapabilityToken[] | null | undefined,
): boolean {
  return capabilities != null;
}

export function isPermissionDeniedError(error: unknown): boolean {
  if (!(error instanceof Error)) {
    return false;
  }
  return error.message.includes("Missing capability:");
}
