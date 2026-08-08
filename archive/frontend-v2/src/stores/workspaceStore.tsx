import {createContext, useContext, useReducer, ReactNode} from 'react';
interface Tab {
  id: string;
  path: string;
  label: string;
  icon?: string;
}
interface SplitPane {
  id: string;
  direction: 'horizontal' | 'vertical';
  primary: string;
  secondary: string | null;
  ratio: number;
}
interface Widget {
  id: string;
  type: string;
  position: { x: number; y: number };
  size: { w: number; h: number };
  config?: Record<string, unknown>;
}
interface DashboardPreset {
  id: string;
  name: string;
  widgets: Widget[];
}
interface WorkspaceState {
  activeTab: string;
  tabs: Tab[];
  splitPanes: SplitPane[];
  floatingWidgets: Widget[];
  dashboards: DashboardPreset[];
  activeDashboard: string | null;
  detachedPanels: string[];
  pinnedInspectors: string[];
}
type WorkspaceAction =
  | { type: 'OPEN_TAB'; payload: Tab }
  | { type: 'CLOSE_TAB'; payload: string }
  | { type: 'SET_ACTIVE_TAB'; payload: string }
  | { type: 'REORDER_TABS'; payload: Tab[] }
  | { type: 'SPLIT_PANE'; payload: SplitPane }
  | { type: 'CLOSE_SPLIT'; payload: string }
  | { type: 'RESIZE_SPLIT'; payload: { id: string; ratio: number } }
  | { type: 'ADD_WIDGET'; payload: Widget }
  | { type: 'REMOVE_WIDGET'; payload: string }
  | { type: 'MOVE_WIDGET'; payload: { id: string; position: { x: number; y: number } } }
  | { type: 'RESIZE_WIDGET'; payload: { id: string; size: { w: number; h: number } } }
  | { type: 'SAVE_DASHBOARD'; payload: DashboardPreset }
  | { type: 'LOAD_DASHBOARD'; payload: string }
  | { type: 'DELETE_DASHBOARD'; payload: string }
  | { type: 'DETACH_PANEL'; payload: string }
  | { type: 'ATTACH_PANEL'; payload: string }
  | { type: 'PIN_INSPECTOR'; payload: string }
  | { type: 'UNPIN_INSPECTOR'; payload: string };
function workspaceReducer(state: WorkspaceState, action: WorkspaceAction): WorkspaceState {
  switch (action.type) {
    case 'OPEN_TAB': {
      const exists = state.tabs.find(t => t.id === action.payload.id);
      if (exists) return { ...state, activeTab: action.payload.id };
      return {
        ...state,
        tabs: [...state.tabs, action.payload],
        activeTab: action.payload.id,
      };
    }
    case 'CLOSE_TAB': {
      const tabs = state.tabs.filter(t => t.id !== action.payload);
      const activeTab = state.activeTab === action.payload
        ? (tabs[tabs.length - 1]?.id || '')
        : state.activeTab;
      return { ...state, tabs, activeTab };
    }
    case 'SET_ACTIVE_TAB':
      return { ...state, activeTab: action.payload };
    case 'REORDER_TABS':
      return { ...state, tabs: action.payload };
    case 'SPLIT_PANE':
      return { ...state, splitPanes: [...state.splitPanes, action.payload] };
    case 'CLOSE_SPLIT':
      return { ...state, splitPanes: state.splitPanes.filter(s => s.id !== action.payload) };
    case 'RESIZE_SPLIT':
      return {
        ...state,
        splitPanes: state.splitPanes.map(s =>
          s.id === action.payload.id ? { ...s, ratio: action.payload.ratio } : s
        ),
      };
    case 'ADD_WIDGET':
      return { ...state, floatingWidgets: [...state.floatingWidgets, action.payload] };
    case 'REMOVE_WIDGET':
      return { ...state, floatingWidgets: state.floatingWidgets.filter(w => w.id !== action.payload) };
    case 'MOVE_WIDGET':
      return {
        ...state,
        floatingWidgets: state.floatingWidgets.map(w =>
          w.id === action.payload.id ? { ...w, position: action.payload.position } : w
        ),
      };
    case 'RESIZE_WIDGET':
      return {
        ...state,
        floatingWidgets: state.floatingWidgets.map(w =>
          w.id === action.payload.id ? { ...w, size: action.payload.size } : w
        ),
      };
    case 'SAVE_DASHBOARD': {
      const existing = state.dashboards.findIndex(d => d.id === action.payload.id);
      if (existing >= 0) {
        const dashboards = [...state.dashboards];
        dashboards[existing] = action.payload;
        return { ...state, dashboards };
      }
      return { ...state, dashboards: [...state.dashboards, action.payload] };
    }
    case 'LOAD_DASHBOARD':
      return { ...state, activeDashboard: action.payload };
    case 'DELETE_DASHBOARD':
      return {
        ...state,
        dashboards: state.dashboards.filter(d => d.id !== action.payload),
        activeDashboard: state.activeDashboard === action.payload ? null : state.activeDashboard,
      };
    case 'DETACH_PANEL':
      return {
        ...state,
        detachedPanels: state.detachedPanels.includes(action.payload)
          ? state.detachedPanels : [...state.detachedPanels, action.payload],
      };
    case 'ATTACH_PANEL':
      return {
        ...state,
        detachedPanels: state.detachedPanels.filter(p => p !== action.payload),
      };
    case 'PIN_INSPECTOR':
      return { ...state, pinnedInspectors: [...state.pinnedInspectors, action.payload] };
    case 'UNPIN_INSPECTOR':
      return { ...state, pinnedInspectors: state.pinnedInspectors.filter(p => p !== action.payload) };
    default:
      return state;
  }
}
const initialState: WorkspaceState = {
  activeTab: '',
  tabs: [],
  splitPanes: [],
  floatingWidgets: [],
  dashboards: [],
  activeDashboard: null,
  detachedPanels: [],
  pinnedInspectors: [],
};
interface WorkspaceContextType {
  state: WorkspaceState;
  dispatch: React.Dispatch<WorkspaceAction>;
}
const WorkspaceContext = createContext<WorkspaceContextType | null>(null);
export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(workspaceReducer, initialState);
  return (
    <WorkspaceContext.Provider value={{ state, dispatch }}>
      {children}
    </WorkspaceContext.Provider>
  );
}
export function useWorkspaceStore() {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) throw new Error('useWorkspaceStore must be used within WorkspaceProvider');
  return ctx;
}