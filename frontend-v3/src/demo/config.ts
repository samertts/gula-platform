export interface DemoConfig {
  enabled: boolean;
  enabledByEnv: boolean;
  expiresAt: string | null;
  reason: string | null;
}

const TRUE_VALUES = new Set(["true", "1", "yes"]);

/**
 * Parses the demo-mode configuration from raw environment values.
 *
 * Fail-closed rules:
 *  - Demo is disabled unless VITE_DEMO_MODE_ENABLED is an explicit true value.
 *  - If enabled but VITE_DEMO_MODE_EXPIRES_AT is missing -> disabled.
 *  - If the expiry value is not a valid timestamp -> disabled.
 *  - If the expiry timestamp is in the past -> disabled.
 */
export function parseDemoConfig(
  enabledRaw: string | undefined,
  expiresRaw: string | undefined,
  now: Date = new Date(),
): DemoConfig {
  const enabledByEnv = TRUE_VALUES.has(String(enabledRaw ?? "").trim().toLowerCase());

  if (!enabledByEnv) {
    return { enabled: false, enabledByEnv: false, expiresAt: null, reason: "disabled_by_config" };
  }

  const rawExpiry = (expiresRaw ?? "").trim();
  if (!rawExpiry) {
    return { enabled: false, enabledByEnv: true, expiresAt: null, reason: "expiry_missing" };
  }

  const expiresAt = new Date(rawExpiry);
  if (Number.isNaN(expiresAt.getTime())) {
    return { enabled: false, enabledByEnv: true, expiresAt: null, reason: "expiry_invalid" };
  }

  if (now.getTime() >= expiresAt.getTime()) {
    return { enabled: false, enabledByEnv: true, expiresAt: rawExpiry, reason: "expired" };
  }

  return { enabled: true, enabledByEnv: true, expiresAt: rawExpiry, reason: null };
}

export const demoConfig: DemoConfig = parseDemoConfig(
  import.meta.env.VITE_DEMO_MODE_ENABLED,
  import.meta.env.VITE_DEMO_MODE_EXPIRES_AT,
);
