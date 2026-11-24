/**
 * Showcase session.
 *
 * A Showcase session is a frontend-only presentation marker. It is NOT a
 * production identity and NEVER grants access to production data or APIs.
 *
 * localStorage is NOT a trusted security boundary: a user can modify it. A
 * tampered session can at most change the local presentation state — it can
 * never grant production access, because:
 *   1. the API client interceptor blocks all API calls while a session exists;
 *   2. the global network boundary (networkBoundary.ts) blocks raw fetch/XHR;
 *   3. the session carries no production credential of any kind.
 *
 * Session structure is validated fail-closed on read (demo flag, read-only
 * flag, known persona, valid timestamps, session id, matching profile).
 */

import { getShowcaseControl, type ShowcaseControl } from "./control";
import { DEMO_PROFILES, isDemoProfileId, type DemoProfileId } from "./profiles";

export const DEMO_SESSION_KEY = "gula_demo_session";
export const SHOWCASE_UNAVAILABLE_KEY = "showcase_unavailable";

/** Maximum lifetime of a Showcase session regardless of control expiry. */
export const DEMO_SESSION_TTL_MS = 30 * 60 * 1000;

export interface DemoSession {
  demo: true;
  profile: DemoProfileId;
  profileId: DemoProfileId;
  persona: DemoProfileId;
  displayName: string;
  displayNameEn: string;
  readOnly: true;
  /** Presentation label only — never used for authorization. */
  role: string;
  /** Random, non-sensitive identifier. */
  sessionId: string;
  issuedAt: string;
  expiresAt: string;
}

function randomSessionId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `demo-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

export function buildDemoSession(profileId: DemoProfileId, now: Date = new Date()): DemoSession {
  const profile = DEMO_PROFILES[profileId]!;
  const issuedAt = now.toISOString();
  return {
    demo: true,
    profile: profileId,
    profileId,
    persona: profileId,
    displayName: profile.displayNameAr,
    displayNameEn: profile.displayNameEn,
    readOnly: true,
    role: profile.role,
    sessionId: randomSessionId(),
    issuedAt,
    expiresAt: new Date(now.getTime() + DEMO_SESSION_TTL_MS).toISOString(),
  };
}

export function writeDemoSession(session: DemoSession): void {
  localStorage.setItem(DEMO_SESSION_KEY, JSON.stringify(session));
}

function isValidTimestamp(value: unknown): value is string {
  return typeof value === "string" && value.length > 0 && !Number.isNaN(Date.parse(value));
}

/**
 * Reads and validates the stored Showcase session. Fail closed: any
 * structurally invalid, unknown-persona, or expired session is cleared and
 * treated as no session.
 */
export function readDemoSession(now: Date = new Date()): DemoSession | null {
  const raw = localStorage.getItem(DEMO_SESSION_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<DemoSession>;
    const valid =
      parsed !== null &&
      typeof parsed === "object" &&
      parsed.demo === true &&
      parsed.readOnly === true &&
      typeof parsed.persona === "string" &&
      isDemoProfileId(parsed.persona) &&
      parsed.profileId === parsed.persona &&
      isValidTimestamp(parsed.issuedAt) &&
      isValidTimestamp(parsed.expiresAt) &&
      new Date(parsed.expiresAt).getTime() > now.getTime() &&
      typeof parsed.sessionId === "string" &&
      parsed.sessionId.length > 0 &&
      typeof parsed.role === "string";
    if (valid) {
      return parsed as DemoSession;
    }
  } catch {
    // malformed Showcase session — fail closed
  }
  localStorage.removeItem(DEMO_SESSION_KEY);
  return null;
}

export function isDemoSessionActive(now: Date = new Date()): boolean {
  return readDemoSession(now) !== null;
}

/** Enters Showcase for the given persona. Fails closed unless control is enabled. */
export function enterDemo(
  persona: DemoProfileId,
  control: ShowcaseControl = getShowcaseControl(),
  now: Date = new Date(),
): DemoSession | null {
  if (!control.enabled) return null;
  if (!isDemoProfileId(persona)) return null;
  const session = buildDemoSession(persona, now);
  writeDemoSession(session);
  return session;
}

/** Ends the Showcase session and clears local Showcase state. */
export function exitDemo(): void {
  localStorage.removeItem(DEMO_SESSION_KEY);
}

/**
 * Marks that Showcase became unavailable (killed / expired / disabled) so the
 * login page can show a safe, non-sensitive notice. Stored in sessionStorage
 * (transient, per browser tab session).
 */
export function markShowcaseUnavailable(): void {
  sessionStorage.setItem(SHOWCASE_UNAVAILABLE_KEY, "1");
}

/** Consumes (reads and clears) the Showcase-unavailable notice flag. */
export function consumeShowcaseUnavailable(): boolean {
  const present = sessionStorage.getItem(SHOWCASE_UNAVAILABLE_KEY) === "1";
  if (present) {
    sessionStorage.removeItem(SHOWCASE_UNAVAILABLE_KEY);
  }
  return present;
}
