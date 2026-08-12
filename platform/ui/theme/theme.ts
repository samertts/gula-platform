import { colors, semanticColors, getColor, getSemantic, type ThemeMode } from '../design-system/tokens/colors';
import { fontFamilies, typeScale, getFontFamily } from '../design-system/tokens/typography';
import { spacing, borderRadius, shadows } from '../design-system/tokens/spacing';
import { breakpoints } from '../design-system/tokens/breakpoints';

export interface GulaTheme {
  mode: ThemeMode;
  isRtl: boolean;
  colors: typeof colors;
  semantic: {
    background: string;
    surface: string;
    surfaceSecondary: string;
    text: string;
    textSecondary: string;
    border: string;
    borderLight: string;
  };
  typography: {
    fontFamilies: typeof fontFamilies;
    typeScale: typeof typeScale;
    getFontFamily: typeof getFontFamily;
  };
  spacing: typeof spacing;
  borderRadius: typeof borderRadius;
  shadows: typeof shadows;
  breakpoints: typeof breakpoints;
  getColor: typeof getColor;
  getSemantic: typeof getSemantic;
}

export function createTheme(mode: ThemeMode = 'light', isRtl = false): GulaTheme {
  return {
    mode,
    isRtl,
    colors,
    semantic: semanticColors[mode],
    typography: {
      fontFamilies,
      typeScale,
      getFontFamily,
    },
    spacing,
    borderRadius,
    shadows,
    breakpoints,
    getColor,
    getSemantic,
  };
}

export function applyThemeToDocument(mode: ThemeMode, isRtl: boolean): void {
  const root = document.documentElement;
  root.setAttribute('data-theme', mode);
  root.setAttribute('dir', isRtl ? 'rtl' : 'ltr');
  root.style.colorScheme = mode;

  const semantic = semanticColors[mode];
  root.style.setProperty('--gula-bg', semantic.background);
  root.style.setProperty('--gula-surface', semantic.surface);
  root.style.setProperty('--gula-surface-secondary', semantic.surfaceSecondary);
  root.style.setProperty('--gula-text', semantic.text);
  root.style.setProperty('--gula-text-secondary', semantic.textSecondary);
  root.style.setProperty('--gula-border', semantic.border);
  root.style.setProperty('--gula-border-light', semantic.borderLight);
}
