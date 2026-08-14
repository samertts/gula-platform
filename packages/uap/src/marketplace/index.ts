import { create } from 'zustand';

export interface AppStoreEntry {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  icon?: string;
  category: AppCategory;
  screenshots?: string[];
  permissions: string[];
  price: number;
  rating: number;
  downloads: number;
  publishedAt: string;
  updatedAt: string;
  approved: boolean;
  status: 'draft' | 'submitted' | 'approved' | 'rejected' | 'published';
  minPlatformVersion: string;
  size: number;
}

export type AppCategory =
  | 'citizen' | 'doctor' | 'nurse' | 'laboratory' | 'hospital'
  | 'pharmacy' | 'inspector' | 'research' | 'administrator' | 'plugin' | 'extension';

export interface Extension {
  id: string;
  appId: string;
  name: string;
  description: string;
  version: string;
  type: 'plugin' | 'theme' | 'language' | 'integration';
  permissions: string[];
  entryPoint: string;
}

interface MarketplaceState {
  apps: AppStoreEntry[];
  extensions: Extension[];
  installedApps: Set<string>;
  installQueue: string[];
  searchQuery: string;
  category: AppCategory | 'all';

  setApps: (apps: AppStoreEntry[]) => void;
  addApp: (app: AppStoreEntry) => void;
  updateApp: (id: string, updates: Partial<AppStoreEntry>) => void;
  approveApp: (id: string) => void;
  rejectApp: (id: string) => void;
  installApp: (id: string) => Promise<void>;
  uninstallApp: (id: string) => void;
  search: (query: string) => AppStoreEntry[];
  filterByCategory: (category: AppCategory | 'all') => AppStoreEntry[];
  addExtension: (ext: Extension) => void;
  getExtensions: (appId: string) => Extension[];
  isInstalled: (id: string) => boolean;
}

export const CATEGORY_ROLES: Record<AppCategory, string> = {
  citizen: 'citizen',
  doctor: 'doctor',
  nurse: 'nurse',
  laboratory: 'lab_technician',
  hospital: 'hospital_admin',
  pharmacy: 'pharmacist',
  inspector: 'inspector',
  research: 'researcher',
  administrator: 'admin',
  plugin: 'admin',
  extension: 'admin',
};

export const useMarketplace = create<MarketplaceState>((set, get) => ({
  apps: [],
  extensions: [],
  installedApps: new Set(),
  installQueue: [],
  searchQuery: '',
  category: 'all',

  setApps: (apps) => set({ apps }),
  addApp: (app) => set((state) => ({ apps: [...state.apps, app] })),
  updateApp: (id, updates) => {
    set((state) => ({
      apps: state.apps.map((a) => (a.id === id ? { ...a, ...updates } : a)),
    }));
  },

  approveApp: (id) => {
    set((state) => ({
      apps: state.apps.map((a) => (a.id === id ? { ...a, approved: true, status: 'published' } : a)),
    }));
  },

  rejectApp: (id) => {
    set((state) => ({
      apps: state.apps.map((a) => (a.id === id ? { ...a, approved: false, status: 'rejected' } : a)),
    }));
  },

  installApp: async (id) => {
    set((state) => ({ installQueue: [...state.installQueue, id] }));
    await new Promise((r) => setTimeout(r, 1000));
    set((state) => {
      const next = new Set(state.installedApps);
      next.add(id);
      return {
        installedApps: next,
        installQueue: state.installQueue.filter((i) => i !== id),
      };
    });
  },

  uninstallApp: (id) => {
    set((state) => {
      const next = new Set(state.installedApps);
      next.delete(id);
      return { installedApps: next };
    });
  },

  search: (query: string) => {
    const q = query.toLowerCase();
    return get().apps.filter(
      (app) =>
        app.name.toLowerCase().includes(q) ||
        app.description.toLowerCase().includes(q) ||
        app.author.toLowerCase().includes(q)
    );
  },

  filterByCategory: (category) => {
    if (category === 'all') return get().apps;
    return get().apps.filter((app) => app.category === category);
  },

  addExtension: (ext) => set((state) => ({ extensions: [...state.extensions, ext] })),
  getExtensions: (appId) => get().extensions.filter((e) => e.appId === appId),
  isInstalled: (id) => get().installedApps.has(id),
}));
