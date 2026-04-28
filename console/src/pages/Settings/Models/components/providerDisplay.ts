export function getProviderDisplayName(providerId: string, providerName: string) {
  if (providerId === "ltclaw_gy_x-local") {
    return "llama.cpp Local";
  }

  return providerName;
}
