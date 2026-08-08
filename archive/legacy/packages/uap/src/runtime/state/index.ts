import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type AppView =
  | 'dashboard'
  | 'patients'
  | 'appointments'
  | 'lab'
  | 'results'
  | 'settings'
  | 'admin'
  | 'citizen'
  | 'ministry'
  | 'research';

export type NavigationTab = {
  id: string;
  label: string;
  path: string;
  icon?: string;
  badge?: number;
  permissions?: string[];
};

export interface SessionInfo {
  id: string;
  startedAt: number;
  lastActivity: number;
  device: string;
  ip?: string;
}

interface AppState {
  currentView: AppView;
  navigation: NavigationTab[];
  activeTab: string | null;
  breadcrumbs: { label: string; path: string }[];
  session: SessionInfo | null;
  sidebarOpen: boolean;
  sidebarPinned: boolean;

  setView: (view: AppView) => void;
  setNavigation: (tabs: NavigationTab[]) => void;
  setActiveTab: (id: string | null) => void;
  setBreadcrumbs: (crumbs: { label: string; path: string }[]) => void;
  setSession: (session: SessionInfo) => void;
  updateActivity: () => void;
  toggleSidebar: () => void;
  pinSidebar: (pinned: boolean) => void;
}

export const useAppState = create<AppState>()(
  persist(
    (set, get) => ({
      currentView: 'dashboard',
      navigation: [],
      activeTab: null,
      breadcrumbs: [],
      session: null,
      sidebarOpen: true,
      sidebarPinned: false,

      setView: (view) => set({ currentView: view }),
      setNavigation: (navigation) => set({ navigation }),
      setActiveTab: (id) => set({ activeTab: id }),
      setBreadcrumbs: (breadcrumbs) => set({ breadcrumbs }),
      setSession: (session) => set({ session }),
      updateActivity: () => {
        const s = get().session;
        if (s) set({ session: { ...s, lastActivity: Date.now() } });
      },
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      pinSidebar: (pinned) => set({ sidebarPinned: pinned, sidebarOpen: true }),
    }),
    {
      name: 'gula-app-state',
      partialize: (state) => ({
        sidebarPinned: state.sidebarPinned,
        currentView: state.currentView,
      }),
    }
  )
);
