import { create } from 'zustand';

export type FeatureFlag = {
  key: string;
  enabled: boolean;
  description?: string;
  dependencies?: string[];
  rolloutPercentage?: number;
};

interface FeatureState {
  flags: Map<string, FeatureFlag>;
  registerFlag: (flag: FeatureFlag) => void;
  isEnabled: (key: string) => boolean;
  enableFlag: (key: string) => void;
  disableFlag: (key: string) => void;
  setRollout: (key: string, percentage: number) => void;
  getFlag: (key: string) => FeatureFlag | undefined;
  getAllFlags: () => FeatureFlag[];
}

export const useFeatureFlags = create<FeatureState>((set, get) => ({
  flags: new Map(),

  registerFlag: (flag: FeatureFlag) => {
    set((state) => {
      const next = new Map(state.flags);
      next.set(flag.key, flag);
      return { flags: next };
    });
  },

  isEnabled: (key: string): boolean => {
    const flag = get().flags.get(key);
    if (!flag) return false;
    if (!flag.enabled) return false;
    if (flag.dependencies) {
      for (const dep of flag.dependencies) {
        if (!get().isEnabled(dep)) return false;
      }
    }
    if (flag.rolloutPercentage !== undefined && flag.rolloutPercentage < 100) {
      const hash = key.split('').reduce((a, c) => a + c.charCodeAt(0), 0);
      return hash % 100 < flag.rolloutPercentage;
    }
    return true;
  },

  enableFlag: (key: string) => {
    set((state) => {
      const next = new Map(state.flags);
      const f = next.get(key);
      if (f) next.set(key, { ...f, enabled: true });
      return { flags: next };
    });
  },

  disableFlag: (key: string) => {
    set((state) => {
      const next = new Map(state.flags);
      const f = next.get(key);
      if (f) next.set(key, { ...f, enabled: false });
      return { flags: next };
    });
  },

  setRollout: (key: string, percentage: number) => {
    set((state) => {
      const next = new Map(state.flags);
      const f = next.get(key);
      if (f) next.set(key, { ...f, rolloutPercentage: percentage });
      return { flags: next };
    });
  },

  getFlag: (key: string) => get().flags.get(key),
  getAllFlags: () => Array.from(get().flags.values()),
}));
