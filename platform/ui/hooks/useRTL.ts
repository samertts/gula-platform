import { useState, useEffect, useCallback } from 'react';

export interface RTLResult {
  isRtl: boolean;
  dir: 'rtl' | 'ltr';
  toggleDirection: () => void;
  setDirection: (rtl: boolean) => void;
}

export function useRTL(initialRtl = false): RTLResult {
  const [isRtl, setIsRtl] = useState(() => {
    if (typeof document !== 'undefined') {
      const saved = localStorage.getItem('gula-direction');
      if (saved === 'rtl') return true;
      if (saved === 'ltr') return false;
      return document.documentElement.dir === 'rtl';
    }
    return initialRtl;
  });

  useEffect(() => {
    document.documentElement.dir = isRtl ? 'rtl' : 'ltr';
    document.documentElement.lang = isRtl ? 'ar' : 'en';
    localStorage.setItem('gula-direction', isRtl ? 'rtl' : 'ltr');
  }, [isRtl]);

  const toggleDirection = useCallback(() => {
    setIsRtl(prev => !prev);
  }, []);

  const setDirection = useCallback((rtl: boolean) => {
    setIsRtl(rtl);
  }, []);

  return {
    isRtl,
    dir: isRtl ? 'rtl' : 'ltr',
    toggleDirection,
    setDirection,
  };
}

export function getDir(isRtl: boolean): 'rtl' | 'ltr' {
  return isRtl ? 'rtl' : 'ltr';
}

export function isArabicLang(lang: string): boolean {
  return ['ar', 'AR', 'ku', 'KU'].some(l => l === lang);
}
