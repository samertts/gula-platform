/**
 * Pure-logic tests for the command palette and shortcut machinery.
 *
 * Run with the project's existing tsx (already a devDependency):
 *
 *     npx tsx --test src/lib/__tests__/commandRegistryCore.test.ts
 *
 * The tests exercise only React-free code: search scoring, role filtering,
 * and the keyboard-sequence state machine. No JSDOM, no mocks, no bundler.
 */
import { strict as assert } from 'node:assert';
import { describe, it } from 'node:test';

// Note: explicit `.ts` extensions are required so the file is runnable with
// `node --experimental-strip-types --test`. The project's tsconfig sets
// `allowImportingTsExtensions: true`, so this stays type-checked too.
import {
  filterByWings,
  scoreCommand,
  searchCommands,
  stepSequence,
  wingsForProfile,
  type SearchableCommand,
} from '../commandRegistryCore.ts';
import type { Translation } from '../../translations.ts';
import type { UserProfile, UserWing } from '../../types/domain.ts';

/* Minimal stand-in for the real Translation type — we only read a few keys. */
const t = {
  goToDashboard: 'Go to Dashboard',
  dashboard: 'Dashboard',
  workQueue: 'Work Queue',
  citizenWing: 'Citizen Wing',
  labWing: 'Lab Wing',
  appointments: 'Appointments',
} as unknown as Translation;

const cmd = (
  partial: { id: string; label: string; category: string; keywords?: readonly string[]; shortcut?: readonly string[]; wings?: readonly string[] },
): SearchableCommand => ({
  label: () => partial.label,
  category: partial.category,
  id: partial.id,
  keywords: partial.keywords,
  shortcut: partial.shortcut,
  wings: partial.wings as unknown as readonly UserWing[],
});

const COMMANDS: readonly SearchableCommand[] = [
  cmd({ id: 'a', label: 'Go to Dashboard', category: 'navigation', keywords: ['home'], shortcut: ['G', 'D'] }),
  cmd({ id: 'b', label: 'Work Queue', category: 'lab', wings: ['lab'] }),
  cmd({ id: 'c', label: 'Lab Wing', category: 'lab', wings: ['lab'] }),
  cmd({ id: 'd', label: 'Citizen Wing', category: 'citizen', wings: ['citizen'] }),
  cmd({ id: 'e', label: 'Appointments', category: 'navigation', shortcut: ['G', 'A'] }),
];

const profile = (role: string): UserProfile =>
  ({ role, uid: 'u1', email: 'x@x', name: 'x', wing: 'citizen' } as unknown as UserProfile);

/* ─── wings ─────────────────────────────────────────────────────────── */

describe('wingsForProfile', () => {
  it('returns citizen for null profile', () => {
    assert.deepEqual(wingsForProfile(null), ['citizen']);
  });

  it('returns the full set for master_admin', () => {
    const w = wingsForProfile(profile('master_admin'));
    for (const expected of ['admin', 'lab', 'citizen', 'ministry', 'researcher']) {
      assert.ok(w.includes(expected as any), `expected ${expected} for master_admin`);
    }
  });

  it('returns lab+citizen for technician', () => {
    assert.deepEqual([...wingsForProfile(profile('technician'))].sort(), ['citizen', 'lab']);
  });

  it('falls back to citizen for an unknown role', () => {
    assert.deepEqual(wingsForProfile(profile('zzz_unknown')), ['citizen']);
  });
});

/* ─── filterByWings ─────────────────────────────────────────────────── */

describe('filterByWings', () => {
  it('always includes commands without a wings restriction', () => {
    const filtered = filterByWings(COMMANDS, ['ministry']);
    const ids = filtered.map((c) => c.id);
    assert.ok(ids.includes('a'), 'navigation command without wings should pass');
    assert.ok(ids.includes('e'), 'navigation command without wings should pass');
  });

  it('hides commands whose wings do not intersect the user wings', () => {
    const filtered = filterByWings(COMMANDS, ['ministry']);
    const ids = filtered.map((c) => c.id);
    assert.ok(!ids.includes('b'), 'lab-only command should be hidden');
    assert.ok(!ids.includes('c'), 'lab-only command should be hidden');
    assert.ok(!ids.includes('d'), 'citizen-only command should be hidden');
  });

  it('shows lab commands to a lab user', () => {
    const filtered = filterByWings(COMMANDS, ['lab', 'citizen']);
    const ids = filtered.map((c) => c.id);
    assert.ok(ids.includes('b'));
    assert.ok(ids.includes('c'));
    assert.ok(ids.includes('d'));
  });
});

