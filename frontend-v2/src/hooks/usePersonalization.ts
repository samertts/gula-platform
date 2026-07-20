import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY_FAVORITES = 'gula_nav_favorites';
const STORAGE_KEY_RECENT = 'gula_nav_recent';
const STORAGE_KEY_USAGE = 'gula_nav_usage';
const STORAGE_KEY_PINNED = 'gula_nav_pinned';

interface UsageEntry {
  path: string;
  count: number;
  lastUsed: number;
}

export function usePersonalization() {
  const [favorites, setFavorites] = useState<string[]>([]);
  const [recent, setRecent] = useState<string[]>([]);
  const [usage, setUsage] = useState<Record<string, UsageEntry>>({});
  const [pinned, setPinned] = useState<string[]>([]);

  useEffect(() => {
    try {
      const f = localStorage.getItem(STORAGE_KEY_FAVORITES);
      if (f) setFavorites(JSON.parse(f));
      const r = localStorage.getItem(STORAGE_KEY_RECENT);
      if (r) setRecent(JSON.parse(r));
      const u = localStorage.getItem(STORAGE_KEY_USAGE);
      if (u) setUsage(JSON.parse(u));
      const p = localStorage.getItem(STORAGE_KEY_PINNED);
      if (p) setPinned(JSON.parse(p));
    } catch { /* ignore */ }
  }, []);

  const persist = useCallback((key: string, data: unknown) => {
    try { localStorage.setItem(key, JSON.stringify(data)); } catch { /* ignore */ }
  }, []);

  const trackVisit = useCallback((path: string) => {
    const now = Date.now();
    setRecent(prev => {
      const next = [path, ...prev.filter(p => p !== path)].slice(0, 20);
      persist(STORAGE_KEY_RECENT, next);
      return next;
    });
    setUsage(prev => {
      const entry = prev[path] || { path, count: 0, lastUsed: 0 };
      const next = { ...prev, [path]: { path, count: entry.count + 1, lastUsed: now } };
      persist(STORAGE_KEY_USAGE, next);
      return next;
    });
  }, [persist]);

  const toggleFavorite = useCallback((path: string) => {
    setFavorites(prev => {
      const next = prev.includes(path) ? prev.filter(p => p !== path) : [...prev, path];
      persist(STORAGE_KEY_FAVORITES, next);
      return next;
    });
  }, [persist]);

  const togglePinned = useCallback((path: string) => {
    setPinned(prev => {
      const next = prev.includes(path) ? prev.filter(p => p !== path) : [...prev, path];
      persist(STORAGE_KEY_PINNED, next);
      return next;
    });
  }, [persist]);

  const isFavorite = useCallback((path: string) => favorites.includes(path), [favorites]);
  const isPinned = useCallback((path: string) => pinned.includes(path), [pinned]);

  const getAdaptiveOrder = useCallback((items: { to: string; label: string }[]) => {
    return [...items].sort((a, b) => {
      const aScore = (pinned.includes(a.to) ? 1e9 : 0) + (favorites.includes(a.to) ? 1e6 : 0) + (usage[a.to]?.count || 0);
      const bScore = (pinned.includes(b.to) ? 1e9 : 0) + (favorites.includes(b.to) ? 1e6 : 0) + (usage[b.to]?.count || 0);
      return bScore - aScore;
    });
  }, [favorites, pinned, usage]);

  return {
    favorites, recent, usage, pinned,
    trackVisit, toggleFavorite, togglePinned,
    isFavorite, isPinned, getAdaptiveOrder,
  };
}
