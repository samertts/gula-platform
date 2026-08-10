import { describe, it, expect } from 'vitest';
import { parseDemoConfig, type DemoConfig } from '../config';

const NOW = new Date('2026-08-10T12:00:00Z');
const FUTURE = '2026-12-31T23:59:59Z';
const PAST = '2026-01-01T00:00:00Z';

function expectDisabled(cfg: DemoConfig, reason: string) {
  expect(cfg.enabled).toBe(false);
  expect(cfg.reason).toBe(reason);
}

describe('parseDemoConfig', () => {
  it('is disabled by default when the enable flag is missing', () => {
    expectDisabled(parseDemoConfig(undefined, FUTURE, NOW), 'disabled_by_config');
  });

  it('is disabled when enable flag is false', () => {
    expectDisabled(parseDemoConfig('false', FUTURE, NOW), 'disabled_by_config');
  });

  it('is disabled when enable flag is an empty string', () => {
    expectDisabled(parseDemoConfig('', FUTURE, NOW), 'disabled_by_config');
  });

  it('is enabled when the flag is true and expiry is a future timestamp', () => {
    const cfg = parseDemoConfig('true', FUTURE, NOW);
    expect(cfg.enabled).toBe(true);
    expect(cfg.reason).toBeNull();
    expect(cfg.expiresAt).toBe(FUTURE);
  });

  it('accepts TRUE / yes / 1 as truthy', () => {
    expect(parseDemoConfig('TRUE', FUTURE, NOW).enabled).toBe(true);
    expect(parseDemoConfig('yes', FUTURE, NOW).enabled).toBe(true);
    expect(parseDemoConfig('1', FUTURE, NOW).enabled).toBe(true);
  });

  it('fails closed when enabled but expiry is missing', () => {
    expectDisabled(parseDemoConfig('true', undefined, NOW), 'expiry_missing');
  });

  it('fails closed when enabled but expiry is an empty string', () => {
    expectDisabled(parseDemoConfig('true', '', NOW), 'expiry_missing');
  });

  it('fails closed when the expiry value is invalid', () => {
    expectDisabled(parseDemoConfig('true', 'not-a-timestamp', NOW), 'expiry_invalid');
  });

  it('fails closed when the expiry is in the past', () => {
    expectDisabled(parseDemoConfig('true', PAST, NOW), 'expired');
  });

  it('fails closed exactly at the expiry instant', () => {
    const cfg = parseDemoConfig('true', '2026-08-10T12:00:00Z', NOW);
    expect(cfg.enabled).toBe(false);
    expect(cfg.reason).toBe('expired');
  });

  it('is enabled when now is strictly before the expiry', () => {
    expect(parseDemoConfig('true', '2026-08-10T12:00:01Z', NOW).enabled).toBe(true);
  });

  it('keeps the enabled flag reported by the environment even when expired', () => {
    const cfg = parseDemoConfig('true', PAST, NOW);
    expect(cfg.enabledByEnv).toBe(true);
    expect(cfg.enabled).toBe(false);
  });
});

