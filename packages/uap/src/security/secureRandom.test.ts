import { describe, expect, it } from 'vitest';

import { secureId, secureRandomHex, secureRandomInt } from './secureRandom';

describe('secure random helpers', () => {
  it('returns the requested hexadecimal length', () => {
    expect(secureRandomHex(8)).toMatch(/^[0-9a-f]{16}$/);
  });

  it('creates prefixed identifiers with a random suffix', () => {
    const first = secureId('test');
    const second = secureId('test');
    expect(first).toMatch(/^test-\d+-[0-9a-f]{16}$/);
    expect(second).toMatch(/^test-\d+-[0-9a-f]{16}$/);
    expect(first).not.toBe(second);
  });

  it('returns values inside the requested range', () => {
    for (let index = 0; index < 20; index += 1) {
      const value = secureRandomInt(7);
      expect(value).toBeGreaterThanOrEqual(0);
      expect(value).toBeLessThan(7);
    }
    expect(secureRandomInt(1)).toBe(0);
  });

  it('rejects invalid bounds', () => {
    expect(() => secureRandomInt(0)).toThrow(RangeError);
    expect(() => secureRandomInt(-1)).toThrow(RangeError);
    expect(() => secureRandomHex(0)).toThrow(RangeError);
  });
});
