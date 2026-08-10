import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { api, DemoModeBlockedError } from '@/api/client';
import {
  buildDemoSession,
  writeDemoSession,
  exitDemo,
  DEMO_SESSION_KEY,
} from '@/demo/session';

describe('demo API guard', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    exitDemo();
    localStorage.clear();
  });

  it('blocks mutation requests while a demo session is active', async () => {
    writeDemoSession(buildDemoSession('doctor'));
    await expect(api.post('/test-results/', {})).rejects.toBeInstanceOf(DemoModeBlockedError);
  });

  it('blocks update/delete-style requests while a demo session is active', async () => {
    writeDemoSession(buildDemoSession('doctor'));
    await expect(api.put('/patients/1', {})).rejects.toBeInstanceOf(DemoModeBlockedError);
    await expect(api.delete('/ehr/clinical-notes/1')).rejects.toBeInstanceOf(DemoModeBlockedError);
    await expect(api.post('/admin/users', {})).rejects.toBeInstanceOf(DemoModeBlockedError);
    await expect(api.post('/orders', {})).rejects.toBeInstanceOf(DemoModeBlockedError);
  });

  it('blocks read requests while a demo session is active (no real data can load)', async () => {
    writeDemoSession(buildDemoSession('citizen'));
    await expect(api.get('/patients')).rejects.toBeInstanceOf(DemoModeBlockedError);
  });

  it('does not create a production credential when entering a demo session', () => {
    writeDemoSession(buildDemoSession('citizen'));
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(localStorage.getItem('user')).toBeNull();
    expect(localStorage.getItem(DEMO_SESSION_KEY)).not.toBeNull();
  });

  it('allows requests when no demo session is active (real auth path unaffected)', async () => {
    let err: unknown = null;
    try {
      await api.get('/health');
    } catch (e) {
      err = e;
    }
    expect(err).toBeTruthy();
    expect((err as Error)?.message).not.toMatch(/demo mode is read-only/i);
  });

  it('re-enables API access after the demo session is exited', async () => {
    writeDemoSession(buildDemoSession('doctor'));
    await expect(api.get('/patients')).rejects.toBeInstanceOf(DemoModeBlockedError);

    exitDemo();
    let err: unknown = null;
    try {
      await api.get('/health');
    } catch (e) {
      err = e;
    }
    expect((err as Error)?.message).not.toMatch(/demo mode is read-only/i);
  });
});
