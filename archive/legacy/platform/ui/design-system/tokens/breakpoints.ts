export const breakpoints = {
  xs: 0,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
} as const;

export type BreakpointKey = keyof typeof breakpoints;

export type BreakpointDirection = 'up' | 'down';

export function getBreakpointValue(key: BreakpointKey): number {
  return breakpoints[key];
}

export function getMediaQuery(key: BreakpointKey, direction: BreakpointDirection = 'up'): string {
  const value = breakpoints[key];
  if (direction === 'up') {
    return `(min-width: ${value}px)`;
  }
  if (key === 'xs') return '(max-width: 0px)';
  const prevKey = Object.keys(breakpoints)[Object.keys(breakpoints).indexOf(key) - 1] as BreakpointKey | undefined;
  const prevValue = prevKey ? breakpoints[prevKey] : 0;
  return `(max-width: ${prevValue}px)`;
}

export const containerMaxWidths: Record<BreakpointKey, string> = {
  xs: '100%',
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
};
