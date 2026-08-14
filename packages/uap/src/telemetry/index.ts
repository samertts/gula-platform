import { create } from 'zustand';
import { secureId } from '../security/secureRandom';

export type MetricType = 'counter' | 'gauge' | 'histogram' | 'timing';

export interface Metric {
  name: string;
  type: MetricType;
  value: number;
  labels?: Record<string, string>;
  timestamp: number;
}

export interface TelemetryEvent {
  type: string;
  category: string;
  action: string;
  label?: string;
  value?: number;
  metadata?: Record<string, unknown>;
  timestamp: number;
}

export interface CrashReport {
  id: string;
  error: string;
  stack?: string;
  componentStack?: string;
  browserInfo: string;
  url: string;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

export interface PerformanceMetrics {
  fcp: number;
  lcp: number;
  fid: number;
  cls: number;
  ttfb: number;
  domInteractive: number;
  domComplete: number;
}

interface TelemetryState {
  metrics: Metric[];
  events: TelemetryEvent[];
  crashes: CrashReport[];
  performance: PerformanceMetrics | null;
  enabled: boolean;
  privacyMode: boolean;
  sessionId: string;
  startTime: number;

  trackMetric: (name: string, value: number, type?: MetricType, labels?: Record<string, string>) => void;
  trackEvent: (category: string, action: string, label?: string, value?: number, metadata?: Record<string, unknown>) => void;
  reportCrash: (report: Omit<CrashReport, 'id' | 'timestamp' | 'browserInfo' | 'url'>) => void;
  setPerformance: (metrics: PerformanceMetrics) => void;
  setEnabled: (enabled: boolean) => void;
  setPrivacyMode: (privacy: boolean) => void;
  getMetrics: (name?: string) => Metric[];
  getSessionDuration: () => number;
  clearMetrics: () => void;
}

const generateSessionId = (): string => secureId('sess');

export const useTelemetry = create<TelemetryState>((set, get) => ({
  metrics: [],
  events: [],
  crashes: [],
  performance: null,
  enabled: true,
  privacyMode: true,
  sessionId: generateSessionId(),
  startTime: Date.now(),

  trackMetric: (name, value, type = 'gauge', labels) => {
    if (!get().enabled) return;
    set((state) => ({
      metrics: [
        ...state.metrics.slice(-999),
        { name, type, value, labels, timestamp: Date.now() },
      ],
    }));
  },

  trackEvent: (category, action, label, value, metadata) => {
    if (!get().enabled) return;
    set((state) => ({
      events: [
        ...state.events.slice(-99),
        { type: `${category}:${action}`, category, action, label, value, metadata, timestamp: Date.now() },
      ],
    }));
  },

  reportCrash: (report) => {
    if (!get().enabled) return;
    const crash: CrashReport = {
      ...report,
      id: secureId('crash'),
      browserInfo: navigator.userAgent,
      url: window.location.href,
      timestamp: Date.now(),
    };
    set((state) => ({
      crashes: [...state.crashes.slice(-49), crash],
    }));
  },

  setPerformance: (metrics) => set({ performance: metrics }),
  setEnabled: (enabled) => set({ enabled }),
  setPrivacyMode: (privacy) => set({ privacyMode: privacy }),
  getMetrics: (name) =>
    name
      ? get().metrics.filter((m) => m.name === name)
      : get().metrics,
  getSessionDuration: () => Date.now() - get().startTime,
  clearMetrics: () => set({ metrics: [], events: [] }),
}));

export const initTelemetry = () => {
  if (typeof window === 'undefined') return;
  const telemetry = useTelemetry.getState();
  if (!telemetry.enabled) return;

  // Track page load performance
  if (window.performance) {
    window.addEventListener('load', () => {
      setTimeout(() => {
        const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined;
        if (nav) {
          telemetry.setPerformance({
            fcp: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0,
            lcp: 0,
            fid: 0,
            cls: 0,
            ttfb: nav.responseStart - nav.requestStart,
            domInteractive: nav.domInteractive,
            domComplete: nav.domComplete,
          });
        }
      }, 2000);
    });
  }

  // Track errors
  window.addEventListener('error', (event) => {
    telemetry.reportCrash({
      error: event.message || 'Unknown error',
      stack: event.error?.stack,
      metadata: { filename: event.filename, lineno: event.lineno, colno: event.colno },
    });
  });

  window.addEventListener('unhandledrejection', (event) => {
    telemetry.reportCrash({
      error: 'Unhandled Promise Rejection',
      stack: event.reason?.stack,
      metadata: { reason: String(event.reason) },
    });
  });

  // Track online/offline
  window.addEventListener('online', () => telemetry.trackMetric('network_online', 1, 'gauge'));
  window.addEventListener('offline', () => telemetry.trackMetric('network_online', 0, 'gauge'));
};

export const trackLatency = (name: string) => {
  const start = performance.now();
  return () => {
    const duration = performance.now() - start;
    useTelemetry.getState().trackMetric(`latency_${name}`, Math.round(duration), 'timing');
  };
};

export const trackBattery = async () => {
  if (!('getBattery' in navigator)) return;
  try {
    const battery = await (navigator as any).getBattery();
    useTelemetry.getState().trackMetric('battery_level', battery.level * 100, 'gauge', { charging: String(battery.charging) });
    battery.addEventListener('levelchange', () => {
      useTelemetry.getState().trackMetric('battery_level', battery.level * 100, 'gauge', { charging: String(battery.charging) });
    });
  } catch {}
};

export const trackMemory = () => {
  if ('memory' in performance) {
    const mem = (performance as any).memory;
    useTelemetry.getState().trackMetric('memory_used', mem.usedJSHeapSize / 1048576, 'gauge');
    useTelemetry.getState().trackMetric('memory_total', mem.totalJSHeapSize / 1048576, 'gauge');
  }
};
