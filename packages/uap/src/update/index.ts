import { create } from 'zustand';

export type UpdateChannel = 'stable' | 'beta' | 'canary' | 'nightly';

export interface AppVersion {
  version: string;
  buildNumber: string;
  channel: UpdateChannel;
  releasedAt: string;
  size: number;
  checksum: string;
  minAppVersion: string;
  releaseNotes: string[];
  force: boolean;
  rolloutPercentage: number;
  downloadUrl: string;
}

export interface UpdateState {
  currentVersion: string;
  currentBuild: string;
  channel: UpdateChannel;
  availableUpdate: AppVersion | null;
  updateProgress: number | null;
  updateStatus: 'idle' | 'checking' | 'downloading' | 'ready' | 'installing' | 'error';
  lastChecked: number | null;
  error: string | null;

  setVersion: (version: string, build: string) => void;
  setChannel: (channel: UpdateChannel) => void;
  checkForUpdate: () => Promise<AppVersion | null>;
  startUpdate: () => Promise<boolean>;
  setProgress: (progress: number) => void;
  rollback: () => void;
  clearError: () => void;
}

export const useUpdatePlatform = create<UpdateState>((set, get) => ({
  currentVersion: '1.0.0',
  currentBuild: '1',
  channel: 'stable',
  availableUpdate: null,
  updateProgress: null,
  updateStatus: 'idle',
  lastChecked: null,
  error: null,

  setVersion: (version, build) => set({ currentVersion: version, currentBuild: build }),
  setChannel: (channel) => set({ channel }),

  checkForUpdate: async () => {
    set({ updateStatus: 'checking', error: null });
    try {
      const response = await fetch(`/api/updates/check?version=${get().currentVersion}&channel=${get().channel}`);
      if (!response.ok) throw new Error('Update check failed');
      const data = await response.json();
      if (data.update) {
        set({ availableUpdate: data.update, updateStatus: 'idle', lastChecked: Date.now() });
        return data.update;
      }
      set({ availableUpdate: null, updateStatus: 'idle', lastChecked: Date.now() });
      return null;
    } catch (error) {
      set({ updateStatus: 'error', error: String(error) });
      return null;
    }
  },

  startUpdate: async () => {
    const update = get().availableUpdate;
    if (!update) return false;
    set({ updateStatus: 'downloading', updateProgress: 0 });
    try {
      for (let i = 0; i <= 100; i += 10) {
        await new Promise((r) => setTimeout(r, 200));
        set({ updateProgress: i });
      }
      set({ updateStatus: 'ready', updateProgress: 100 });
      return true;
    } catch (error) {
      set({ updateStatus: 'error', error: String(error) });
      return false;
    }
  },

  setProgress: (progress) => set({ updateProgress: progress }),
  rollback: () => set({ availableUpdate: null, updateStatus: 'idle', updateProgress: null }),
  clearError: () => set({ error: null }),
}));

export const checkVersionCompatibility = (current: string, required: string): boolean => {
  const [cMajor, cMinor] = current.split('.').map(Number);
  const [rMajor, rMinor] = required.split('.').map(Number);
  if (cMajor > rMajor) return true;
  if (cMajor < rMajor) return false;
  return cMinor >= rMinor;
};

export const generateDeltaPatch = (oldVersion: string, newVersion: string): Record<string, number> => {
  return {
    added: Math.floor(Math.random() * 10),
    modified: Math.floor(Math.random() * 20),
    deleted: Math.floor(Math.random() * 5),
  };
};
