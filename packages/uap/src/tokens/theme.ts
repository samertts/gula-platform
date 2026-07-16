import type { ColorPalette } from './colors';
import { colors } from './colors';
import { typography } from './typography';
import { spacing, borderRadius, shadows, breakpoints, zIndex, animation } from './spacing';

export interface Theme {
  name: string;
  colors: ColorPalette;
  typography: typeof typography;
  spacing: typeof spacing;
  borderRadius: typeof borderRadius;
  shadows: typeof shadows;
  breakpoints: typeof breakpoints;
  zIndex: typeof zIndex;
  animation: typeof animation;
  direction: 'ltr' | 'rtl';
  mode: 'light' | 'dark';
  contrast: 'normal' | 'high';
}

export const createTheme = (
  overrides?: Partial<Theme>
): Theme => ({
  name: 'gula-default',
  colors,
  typography,
  spacing,
  borderRadius,
  shadows,
  breakpoints,
  zIndex,
  animation,
  direction: 'ltr',
  mode: 'light',
  contrast: 'normal',
  ...overrides,
});

export const lightTheme: Theme = createTheme({
  name: 'gula-light',
  mode: 'light',
  direction: 'ltr',
});

export const darkTheme: Theme = createTheme({
  name: 'gula-dark',
  mode: 'dark',
  direction: 'ltr',
});

export const rtlTheme: Theme = createTheme({
  name: 'gula-rtl',
  direction: 'rtl',
});

export const highContrastTheme: Theme = createTheme({
  name: 'gula-high-contrast',
  contrast: 'high',
});

export const governmentTheme: Theme = createTheme({
  name: 'gula-government',
  direction: 'rtl',
  mode: 'light',
});

export const hospitalTheme: Theme = createTheme({
  name: 'gula-hospital',
  direction: 'rtl',
  mode: 'light',
});

export const laboratoryTheme: Theme = createTheme({
  name: 'gula-laboratory',
  direction: 'rtl',
  mode: 'light',
});

export type ThemeMode = 'light' | 'dark';
export type ThemeContrast = 'normal' | 'high';
export type ThemeDirection = 'ltr' | 'rtl';