/* ─── scoring & search ──────────────────────────────────────────────── */

describe('scoreCommand', () => {
  it('returns 1 for empty query (every command passes)', () => {
    assert.equal(scoreCommand(COMMANDS[0], t, ''), 1);
    assert.equal(scoreCommand(COMMANDS[0], t, '   '), 1);
  });

  it('exact substring beats subsequence', () => {
    const s1 = scoreCommand(COMMANDS[0], t, 'dash');
    const s2 = scoreCommand(COMMANDS[0], t, 'gdh'); // subsequence of "go to dashboard"
    assert.ok(s1 > s2, 'substring score should beat subsequence');
  });

  it('keyword and shortcut tokens are searchable', () => {
    assert.ok(scoreCommand(COMMANDS[0], t, 'home') > 0, 'keyword "home" should match');
    assert.ok(scoreCommand(COMMANDS[0], t, 'gd') > 0, 'shortcut "GD" should match');
  });

  it('case-insensitive match', () => {
    assert.ok(scoreCommand(COMMANDS[0], t, 'DASHBOARD') > 0);
    assert.ok(scoreCommand(COMMANDS[0], t, 'dashBOARD') > 0);
  });

  it('returns 0 when no chars line up', () => {
    assert.equal(scoreCommand(COMMANDS[0], t, 'xyz'), 0);
  });
});

describe('searchCommands', () => {
  it('returns substring matches before subsequence matches', () => {
    const results = searchCommands(COMMANDS, t, 'queue');
    assert.equal(results[0]?.id, 'b', 'Work Queue should rank first');
  });

  it('drops zero-score commands', () => {
    const results = searchCommands(COMMANDS, t, 'queue');
    assert.ok(!results.some((c) => c.id === 'd'), 'Citizen Wing must not appear');
  });

  it('empty query returns every command', () => {
    const results = searchCommands(COMMANDS, t, '');
    assert.equal(results.length, COMMANDS.length);
  });
});

/* ─── sequence state machine ────────────────────────────────────────── */

describe('stepSequence', () => {
  const bindings = ['g d', 'g l', 'g s'];
  const win = 1500;

  it('fires on full match and resets the buffer', () => {
    const s1 = stepSequence({ buffer: [], expiresAt: 0 }, 'g', bindings, 1000, win);
    assert.equal(s1.fired, null);
    assert.deepEqual(s1.state.buffer, ['g']);

    const s2 = stepSequence(s1.state, 'd', bindings, 1100, win);
    assert.equal(s2.fired, 'g d');
    assert.deepEqual(s2.state.buffer, []);
  });

  it('drops buffer when next key has no continuation', () => {
    const s1 = stepSequence({ buffer: [], expiresAt: 0 }, 'g', bindings, 1000, win);
    const s2 = stepSequence(s1.state, 'q', bindings, 1100, win);
    assert.equal(s2.fired, null);
    assert.deepEqual(s2.state.buffer, [], 'invalid continuation should reset');
  });

  it('expires the buffer after the timeout', () => {
    const s1 = stepSequence({ buffer: [], expiresAt: 0 }, 'g', bindings, 1000, win);
    // Far past the window — next 'g' should start fresh, not match "gg".
    const s2 = stepSequence(s1.state, 'g', bindings, 5000, win);
    assert.deepEqual(s2.state.buffer, ['g']);
    assert.equal(s2.fired, null);
  });

  it('lower-cases keys for comparison', () => {
    const s1 = stepSequence({ buffer: [], expiresAt: 0 }, 'G', bindings, 1000, win);
    const s2 = stepSequence(s1.state, 'D', bindings, 1100, win);
    assert.equal(s2.fired, 'g d');
  });

  it('returns null without buffering when key has no prefix at all', () => {
    const s = stepSequence({ buffer: [], expiresAt: 0 }, 'x', bindings, 1000, win);
    assert.equal(s.fired, null);
    assert.deepEqual(s.state.buffer, []);
  });
});
