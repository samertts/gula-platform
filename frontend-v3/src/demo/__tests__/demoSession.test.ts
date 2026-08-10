import { describe, it, expect, beforeEach } from 'vitest';
import type { DemoConfig } from '../config';
import {
  buildDemoSession,
  enterDemo,
  exitDemo,
  readDemoSession,
  isDemoSessionActive,
  writeDemoSession,
  DEMO_SESSION_KEY,
} from '../session';
import { DEMO_PROFILES, DEMO_PROFILE_IDS, isDemoProfileId } from '../profiles';
import { ROLE_PERMISSIONS } from '@/permissions';

const ENABLED: DemoConfig = {
  enabled: true,
  enabledByEnv: true,
  expiresAt: '2099-01-01T00:00:00Z',
  reason: null,
};

describe('demo profiles', () => {
  it('exposes exactly the documented demo profiles', () => {
    expect([...DEMO_PROFILE_IDS]).toEqual(['citizen', 'doctor', 'lab_staff', 'nurse', 'health_admin']);
  });

  it('maps every demo profile to an existing application role (no invented roles)', () => {
    for (const id of DEMO_PROFILE_IDS) {
      const profile = DEMO_PROFILES[id];
      expect(profile).toBeDefined();
      expect(profile.role in ROLE_PERMISSIONS).toBe(true);
    }
  });

  it('does not invent a pharmacist role (not present in the application)', () => {
    expect(isDemoProfileId('pharmacist')).toBe(false);
  });
});

describe('demo session', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('builds a session marked demo and read-only', () => {
    const session = buildDemoSession('doctor');
    expect(session.demo).toBe(true);
    expect(session.readOnly).toBe(true);
    expect(session.profile).toBe('doctor');
    expect(session.role).toBe('doctor');
    expect(session.displayName).toBe('طبيب تجريبي');
  });

  it('stores only minimum identity info and never a production credential', () => {
    enterDemo('citizen', ENABLED);
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(localStorage.getItem('user')).toBeNull();
    expect(localStorage.getItem(DEMO_SESSION_KEY)).not.toBeNull();
  });

  it('enterDemo fails closed when demo mode is disabled', () => {
    expect(enterDemo('doctor')).toBeNull();
    expect(localStorage.getItem(DEMO_SESSION_KEY)).toBeNull();
  });

  it('enterDemo rejects unknown profiles', () => {
    expect(enterDemo('pharmacist' as never, ENABLED)).toBeNull();
  });

  it('enterDemo persists a readable session when enabled', () => {
    const session = enterDemo('doctor', ENABLED);
    expect(session).not.toBeNull();
    expect(isDemoSessionActive()).toBe(true);
    const read = readDemoSession();
    expect(read?.demo).toBe(true);
    expect(read?.readOnly).toBe(true);
    expect(read?.profileId).toBe('doctor');
  });

  it('exitDemo clears the session and deactivates demo mode', () => {
    enterDemo('nurse', ENABLED);
    expect(isDemoSessionActive()).toBe(true);
    exitDemo();
    expect(isDemoSessionActive()).toBe(false);
    expect(localStorage.getItem(DEMO_SESSION_KEY)).toBeNull();
  });

  it('treats malformed stored data as no session and clears it (fail closed)', () => {
    localStorage.setItem(DEMO_SESSION_KEY, '{not-json');
    expect(readDemoSession()).toBeNull();
    expect(localStorage.getItem(DEMO_SESSION_KEY)).toBeNull();
  });

  it('rejects a stored session that is not explicitly read-only', () => {
    writeDemoSession({ ...buildDemoSession('doctor'), readOnly: false } as never);
    expect(readDemoSession()).toBeNull();
  });

  it('rejects a stored session with an unknown profile', () => {
    localStorage.setItem(
      DEMO_SESSION_KEY,
      JSON.stringify({ demo: true, readOnly: true, profileId: 'hacker', enteredAt: 'x' }),
    );
    expect(readDemoSession()).toBeNull();
  });
});
