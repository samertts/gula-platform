import { demoConfig, type DemoConfig } from "./config";
import { DEMO_PROFILES, isDemoProfileId, type DemoProfileId } from "./profiles";

export const DEMO_SESSION_KEY = "gula_demo_session";

export interface DemoSession {
  demo: true;
  profile: DemoProfileId;
  profileId: DemoProfileId;
  displayName: string;
  displayNameEn: string;
  readOnly: true;
  role: string;
  enteredAt: string;
}

export function buildDemoSession(profileId: DemoProfileId): DemoSession {
  const profile = DEMO_PROFILES[profileId]!;
  return {
    demo: true,
    profile: profileId,
    profileId,
    displayName: profile.displayNameAr,
    displayNameEn: profile.displayNameEn,
    readOnly: true,
    role: profile.role,
    enteredAt: new Date().toISOString(),
  };
}

export function writeDemoSession(session: DemoSession): void {
  localStorage.setItem(DEMO_SESSION_KEY, JSON.stringify(session));
}

/**
 * Reads and validates the stored demo session. A demo session is only valid
 * if it is explicitly marked demo and readOnly. Malformed or partial data
 * fails closed: it is cleared and treated as no session.
 */
export function readDemoSession(): DemoSession | null {
  const raw = localStorage.getItem(DEMO_SESSION_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<DemoSession>;
    if (
      parsed &&
      parsed.demo === true &&
      parsed.readOnly === true &&
      typeof parsed.profileId === "string" &&
      isDemoProfileId(parsed.profileId)
    ) {
      return parsed as DemoSession;
    }
  } catch {
    // malformed demo session — fail closed
  }
  localStorage.removeItem(DEMO_SESSION_KEY);
  return null;
}

export function isDemoSessionActive(): boolean {
  return readDemoSession() !== null;
}

export function enterDemo(
  profileId: DemoProfileId,
  config: DemoConfig = demoConfig,
): DemoSession | null {
  if (!config.enabled) return null;
  if (!isDemoProfileId(profileId)) return null;
  const session = buildDemoSession(profileId);
  writeDemoSession(session);
  return session;
}

export function exitDemo(): void {
  localStorage.removeItem(DEMO_SESSION_KEY);
}
