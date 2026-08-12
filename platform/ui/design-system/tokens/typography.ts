export const fontFamilies = {
  english: {
    sans: "'Inter', ui-sans-serif, system-ui, sans-serif",
    display: "'Outfit', 'Inter', ui-sans-serif, system-ui, sans-serif",
    mono: "'JetBrains Mono', ui-monospace, SFMono-Regular, monospace",
  },
  arabic: {
    sans: "'Tajawal', 'Cairo', ui-sans-serif, system-ui, sans-serif",
    display: "'Noto Naskh Arabic', 'Tajawal', ui-sans-serif, system-ui, sans-serif",
    mono: "'JetBrains Mono', ui-monospace, SFMono-Regular, monospace",
  },
} as const;

export type FontCategory = keyof typeof fontFamilies.english;

export function getFontFamily(category: FontCategory, isArabic: boolean): string {
  const lang = isArabic ? 'arabic' : 'english';
  return fontFamilies[lang][category];
}

export const typeScale = {
  display: {
    xs: { fontSize: '1.875rem', lineHeight: '2.25rem', fontWeight: 800 },
    sm: { fontSize: '2.25rem', lineHeight: '2.5rem', fontWeight: 800 },
    md: { fontSize: '3rem', lineHeight: '1', fontWeight: 800 },
    lg: { fontSize: '3.75rem', lineHeight: '1', fontWeight: 900 },
    xl: { fontSize: '4.5rem', lineHeight: '1', fontWeight: 900 },
  },
  heading: {
    xs: { fontSize: '1.25rem', lineHeight: '1.75rem', fontWeight: 700 },
    sm: { fontSize: '1.5rem', lineHeight: '2rem', fontWeight: 700 },
    md: { fontSize: '1.875rem', lineHeight: '2.25rem', fontWeight: 700 },
    lg: { fontSize: '2.25rem', lineHeight: '2.5rem', fontWeight: 700 },
  },
  body: {
    xs: { fontSize: '0.75rem', lineHeight: '1rem', fontWeight: 400 },
    sm: { fontSize: '0.875rem', lineHeight: '1.25rem', fontWeight: 400 },
    md: { fontSize: '1rem', lineHeight: '1.5rem', fontWeight: 400 },
    lg: { fontSize: '1.125rem', lineHeight: '1.75rem', fontWeight: 400 },
  },
  label: {
    xs: { fontSize: '0.625rem', lineHeight: '0.875rem', fontWeight: 700, letterSpacing: '0.05em' },
    sm: { fontSize: '0.75rem', lineHeight: '1rem', fontWeight: 700, letterSpacing: '0.025em' },
    md: { fontSize: '0.875rem', lineHeight: '1.25rem', fontWeight: 600 },
  },
} as const;

export type TypeScaleCategory = keyof typeof typeScale;
export type TypeScaleSize = keyof typeof typeScale.display;

export function getTypeScale(category: TypeScaleCategory, size: TypeScaleSize) {
  const cat = typeScale[category];
  if (cat && size in cat) {
    return cat[size as keyof typeof cat];
  }
  return typeScale.body.md;
}
