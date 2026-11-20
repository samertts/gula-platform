import { describe, expect, it } from 'vitest';
import { coreLanguages, getLanguage, gulsRegistry } from './registry';
import {
  directionFor,
  formatIdentifier,
  formatNumber,
  resolveLanguage,
  stableMessage,
  translateKey,
} from './runtime';
import { containerAttributes, logicalDirectionStyles } from './rtl';

describe('GULS registry', () => {
  it('contains five core entries and English fallback', () => {
    expect(coreLanguages()).toHaveLength(5);
    expect(gulsRegistry.fallbackLanguage).toBe('en');
  });

  it('resolves locale tags separately from internal IDs', () => {
    expect(getLanguage('fa-IR')?.language_id).toBe('fa');
    expect(getLanguage('PENDING_SYRIAC')?.is_publishable).toBe(false);
  });
});

describe('GULS runtime', () => {
  it('uses English fallback for an uninstalled language', () => {
    const result = resolveLanguage('fa', new Set(['en']), 'ar');
    expect(result.selected).toBe('en');
    expect(result.reason).toBe('mandatory_fallback');
  });

  it('uses a ready requested language', () => {
    const result = resolveLanguage('ckb', new Set(['en', 'ckb']), 'en');
    expect(result.selected).toBe('ckb');
    expect(result.direction).toBe('rtl');
  });

  it('never returns raw translation keys', () => {
    const result = translateKey({}, { 'ui.save': 'Save' }, 'ui.save');
    expect(result.text).toBe('Save');
    expect(translateKey({}, {}, 'ui.save').text).toBe('');
  });

  it('falls back to English when a localized value is empty', () => {
    const result = translateKey({ 'ui.save': '' }, { 'ui.save': 'Save' }, 'ui.save');
    expect(result.text).toBe('Save');
    expect(result.fallbackUsed).toBe(true);
  });

  it('formats numbers without mutating identifiers', () => {
    expect(formatNumber('1234', 'ar')).not.toBe('1234');
    expect(formatIdentifier('LAB-1234.5')).toBe('LAB-1234.5');
    expect(directionFor('en')).toBe('ltr');
  });

  it('emits stable error codes without translated prose', () => {
    expect(stableMessage('PATIENT_NOT_FOUND', { id: 'SYNTHETIC-1' })).toEqual({
      code: 'PATIENT_NOT_FOUND',
      parameters: { id: 'SYNTHETIC-1' },
    });
    expect(() => stableMessage('patient not found')).toThrow();
  });

  it('uses logical CSS properties and container direction', () => {
    expect(logicalDirectionStyles.marginStart).toBe('margin-inline-start');
    expect(containerAttributes('rtl', 'ar')).toEqual({ dir: 'rtl', lang: 'ar' });
  });
});
