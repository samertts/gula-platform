import { createContext, useState, useCallback, useEffect, type ReactNode, type CSSProperties } from 'react';
import { createTheme, applyThemeToDocument, type GulaTheme } from './theme';
import type { ThemeMode } from '../design-system/tokens/colors';

export interface ThemeContextValue {
  theme: GulaTheme;
  mode: ThemeMode;
  isRtl: boolean;
  toggleMode: () => void;
  setMode: (mode: ThemeMode) => void;
  setRtl: (rtl: boolean) => void;
}

export const ThemeContext = createContext<ThemeContextValue | null>(null);

export interface ThemeProviderProps {
  children: ReactNode;
  defaultMode?: ThemeMode;
  defaultTheme?: ThemeMode;
  defaultRtl?: boolean;
  defaultDirection?: 'rtl' | 'ltr';
  defaultLocale?: string;
  /** CSS variable injection strategy */
  strategy?: 'css-vars' | 'class' | 'both';
}

export function ThemeProvider({
  children,
  defaultMode = 'light',
  defaultTheme,
  defaultRtl = false,
  defaultDirection,
  defaultLocale,
  strategy = 'css-vars',
}: ThemeProviderProps) {
  const initialMode = defaultTheme ?? defaultMode;
  const [mode, setModeState] = useState<ThemeMode>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('gula-theme-mode') as ThemeMode | null;
      if (saved === 'light' || saved === 'dark') return saved;
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark';
    }
    return initialMode;
  });

  const initialRtl = defaultDirection ? defaultDirection === 'rtl' : defaultRtl;
  const [isRtl, setRtlState] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('gula-direction') as 'rtl' | 'ltr' | null;
      if (saved) return saved === 'rtl';
    }
    return initialRtl;
  });

  const [theme, setTheme] = useState(() => createTheme(mode, isRtl));

  useEffect(() => {
    const t = createTheme(mode, isRtl);
    setTheme(t);
    localStorage.setItem('gula-theme-mode', mode);
    localStorage.setItem('gula-direction', isRtl ? 'rtl' : 'ltr');

    applyThemeToDocument(mode, isRtl);
    if (defaultLocale) document.documentElement.lang = defaultLocale;

    if (strategy === 'class' || strategy === 'both') {
      const root = document.documentElement;
      root.classList.remove('theme-light', 'theme-dark');
      root.classList.add(`theme-${mode}`);
      root.classList.toggle('rtl', isRtl);
      root.classList.toggle('ltr', !isRtl);
    }
  }, [mode, isRtl, strategy, defaultLocale]);

  const toggleMode = useCallback(() => {
    setModeState((prev: ThemeMode) => prev === 'light' ? 'dark' : 'light');
  }, []);

  const setMode = useCallback((newMode: ThemeMode) => {
    setModeState(newMode);
  }, []);

  const setRtl = useCallback((rtl: boolean) => {
    setRtlState(rtl);
  }, []);

  const cssVars = {
    '--gula-bg': theme.semantic.background,
    '--gula-surface': theme.semantic.surface,
    '--gula-surface-secondary': theme.semantic.surfaceSecondary,
    '--gula-text': theme.semantic.text,
    '--gula-text-secondary': theme.semantic.textSecondary,
    '--gula-border': theme.semantic.border,
    '--gula-border-light': theme.semantic.borderLight,
    '--gula-primary': theme.colors.primary[500],
    '--gula-primary-hover': theme.colors.primary[600],
    '--gula-success': theme.colors.success[500],
    '--gula-warning': theme.colors.warning[500],
    '--gula-danger': theme.colors.danger[500],
    '--gula-info': theme.colors.info[500],
  } as unknown as CSSProperties;

  return (
    <ThemeContext.Provider value={{ theme, mode, isRtl, toggleMode, setMode, setRtl }}>
      <div
        style={cssVars}
        className={`gula-theme-root ${mode === 'dark' ? 'dark' : ''}`}
        data-theme={mode}
        dir={isRtl ? 'rtl' : 'ltr'}
      >
        {children}
      </div>
    </ThemeContext.Provider>
  );
}
