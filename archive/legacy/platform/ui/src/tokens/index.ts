export const designTokens = {
  colors: {
    primary: {
      50: '#eff6ff', 100: '#dbeafe', 200: '#bfdbfe',
      300: '#93c5fd', 400: '#60a5fa', 500: '#3b82f6',
      600: '#2563eb', 700: '#1d4ed8', 800: '#1e40af',
      900: '#1e3a8a', 950: '#172554',
    },
    clinical: {
      green: { 50: '#f0fdf4', 500: '#22c55e', 700: '#15803d' },
      yellow: { 50: '#fefce8', 500: '#eab308', 700: '#a16207' },
      red: { 50: '#fef2f2', 500: '#ef4444', 700: '#b91c1c' },
      blue: { 50: '#eff6ff', 500: '#3b82f6', 700: '#1d4ed8' },
    },
    status: {
      normal: '#22c55e',
      borderline: '#eab308',
      abnormal: '#ef4444',
      critical: '#e11d48',
      pending: '#6b7280',
      cancelled: '#9ca3af',
    },
    surface: {
      50: '#f8fafc', 100: '#f1f5f9', 200: '#e2e8f0',
      300: '#cbd5e1', 400: '#94a3b8', 500: '#64748b',
      600: '#475569', 700: '#334155', 800: '#1e293b',
      900: '#0f172a', 950: '#020617',
    },
    dark: {
      surface: {
        50: '#0f172a', 100: '#1e293b', 200: '#334155',
        300: '#475569', 400: '#64748b', 500: '#94a3b8',
        600: '#cbd5e1', 700: '#e2e8f0', 800: '#f1f5f9',
        900: '#f8fafc',
      },
    },
  },
  typography: {
    fonts: {
      sans: "'Inter', system-ui, -apple-system, sans-serif",
      arabic: "'Noto Kufi Arabic', 'Tajawal', 'Cairo', sans-serif",
      mono: "'JetBrains Mono', 'Fira Code', monospace",
    },
    sizes: {
      xs: '0.75rem', sm: '0.875rem', base: '1rem',
      lg: '1.125rem', xl: '1.25rem', '2xl': '1.5rem',
      '3xl': '1.875rem', '4xl': '2.25rem', '5xl': '3rem',
      '6xl': '3.75rem',
    },
    weights: {
      light: 300, normal: 400, medium: 500,
      semibold: 600, bold: 700,
    },
  },
  spacing: {
    0: '0px', 1: '0.25rem', 2: '0.5rem', 3: '0.75rem',
    4: '1rem', 5: '1.25rem', 6: '1.5rem', 7: '1.75rem',
    8: '2rem', 9: '2.25rem', 10: '2.5rem', 11: '2.75rem',
    12: '3rem', 14: '3.5rem', 16: '4rem', 20: '5rem',
    24: '6rem', 28: '7rem', 32: '8rem', 36: '9rem',
    40: '10rem', 44: '11rem', 48: '12rem', 52: '13rem',
    56: '14rem', 60: '15rem', 64: '16rem', 72: '18rem',
    80: '20rem', 96: '24rem',
  },
  radius: {
    none: '0', sm: '0.125rem', base: '0.25rem',
    md: '0.375rem', lg: '0.5rem', xl: '0.75rem',
    '2xl': '1rem', '3xl': '1.5rem', full: '9999px',
  },
} as const;

export type DesignTokens = typeof designTokens;
