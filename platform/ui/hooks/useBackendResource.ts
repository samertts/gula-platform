import { useCallback, useEffect, useRef, useState } from 'react';

export interface BackendResourceState<T> {
  data: T | null;
  error: Error | null;
  isLoading: boolean;
  isRefreshing: boolean;
  refetch: () => Promise<T | null>;
}

/**
 * Small dependency-free async state primitive for API-backed screens.
 * It never replaces existing data with an error state, which avoids blanking
 * clinical dashboards during a background refresh or temporary outage.
 */
export function useBackendResource<T>(
  loader: () => Promise<T>,
  enabled = true,
): BackendResourceState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState(enabled);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const refetch = useCallback(async (): Promise<T | null> => {
    if (!enabled) return null;
    setIsLoading(true);
    setError(null);
    try {
      const next = await loader();
      if (mounted.current) setData(next);
      return next;
    } catch (cause) {
      const nextError = cause instanceof Error ? cause : new Error('تعذر تحميل البيانات من الخادم');
      if (mounted.current) setError(nextError);
      return null;
    } finally {
      if (mounted.current) setIsLoading(false);
    }
  }, [enabled, loader]);

  useEffect(() => {
    if (!enabled) {
      setIsLoading(false);
      setError(null);
      return;
    }
    void refetch();
  }, [enabled, refetch]);

  return {
    data,
    error,
    isLoading,
    isRefreshing: isLoading && data !== null,
    refetch,
  };
}
