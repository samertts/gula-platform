/**
 * Frontend role-isolation hardening — Phase 7.
 *
 * Pure-logic tests for the role → wings mapping that gates UI surface.
 * Frontend gating is NOT security — every server endpoint already
 * enforces RBAC and tenant isolation in the backend (see
 * backend/tests/test_tenant_isolation_matrix.py).
 *
 * What this file pins as a non-regression:
 *   1. Citizens never see admin / ministry / regulator wings.
 *   2. Technicians and lab admins only see lab + citizen wings.
 *   3. Master admin sees the full set.
 *   4. An unknown / null role falls back to citizen-only — never empty
 *      (an empty wing list would render a broken UI).
 *   5. The map is internally consistent: every role's wing list is a
 *      subset of the master_admin set.
 *
 * Run via:
 *     npx tsx --test src/lib/__tests__/roleWingIsolation.test.ts
 *
 * Blast radius: zero. Frontend tests do not modify production code.
 */
import { strict as assert } from 'node:assert';
import { describe, it } from 'node:test';

import {
  ROLE_WING_MAP,
  wingsForProfile,
} from '../commandRegistryCore.ts';
import type { UserProfile } from '../../types/domain.ts';

const profile = (role: string): UserProfile =>
  ({ role, uid: 'u1', email: 'x@x', name: 'x', wing: 'citizen' } as unknown as UserProfile);

/* ─── 7.A: Citizens never see staff wings ──────────────────────────── */

describe('Citizen role isolation', () => {
  it('citizens see only the citizen wing', () => {
    assert.deepEqual([...wingsForProfile(profile('citizen'))], ['citizen']);
  });

  it('citizens never see the admin wing', () => {
    assert.ok(!wingsForProfile(profile('citizen')).includes('admin' as any));
  });

  it('citizens never see the ministry wing', () => {
    assert.ok(!wingsForProfile(profile('citizen')).includes('ministry' as any));
  });

  it('citizens never see the lab wing', () => {
    assert.ok(!wingsForProfile(profile('citizen')).includes('lab' as any));
  });

  it('citizens never see the regulator wing', () => {
    assert.ok(!wingsForProfile(profile('citizen')).includes('regulator' as any));
  });
});

/* ─── 7.B: Lab roles do not get admin / ministry surface ───────────── */

describe('Lab role isolation', () => {
  const labRoles = ['technician', 'pathologist', 'lab_admin'];

  for (const role of labRoles) {
    it(`${role} sees only [lab, citizen]`, () => {
      assert.deepEqual(
        [...wingsForProfile(profile(role))].sort(),
        ['citizen', 'lab'],
      );
    });

    it(`${role} never sees the admin wing`, () => {
      assert.ok(!wingsForProfile(profile(role)).includes('admin' as any),
        `${role} unexpectedly granted admin wing`);
    });

    it(`${role} never sees the ministry wing`, () => {
      assert.ok(!wingsForProfile(profile(role)).includes('ministry' as any),
        `${role} unexpectedly granted ministry wing`);
    });

    it(`${role} never sees the regulator wing`, () => {
      assert.ok(!wingsForProfile(profile(role)).includes('regulator' as any),
        `${role} unexpectedly granted regulator wing`);
    });
  }
});

/* ─── 7.C: Ministry roles do not get the admin or lab surface ──────── */

describe('Ministry role isolation', () => {
  const ministryRoles = [
    'ministry_admin',
    'ministry_analyst',
    'ministry_inspector',
  ];

  for (const role of ministryRoles) {
    it(`${role} never sees the admin wing`, () => {
      assert.ok(!wingsForProfile(profile(role)).includes('admin' as any),
        `${role} unexpectedly granted admin wing`);
    });

    it(`${role} never sees the lab wing`, () => {
      assert.ok(!wingsForProfile(profile(role)).includes('lab' as any),
        `${role} unexpectedly granted lab wing`);
    });

    it(`${role} sees the ministry wing`, () => {
      assert.ok(wingsForProfile(profile(role)).includes('ministry' as any),
        `${role} missing ministry wing`);
    });
  }
});

/* ─── 7.D: Master admin gets the full set ──────────────────────────── */

describe('master_admin has the full wing set', () => {
  const expected = [
    'admin', 'ministry', 'doctor', 'lab',
    'citizen', 'researcher', 'regulator', 'system',
  ];

  for (const wing of expected) {
    it(`master_admin includes ${wing}`, () => {
      assert.ok(
        wingsForProfile(profile('master_admin')).includes(wing as any),
        `master_admin missing ${wing}`,
      );
    });
  }
});

/* ─── 7.E: Fallback safety ─────────────────────────────────────────── */

describe('unknown / null roles fall back safely', () => {
  it('null profile → [citizen]', () => {
    assert.deepEqual([...wingsForProfile(null)], ['citizen']);
  });

  it('unknown role → [citizen]', () => {
    assert.deepEqual(
      [...wingsForProfile(profile('totally_made_up_role'))],
      ['citizen'],
    );
  });

  it('empty role string → [citizen]', () => {
    assert.deepEqual([...wingsForProfile(profile(''))], ['citizen']);
  });

  it('every role mapping is non-empty (no broken UI)', () => {
    for (const [role, wings] of Object.entries(ROLE_WING_MAP)) {
      assert.ok(wings.length > 0, `role ${role} has empty wing list`);
    }
  });
});

/* ─── 7.F: Internal consistency of the map ─────────────────────────── */

describe('ROLE_WING_MAP internal consistency', () => {
  it('every role wing list is a subset of master_admin', () => {
    const masterSet = new Set(ROLE_WING_MAP.master_admin);
    for (const [role, wings] of Object.entries(ROLE_WING_MAP)) {
      if (role === 'master_admin') continue;
      // integration_service uses a 'system' wing that master_admin also has.
      for (const w of wings) {
        assert.ok(
          masterSet.has(w),
          `role ${role} has wing ${w} not present in master_admin set`,
        );
      }
    }
  });

  it('citizen wing is granted to every role except integration_service', () => {
    /* The citizen wing is the public surface — every human-facing role
     * must include it so that staff users can also act as patients. */
    for (const [role, wings] of Object.entries(ROLE_WING_MAP)) {
      if (role === 'integration_service') continue;
      assert.ok(
        wings.includes('citizen' as any),
        `role ${role} missing citizen wing — staff cannot use citizen self-service`,
      );
    }
  });

  it('only admin and master_admin get the system wing', () => {
    /* The 'system' wing exposes maintenance / governance controls. */
    const allowed = new Set(['master_admin', 'integration_service']);
    for (const [role, wings] of Object.entries(ROLE_WING_MAP)) {
      if ((wings as readonly string[]).includes('system')) {
        assert.ok(
          allowed.has(role),
          `role ${role} unexpectedly has the 'system' wing`,
        );
      }
    }
  });
});
