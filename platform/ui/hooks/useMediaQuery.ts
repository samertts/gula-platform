import { useState, useEffect } from 'react';
import { breakpoints, type BreakpointKey } from '../design-system/tokens/breakpoints';

export interface MediaQueryResult {
  matches: boolean;
  breakpoint: BreakpointKey | null;
  isXs: boolean;
  isSm: boolean;
  isMd: boolean;
  isLg: boolean;
  isXl: boolean;
  is2xl: boolean;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
}

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches;
    }
    return false;
  });

  useEffect(() => {
    const mql = window.matchMedia(query);
    const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, [query]);

  return matches;
}

export function useBreakpoint(): MediaQueryResult {
  const isXs = useMediaQuery(`(max-width: ${breakpoints.sm - 1}px)`);
  const isSm = useMediaQuery(`(min-width: ${breakpoints.sm}px) and (max-width: ${breakpoints.md - 1}px)`);
  const isMd = useMediaQuery(`(min-width: ${breakpoints.md}px) and (max-width: ${breakpoints.lg - 1}px)`);
  const isLg = useMediaQuery(`(min-width: ${breakpoints.lg}px) and (max-width: ${breakpoints.xl - 1}px)`);
  const isXl = useMediaQuery(`(min-width: ${breakpoints.xl}px) and (max-width: ${breakpoints['2xl'] - 1}px)`);
  const is2xl = useMediaQuery(`(min-width: ${breakpoints['2xl']}px)`);

  const isMobile = isXs || isSm;
  const isTablet = isMd;
  const isDesktop = isLg || isXl || is2xl;

  let breakpoint: BreakpointKey | null = 'xs';
  if (isSm) breakpoint = 'sm';
  else if (isMd) breakpoint = 'md';
  else if (isLg) breakpoint = 'lg';
  else if (isXl) breakpoint = 'xl';
  else if (is2xl) breakpoint = '2xl';

  return {
    matches: isXs || isSm || isMd || isLg || isXl || is2xl,
    breakpoint,
    isXs,
    isSm,
    isMd,
    isLg,
    isXl,
    is2xl,
    isMobile,
    isTablet,
    isDesktop,
  };
}
