export interface MockConfig {
  enabled: boolean;
  latency: number;
  errorRate: number;
  demoMode: boolean;
  featureFlags: Record<string, boolean>;
}

const config: MockConfig = {
  enabled: import.meta.env.VITE_USE_MOCK === 'true',
  latency: parseInt(import.meta.env.VITE_MOCK_LATENCY || '200'),
  errorRate: 0,
  demoMode: import.meta.env.VITE_DEMO_MODE === 'true',
  featureFlags: {
    ai: import.meta.env.VITE_FEATURE_AI !== 'false',
    ocr: import.meta.env.VITE_FEATURE_OCR !== 'false',
    fhir: import.meta.env.VITE_FEATURE_FHIR !== 'false',
    notifications: import.meta.env.VITE_FEATURE_NOTIFICATIONS !== 'false',
    analytics: import.meta.env.VITE_FEATURE_ANALYTICS !== 'false',
    knowledgeGraph: import.meta.env.VITE_FEATURE_KNOWLEDGE_GRAPH !== 'false',
    experimental: import.meta.env.VITE_FEATURE_EXPERIMENTAL === 'true',
  },
};

export function getConfig(): MockConfig {
  return { ...config };
}

export function setConfig(updates: Partial<MockConfig>): void {
  Object.assign(config, updates);
}

export function isFeatureEnabled(feature: string): boolean {
  return config.featureFlags[feature] !== false;
}

export function setFeatureFlag(feature: string, enabled: boolean): void {
  config.featureFlags[feature] = enabled;
}
