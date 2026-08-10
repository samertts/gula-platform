import { describe, it, expect } from 'vitest';
import { DEMO_VIEWS } from '../mockData';
import { DEMO_PROFILE_IDS } from '../profiles';

describe('demo mock data', () => {
  it('provides a view for every demo profile', () => {
    for (const id of DEMO_PROFILE_IDS) {
      expect(DEMO_VIEWS[id]).toBeDefined();
    }
  });

  it('contains no real-looking phone numbers', () => {
    const text = JSON.stringify(DEMO_VIEWS);
    expect(text.match(/07\d{8}/)).toBeNull();
  });

  it('contains no real-looking 10-digit national IDs', () => {
    const text = JSON.stringify(DEMO_VIEWS);
    expect(text.match(/\b\d{10}\b/)).toBeNull();
  });

  it('is explicitly marked as demo / synthetic', () => {
    const text = JSON.stringify(DEMO_VIEWS);
    expect(text).toMatch(/تجريبي/);
    expect(text).toMatch(/DEMO/);
  });
});
