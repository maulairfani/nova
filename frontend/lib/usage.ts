import { authenticatedFetch } from "./authenticatedFetch";

/** Chat rate limit status (ADR-0027) — mirrors backend/app/schemas/usage.py's UsageOut. */
export interface UsageStatus {
  used: number;
  limit: number;
  remaining: number;
  reset_seconds: number;
}

export async function getUsage(token: string): Promise<UsageStatus> {
  const response = await authenticatedFetch("/api/v1/usage", token);
  return response.json();
}

/** Shared by SettingsView and the composer's blocked-state message so the
 * "Xh Ym" text is computed in exactly one place. */
export function formatCountdown(totalSeconds: number): string {
  const seconds = Math.max(0, Math.floor(totalSeconds));
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
  if (minutes > 0) return `${minutes}m`;
  return "less than a minute";
}
