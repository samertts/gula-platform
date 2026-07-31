import { describe, it, expect } from 'vitest';
import {
  cn,
  formatNumber,
  getFlagColor,
  getStatusColor,
  getGenderLabel,
  getLabTypeLabel,
  getRoleLabel,
  getTierLabel,
  getTierColor,
} from '../utils';

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
  });

  it('handles conditional classes', () => {
    expect(cn('base', false && 'hidden', 'visible')).toBe('base visible');
  });

  it('returns empty string for no args', () => {
    expect(cn()).toBe('');
  });
});

describe('formatNumber', () => {
  it('formats a number', () => {
    const result = formatNumber(1234);
    expect(result).toBeTruthy();
    expect(result).not.toBe('—');
  });

  it('returns dash for null', () => {
    expect(formatNumber(null)).toBe('—');
  });

  it('returns dash for undefined', () => {
    expect(formatNumber(undefined)).toBe('—');
  });
});

describe('getFlagColor', () => {
  it('returns critical color', () => {
    expect(getFlagColor('critical')).toContain('red');
  });

  it('returns high color', () => {
    expect(getFlagColor('high')).toContain('orange');
  });

  it('returns H color', () => {
    expect(getFlagColor('H')).toContain('orange');
  });

  it('returns L color', () => {
    expect(getFlagColor('L')).toContain('yellow');
  });

  it('returns normal color', () => {
    expect(getFlagColor('normal')).toContain('green');
  });

  it('returns default for unknown', () => {
    expect(getFlagColor('unknown')).toContain('gray');
  });

  it('returns default for null', () => {
    expect(getFlagColor(null)).toContain('gray');
  });
});

describe('getStatusColor', () => {
  it('returns green for active', () => {
    expect(getStatusColor('active')).toContain('green');
  });

  it('returns green for completed', () => {
    expect(getStatusColor('completed')).toContain('green');
  });

  it('returns yellow for pending', () => {
    expect(getStatusColor('pending')).toContain('yellow');
  });

  it('returns red for cancelled', () => {
    expect(getStatusColor('cancelled')).toContain('red');
  });

  it('returns red for rejected', () => {
    expect(getStatusColor('rejected')).toContain('red');
  });

  it('returns gray for inactive', () => {
    expect(getStatusColor('inactive')).toContain('gray');
  });

  it('returns blue for unknown', () => {
    expect(getStatusColor('unknown_status')).toContain('blue');
  });
});

describe('getGenderLabel', () => {
  it('returns Arabic male', () => {
    expect(getGenderLabel('M')).toBe('ذكر');
  });

  it('returns Arabic male for male', () => {
    expect(getGenderLabel('male')).toBe('ذكر');
  });

  it('returns Arabic female', () => {
    expect(getGenderLabel('F')).toBe('أنثى');
  });

  it('returns Arabic female for female', () => {
    expect(getGenderLabel('female')).toBe('أنثى');
  });

  it('returns dash for null', () => {
    expect(getGenderLabel(null)).toBe('—');
  });

  it('returns dash for undefined', () => {
    expect(getGenderLabel(undefined)).toBe('—');
  });

  it('passes through unknown value', () => {
    expect(getGenderLabel('other')).toBe('other');
  });
});

describe('getLabTypeLabel', () => {
  it('returns Arabic for private', () => {
    expect(getLabTypeLabel('private')).toBe('خاص');
  });

  it('returns Arabic for government', () => {
    expect(getLabTypeLabel('government')).toBe('حكومي');
  });

  it('returns Arabic for hospital', () => {
    expect(getLabTypeLabel('hospital')).toBe('مستشفى');
  });

  it('returns Arabic for clinic', () => {
    expect(getLabTypeLabel('clinic')).toBe('عيادة');
  });

  it('passes through unknown', () => {
    expect(getLabTypeLabel('other')).toBe('other');
  });
});

describe('getRoleLabel', () => {
  it('returns Arabic for master_admin', () => {
    expect(getRoleLabel('master_admin')).toBe('مدير النظام');
  });

  it('returns Arabic for admin', () => {
    expect(getRoleLabel('admin')).toBe('مدير مختبر');
  });

  it('returns Arabic for lab_admin', () => {
    expect(getRoleLabel('lab_admin')).toBe('مدير مختبر');
  });

  it('returns Arabic for technician', () => {
    expect(getRoleLabel('technician')).toBe('فني مختبر');
  });

  it('returns Arabic for citizen', () => {
    expect(getRoleLabel('citizen')).toBe('مواطن');
  });

  it('passes through unknown role', () => {
    expect(getRoleLabel('unknown')).toBe('unknown');
  });
});

describe('getTierLabel', () => {
  it('returns Arabic for starter', () => {
    expect(getTierLabel('starter')).toBe('البداية');
  });

  it('returns Arabic for growth', () => {
    expect(getTierLabel('growth')).toBe('النمو');
  });

  it('returns Arabic for enterprise', () => {
    expect(getTierLabel('enterprise')).toBe('المؤسسات');
  });

  it('passes through unknown', () => {
    expect(getTierLabel('unknown')).toBe('unknown');
  });
});

describe('getTierColor', () => {
  it('returns gray for starter', () => {
    expect(getTierColor('starter')).toContain('gray');
  });

  it('returns blue for growth', () => {
    expect(getTierColor('growth')).toContain('blue');
  });

  it('returns purple for enterprise', () => {
    expect(getTierColor('enterprise')).toContain('purple');
  });

  it('returns default for unknown', () => {
    expect(getTierColor('unknown')).toContain('gray');
  });
});
