import {createContext, useContext, useReducer, useCallback, ReactNode} from 'react';
const STORAGE_KEYS = {
  favorites: 'gula_nav_favorites',
  recent: 'gula_nav_recent',
  usage: 'gula_nav_usage',
  pinned: 'gula_nav_pinned',
  collapsed: 'gula_sidebar_collapsed',
  bookmarks: 'gula_nav_bookmarks',
};
interface UsageEntry {
  path: string;
  count: number;
  lastUsed: number;
}
export interface NavItem {
  to: string;
  icon: string;
  label: string;
  description?: string;
  keywords?: string[];
  badge?: number;
}
export interface NavGroup {
  id: string;
  icon: string;
  label: string;
  items: NavItem[];
  roles?: string[];
}
interface NavigationState {
  favorites: string[];
  recent: string[];
  usage: Record<string, UsageEntry>;
  pinned: string[];
  bookmarks: string[];
  isCollapsed: boolean;
  searchQuery: string;
  expandedGroups: Record<string, boolean>;
  customOrder: Record<string, number>;
}
type NavigationAction =
  | { type: 'SET_FAVORITES'; payload: string[] }
  | { type: 'SET_RECENT'; payload: string[] }
  | { type: 'SET_USAGE'; payload: Record<string, UsageEntry> }
  | { type: 'TOGGLE_FAVORITE'; payload: string }
  | { type: 'TOGGLE_PINNED'; payload: string }
  | { type: 'TOGGLE_BOOKMARK'; payload: string }
  | { type: 'TRACK_VISIT'; payload: string }
  | { type: 'SET_COLLAPSED'; payload: boolean }
  | { type: 'SET_SEARCH'; payload: string }
  | { type: 'TOGGLE_GROUP'; payload: string }
  | { type: 'SET_CUSTOM_ORDER'; payload: Record<string, number> }
  | { type: 'REORDER_ITEM'; payload: { path: string; newIndex: number } }
  | { type: 'LOAD_PERSISTED'; payload: Partial<NavigationState> };
function loadJson(key: string) {
  try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : null; } catch { return null; }
}
function getInitialState(): NavigationState {
  return {
    favorites: loadJson(STORAGE_KEYS.favorites) || [],
    recent: loadJson(STORAGE_KEYS.recent) || [],
    usage: loadJson(STORAGE_KEYS.usage) || {},
    pinned: loadJson(STORAGE_KEYS.pinned) || [],
    bookmarks: [],
    isCollapsed: loadJson(STORAGE_KEYS.collapsed) ?? true,
    searchQuery: '',
    expandedGroups: {},
    customOrder: {},
  };
}
function navigationReducer(state: NavigationState, action: NavigationAction): NavigationState {
  switch (action.type) {
    case 'TOGGLE_FAVORITE': {
      const path = action.payload;
      const next = state.favorites.includes(path)
        ? state.favorites.filter(p => p !== path)
        : [...state.favorites, path];
      try { localStorage.setItem(STORAGE_KEYS.favorites, JSON.stringify(next)); } catch {}
      return { ...state, favorites: next };
    }
    case 'TOGGLE_PINNED': {
      const path = action.payload;
      const next = state.pinned.includes(path)
        ? state.pinned.filter(p => p !== path)
        : [...state.pinned, path];
      try { localStorage.setItem(STORAGE_KEYS.pinned, JSON.stringify(next)); } catch {}
      return { ...state, pinned: next };
    }
    case 'TOGGLE_BOOKMARK': {
      const path = action.payload;
      const next = state.bookmarks.includes(path)
        ? state.bookmarks.filter(p => p !== path)
        : [...state.bookmarks, path];
      return { ...state, bookmarks: next };
    }
    case 'TRACK_VISIT': {
      const path = action.payload;
      const now = Date.now();
      const recent = [path, ...state.recent.filter(p => p !== path)].slice(0, 30);
      try { localStorage.setItem(STORAGE_KEYS.recent, JSON.stringify(recent)); } catch {}
      const entry = state.usage[path] || { path, count: 0, lastUsed: 0 };
      const usage = { ...state.usage, [path]: { path, count: entry.count + 1, lastUsed: now } };
      try { localStorage.setItem(STORAGE_KEYS.usage, JSON.stringify(usage)); } catch {}
      return { ...state, recent, usage };
    }
    case 'SET_COLLAPSED': {
      try { localStorage.setItem(STORAGE_KEYS.collapsed, JSON.stringify(action.payload)); } catch {}
      return { ...state, isCollapsed: action.payload };
    }
    case 'SET_SEARCH':
      return { ...state, searchQuery: action.payload };
    case 'TOGGLE_GROUP':
      return {
        ...state,
        expandedGroups: { ...state.expandedGroups, [action.payload]: !state.expandedGroups[action.payload] },
      };
    case 'SET_CUSTOM_ORDER':
      return { ...state, customOrder: action.payload };
    case 'LOAD_PERSISTED':
      return { ...state, ...action.payload };
    default:
      return state;
  }
}
interface NavigationContextType {
  state: NavigationState;
  dispatch: React.Dispatch<NavigationAction>;
  isFavorite: (path: string) => boolean;
  isPinned: (path: string) => boolean;
  isBookmarked: (path: string) => boolean;
  getAdaptiveOrder: (items: { to: string }[]) => { to: string }[];
}
const NavigationContext = createContext<NavigationContextType | null>(null);
export function NavigationProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(navigationReducer, undefined, getInitialState);
  const isFavorite = useCallback((path: string) => state.favorites.includes(path), [state.favorites]);
  const isPinned = useCallback((path: string) => state.pinned.includes(path), [state.pinned]);
  const isBookmarked = useCallback((path: string) => state.bookmarks.includes(path), [state.bookmarks]);
  const getAdaptiveOrder = useCallback((items: { to: string }[]) => {
    return [...items].sort((a, b) => {
      const aScore = (state.pinned.includes(a.to) ? 1000000000 : 0)
        + (state.favorites.includes(a.to) ? 1000000 : 0)
        + (state.customOrder[a.to] ?? 0) * 1000
        + (state.usage[a.to]?.count || 0);
      const bScore = (state.pinned.includes(b.to) ? 1000000000 : 0)
        + (state.favorites.includes(b.to) ? 1000000 : 0)
        + (state.customOrder[b.to] ?? 0) * 1000
        + (state.usage[b.to]?.count || 0);
      return bScore - aScore;
    });
  }, [state.pinned, state.favorites, state.usage, state.customOrder]);
  return (
    <NavigationContext.Provider value={{ state, dispatch, isFavorite, isPinned, isBookmarked, getAdaptiveOrder }}>
      {children}
    </NavigationContext.Provider>
  );
}
export function useNavigationStore() {
  const ctx = useContext(NavigationContext);
  if (!ctx) throw new Error('useNavigationStore must be used within NavigationProvider');
  return ctx;
}