import { create } from 'zustand';

export interface PluginManifest {
  id: string;
  name: string;
  version: string;
  description: string;
  author: string;
  permissions: string[];
  entryPoint: string;
  icon?: string;
  dependencies?: string[];
  configSchema?: Record<string, unknown>;
}

export interface PluginInstance {
  manifest: PluginManifest;
  enabled: boolean;
  loaded: boolean;
  module?: unknown;
}

interface PluginState {
  plugins: Map<string, PluginInstance>;
  register: (manifest: PluginManifest) => void;
  enable: (id: string) => void;
  disable: (id: string) => void;
  load: (id: string) => Promise<void>;
  unload: (id: string) => void;
  getPlugin: (id: string) => PluginInstance | undefined;
  getEnabled: () => PluginInstance[];
  isLoaded: (id: string) => boolean;
}

export const usePluginLoader = create<PluginState>((set, get) => ({
  plugins: new Map(),

  register: (manifest: PluginManifest) => {
    set((state) => {
      const next = new Map(state.plugins);
      next.set(manifest.id, { manifest, enabled: true, loaded: false });
      return { plugins: next };
    });
  },

  enable: (id: string) => {
    set((state) => {
      const next = new Map(state.plugins);
      const p = next.get(id);
      if (p) next.set(id, { ...p, enabled: true });
      return { plugins: next };
    });
  },

  disable: (id: string) => {
    set((state) => {
      const next = new Map(state.plugins);
      const p = next.get(id);
      if (p) next.set(id, { ...p, enabled: false, loaded: false });
      return { plugins: next };
    });
  },

  load: async (id: string) => {
    const plugin = get().plugins.get(id);
    if (!plugin || !plugin.enabled || plugin.loaded) return;
    try {
      const module = await import(/* @vite-ignore */ plugin.manifest.entryPoint);
      set((state) => {
        const next = new Map(state.plugins);
        next.set(id, { ...plugin, loaded: true, module });
        return { plugins: next };
      });
    } catch (error) {
      console.error(`[UAP] Failed to load plugin ${id}:`, error);
    }
  },

  unload: (id: string) => {
    set((state) => {
      const next = new Map(state.plugins);
      const p = next.get(id);
      if (p) next.set(id, { ...p, loaded: false, module: undefined });
      return { plugins: next };
    });
  },

  getPlugin: (id: string) => get().plugins.get(id),
  getEnabled: () => Array.from(get().plugins.values()).filter((p) => p.enabled),
  isLoaded: (id: string) => get().plugins.get(id)?.loaded ?? false,
}));
