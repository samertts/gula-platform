import { create } from 'zustand';
import { z } from 'zod';

export const appConfigSchema = z.object({
  appName: z.string().default('GULA Platform'),
  version: z.string().default('1.0.0'),
  apiUrl: z.string().url().default('http://localhost:8000'),
  environment: z.enum(['development', 'staging', 'production']).default('development'),
  buildNumber: z.string().optional(),
  debug: z.boolean().default(false),
  offlineEnabled: z.boolean().default(true),
  telemetryEnabled: z.boolean().default(true),
  updateCheckInterval: z.number().default(3600000),
  sessionTimeout: z.number().default(3600000),
  maxUploadSize: z.number().default(10485760),
  supportedLocales: z.array(z.string()).default(['ar', 'en', 'ku']),
});

export type AppConfig = z.infer<typeof appConfigSchema>;

interface ConfigState {
  config: AppConfig;
  isHydrated: boolean;
  setConfig: (config: Partial<AppConfig>) => void;
  getConfig: () => AppConfig;
  resetConfig: () => void;
}

const defaultConfig: AppConfig = appConfigSchema.parse({});

export const useConfig = create<ConfigState>((set, get) => ({
  config: defaultConfig,
  isHydrated: false,

  setConfig: (partial: Partial<AppConfig>) => {
    const merged = { ...get().config, ...partial };
    const parsed = appConfigSchema.parse(merged);
    set({ config: parsed, isHydrated: true });
    try {
      localStorage.setItem('gula-config', JSON.stringify(parsed));
    } catch {}
  },

  getConfig: () => get().config,

  resetConfig: () => {
    set({ config: defaultConfig });
    try { localStorage.removeItem('gula-config'); } catch {}
  },
}));

export const hydrateConfig = () => {
  try {
    const stored = localStorage.getItem('gula-config');
    if (stored) {
      const parsed = appConfigSchema.parse(JSON.parse(stored));
      useConfig.getState().setConfig(parsed);
    }
  } catch {
    useConfig.getState().setConfig(defaultConfig);
  }
};
