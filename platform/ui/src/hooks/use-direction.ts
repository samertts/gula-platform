'use client';

import { useCallback, useSyncExternalStore } from 'react';

function getDirection(): 'rtl' | 'ltr' {
  if (typeof document === 'undefined') return 'rtl';
  const dir = document.documentElement.getAttribute('dir');
  return dir === 'ltr' ? 'ltr' : 'rtl';
}

function subscribe(callback: () => void) {
  const observer = new MutationObserver(() => callback());
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['dir'],
  });
  return () => observer.disconnect();
}

export function useDirection() {
  const dir = useSyncExternalStore(subscribe, getDirection, () => 'rtl');
  return dir;
}
