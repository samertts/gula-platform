import React, { createContext, useContext, useEffect, useState } from 'react';
import { cn } from '../utils';
import { Sun, Moon, Monitor } from 'lucide-react';

export type ThemeMode = 'light' | 'dark' | 'system';

interface ThemeContextValue {
  mode: ThemeMode;
  resolved: 'light' | 'dark';
  setMode: (mode: ThemeMode) => void;
  toggle: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  mode: 'system',
  resolved: 'light',
  setMode: () => {},
  toggle: () => {},
});

export const useTheme = () => useContext(ThemeContext);

export const ThemeProvider: React.FC<{ children: React.ReactNode; defaultMode?: ThemeMode; storageKey?: string }> = ({
  children,
  defaultMode = 'system',
  storageKey = 'gula-theme',
}) => {
  const [mode, setModeState] = useState<ThemeMode>(() => {
    if (typeof window === 'undefined') return defaultMode;
    return (localStorage.getItem(storageKey) as ThemeMode) || defaultMode;
  });
  const [systemDark, setSystemDark] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    setSystemDark(mq.matches);
    const handler = (e: MediaQueryListEvent) => setSystemDark(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  const resolved = mode === 'system' ? (systemDark ? 'dark' : 'light') : mode;

  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle('dark', resolved === 'dark');
    localStorage.setItem(storageKey, mode);
  }, [resolved, mode, storageKey]);

  const setMode = (m: ThemeMode) => setModeState(m);
  const toggle = () => setMode(resolved === 'dark' ? 'light' : 'dark');

  return (
    <ThemeContext.Provider value={{ mode, resolved, setMode, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const ThemeToggle: React.FC<{ className?: string }> = ({ className }) => {
  const { mode, setMode } = useTheme();
  const icons = { light: Sun, dark: Moon, system: Monitor };
  const Icon = icons[mode];
  const next = { light: 'dark' as const, dark: 'system' as const, system: 'light' as const };

  return (
    <button
      onClick={() => setMode(next[mode])}
      className={cn(
        'p-2 rounded-lg text-neutral-500 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white',
        'hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors',
        className
      )}
      aria-label={`Theme: ${mode}`}
    >
      <Icon size={18} />
    </button>
  );
};
