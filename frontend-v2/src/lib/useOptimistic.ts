/**
 * `useOptimisticAction` — a tiny optimistic-update helper that:
 *   1. applies an immediate UI change,
 *   2. runs an async commit,
 *   3. rolls back to the original value on failure,
 *   4. exposes a `retry` callback so the caller can offer "Try again".
 *
 * Designed for *safe* surfaces only — UI mutations whose rollback is just
 * setting state back. Do NOT wrap calls that the server may have committed
 * partially (e.g. multi-step transactions, billing, signed audit log writes).
 */
import { useCallback, useRef, useState } from 'react';

export interface OptimisticState<T> {
  value: T;
  pending: boolean;
  error: Error | null;
  /** Apply an optimistic change and commit it asynchronously. */
  apply: (
    optimistic: T | ((prev: T) => T),
    commit: () => Promise<unknown>,
  ) => Promise<boolean>;
  /** Re-run the most recent failed commit with the same optimistic value. */
  retry: () => Promise<boolean>;
  /** Replace the value without going through commit (e.g. server push). */
  set: (next: T | ((prev: T) => T)) => void;
}

/**
 * @param initial Initial state value.
 * @param onError Optional side-effect on commit failure. Receives the error
 *                and a `retry` thunk that re-runs the same commit. Useful
 *                for showing a toast with a Retry button.
 */
export function useOptimisticAction<T>(
  initial: T,
  onError?: (error: Error, retry: () => Promise<boolean>) => void,
): OptimisticState<T> {
  const [value, setValue] = useState<T>(initial);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Track the previous (committed) value so we can roll back on failure, and
  // remember the most recent attempt so `retry` works.
  const lastAttempt = useRef<{
    optimistic: T | ((prev: T) => T);
    commit: () => Promise<unknown>;
    rollbackTo: T;
  } | null>(null);

  const runAttempt = useCallback(
    async (
      optimistic: T | ((prev: T) => T),
      commit: () => Promise<unknown>,
      rollbackTo: T,
    ): Promise<boolean> => {
      setPending(true);
      setError(null);
      // Apply optimistic value immediately.
      setValue((prev) =>
        typeof optimistic === 'function'
          ? (optimistic as (p: T) => T)(prev)
          : optimistic,
      );
      lastAttempt.current = { optimistic, commit, rollbackTo };
      try {
        await commit();
        setPending(false);
        // Clear last attempt on success so retry() is a no-op.
        lastAttempt.current = null;
        return true;
      } catch (err) {
        const e = err instanceof Error ? err : new Error(String(err));
        setError(e);
        setPending(false);
        // Roll back.
        setValue(rollbackTo);
        if (onError) {
          onError(e, () => runAttempt(optimistic, commit, rollbackTo));
        }
        return false;
      }
    },
    [onError],
  );

  const apply = useCallback<OptimisticState<T>['apply']>(
    (optimistic, commit) => {
      // Capture the *current* value as rollback point at call time.
      // We use the functional setter trick to read latest state without races.
      let rollbackTo: T = value;
      setValue((cur) => {
        rollbackTo = cur;
        return cur;
      });
      return runAttempt(optimistic, commit, rollbackTo);
    },
    [value, runAttempt],
  );

  const retry = useCallback(async () => {
    const last = lastAttempt.current;
    if (!last) return false;
    return runAttempt(last.optimistic, last.commit, last.rollbackTo);
  }, [runAttempt]);

  const set = useCallback<OptimisticState<T>['set']>((next) => {
    setValue((prev) =>
      typeof next === 'function' ? (next as (p: T) => T)(prev) : next,
    );
  }, []);

  return { value, pending, error, apply, retry, set };
}
