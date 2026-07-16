import { create } from 'zustand';

interface CrashRecord {
  id: string;
  timestamp: number;
  error: string;
  stack?: string;
  context?: Record<string, unknown>;
  recovered: boolean;
}

interface RecoveryState {
  records: CrashRecord[];
  recoveryAttempts: number;
  lastRecoveryTime: number | null;
  recordCrash: (error: string, stack?: string, context?: Record<string, unknown>) => void;
  markRecovered: (id: string) => void;
  getPending: () => CrashRecord[];
  shouldRecover: () => boolean;
  clearHistory: () => void;
}

export const useCrashRecovery = create<RecoveryState>((set, get) => ({
  records: [],
  recoveryAttempts: 0,
  lastRecoveryTime: null,

  recordCrash: (error: string, stack?: string, context?: Record<string, unknown>) => {
    const record: CrashRecord = {
      id: `crash-${Date.now()}`,
      timestamp: Date.now(),
      error,
      stack,
      context,
      recovered: false,
    };
    set((state) => ({
      records: [record, ...state.records].slice(0, 20),
      recoveryAttempts: state.recoveryAttempts + 1,
      lastRecoveryTime: Date.now(),
    }));
  },

  markRecovered: (id: string) => {
    set((state) => ({
      records: state.records.map((r) => (r.id === id ? { ...r, recovered: true } : r)),
    }));
  },

  getPending: () => get().records.filter((r) => !r.recovered),

  shouldRecover: () => {
    const { recoveryAttempts, lastRecoveryTime } = get();
    if (recoveryAttempts > 5) return false;
    if (lastRecoveryTime && Date.now() - lastRecoveryTime < 5000) return false;
    return true;
  },

  clearHistory: () => set({ records: [], recoveryAttempts: 0, lastRecoveryTime: null }),
}));

export const attemptRecovery = async (): Promise<boolean> => {
  const state = useCrashRecovery.getState();
  if (!state.shouldRecover()) return false;
  try {
    localStorage.clear();
    sessionStorage.clear();
    useCrashRecovery.getState().records.forEach((r) => useCrashRecovery.getState().markRecovered(r.id));
    window.location.reload();
    return true;
  } catch {
    return false;
  }
};
