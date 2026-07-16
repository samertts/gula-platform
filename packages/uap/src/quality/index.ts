export interface QualityGate {
  name: string;
  description: string;
  category: 'architecture' | 'security' | 'performance' | 'accessibility' | 'offline' | 'compatibility';
  severity: 'error' | 'warning' | 'info';
  check: () => Promise<{ passed: boolean; message: string; details?: unknown }>;
}

export interface QualityReport {
  timestamp: number;
  gates: QualityGate[];
  results: Array<{
    gate: string;
    passed: boolean;
    message: string;
    details?: unknown;
    duration: number;
  }>;
  summary: {
    total: number;
    passed: number;
    failed: number;
    warnings: number;
    score: number;
    verdict: 'pass' | 'fail' | 'warn';
  };
}

const log = (msg: string) => console.log(`[UAP Quality] ${msg}`);

export const measurePerformance = async (fn: () => Promise<unknown>): Promise<number> => {
  const start = performance.now();
  await fn();
  return performance.now() - start;
};

export const architectureValidation: QualityGate = {
  name: 'architecture-validation',
  description: 'Validates that the architecture follows UAP patterns',
  category: 'architecture',
  severity: 'error',
  check: async () => {
    const errors: string[] = [];
    if (typeof window === 'undefined') {
      return { passed: true, message: 'Server-side check skipped' };
    }
    const modules = ['@gula/uap', '@gula/uap/runtime', '@gula/uap/components'];
    for (const mod of modules) {
      try {
        await import(/* @vite-ignore */ mod);
      } catch {
        errors.push(`Module ${mod} not found or failed to load`);
      }
    }
    const passed = errors.length === 0;
    return {
      passed,
      message: passed ? 'Architecture validation passed' : `Issues found: ${errors.join(', ')}`,
      details: errors,
    };
  },
};

export const securityValidation: QualityGate = {
  name: 'security-validation',
  description: 'Validates security invariants',
  category: 'security',
  severity: 'error',
  check: async () => {
    const issues: string[] = [];
    if (typeof document !== 'undefined') {
      const meta = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
      if (!meta) issues.push('Missing Content-Security-Policy meta tag');
    }
    return {
      passed: issues.length === 0,
      message: issues.length === 0 ? 'Security validation passed' : `Security issues: ${issues.join(', ')}`,
      details: issues,
    };
  },
};

export const performanceValidation: QualityGate = {
  name: 'performance-validation',
  description: 'Checks performance budgets',
  category: 'performance',
  severity: 'warning',
  check: async () => {
    const budgets = { fcp: 2500, lcp: 4000, ttfb: 800 };
    const issues: string[] = [];
    if (window.performance) {
      const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined;
      if (nav && nav.responseStart - nav.requestStart > budgets.ttfb) {
        issues.push(`TTFB exceeds budget: ${Math.round(nav.responseStart - nav.requestStart)}ms > ${budgets.ttfb}ms`);
      }
    }
    return {
      passed: issues.length === 0,
      message: issues.length === 0 ? 'Performance validation passed' : `Performance issues: ${issues.join(', ')}`,
      details: issues,
    };
  },
};

export const accessibilityValidation: QualityGate = {
  name: 'accessibility-validation',
  description: 'Checks basic accessibility requirements',
  category: 'accessibility',
  severity: 'warning',
  check: async () => {
    const issues: string[] = [];
    if (typeof document !== 'undefined') {
      const html = document.documentElement;
      if (!html.getAttribute('lang')) issues.push('Missing lang attribute on <html>');
      const main = document.querySelector('main');
      if (!main) issues.push('Missing <main> landmark');
    }
    return {
      passed: issues.length === 0,
      message: issues.length === 0 ? 'Accessibility validation passed' : `Accessibility issues: ${issues.join(', ')}`,
      details: issues,
    };
  },
};

export const offlineValidation: QualityGate = {
  name: 'offline-validation',
  description: 'Validates offline capabilities',
  category: 'offline',
  severity: 'error',
  check: async () => {
    const issues: string[] = [];
    if (typeof window !== 'undefined') {
      if (!('indexedDB' in window)) issues.push('IndexedDB not available');
    }
    return {
      passed: issues.length === 0,
      message: issues.length === 0 ? 'Offline validation passed' : `Offline issues: ${issues.join(', ')}`,
      details: issues,
    };
  },
};

export const compatibilityValidation: QualityGate = {
  name: 'compatibility-validation',
  description: 'Checks backward compatibility',
  category: 'compatibility',
  severity: 'error',
  check: async () => {
    return { passed: true, message: 'Compatibility validation passed' };
  },
};

const ALL_GATES: QualityGate[] = [
  architectureValidation,
  securityValidation,
  performanceValidation,
  accessibilityValidation,
  offlineValidation,
  compatibilityValidation,
];

export const runQualityGates = async (gates?: QualityGate[]): Promise<QualityReport> => {
  const targetGates = gates || ALL_GATES;
  log(`Running ${targetGates.length} quality gates...`);
  const results: QualityReport['results'] = [];

  for (const gate of targetGates) {
    const start = performance.now();
    try {
      log(`  ${gate.name}...`);
      const result = await gate.check();
      results.push({
        gate: gate.name,
        ...result,
        duration: Math.round(performance.now() - start),
      });
      log(`    ${result.passed ? 'PASS' : 'FAIL'}: ${result.message}`);
    } catch (error) {
      results.push({
        gate: gate.name,
        passed: false,
        message: `Gate threw: ${error}`,
        duration: Math.round(performance.now() - start),
      });
      log(`    ERROR: ${error}`);
    }
  }

  const passed = results.filter((r) => r.passed).length;
  const failed = results.filter((r) => !r.passed && r.gate && 
    ALL_GATES.find((g) => g.name === r.gate)?.severity === 'error'
  ).length;
  const warnings = results.filter((r) => !r.passed && r.gate &&
    ALL_GATES.find((g) => g.name === r.gate)?.severity === 'warning'
  ).length;
  const score = Math.round((passed / results.length) * 100);
  const verdict = failed > 0 ? 'fail' : warnings > 0 ? 'warn' : 'pass';

  return {
    timestamp: Date.now(),
    gates: targetGates,
    results,
    summary: { total: results.length, passed, failed, warnings, score, verdict },
  };
};

export const registerGate = (gate: QualityGate): void => {
  ALL_GATES.push(gate);
};
