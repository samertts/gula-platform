/**
 * Lightweight keyboard-shortcut primitives.
 *
 * Two flavours:
 *   - `useShortcut`     — single-keystroke binding (with optional modifiers).
 *   - `useKeySequence`  — Vim/GitHub-style chord, e.g. ['g','d'].
 *
 * Both ignore keystrokes originating in editable fields so typing in inputs
 * never triggers a navigation hotkey.
 */
import { useEffect, useRef } from 'react';
import { stepSequence as stepSequenceCore } from './commandRegistryCore';

export type ModifierKey = 'meta' | 'ctrl' | 'shift' | 'alt' | 'mod';

export interface ShortcutOptions {
  /** Modifier(s) that must be held. `mod` matches Ctrl on PC, ⌘ on Mac. */
  modifiers?: readonly ModifierKey[];
  /** Allow the shortcut to fire even while focus is in a form field. */
  allowInInput?: boolean;
  /** When false the shortcut is not registered. Useful for permission gating. */
  enabled?: boolean;
  /** Prevent the browser's default for the matched event. Default: true. */
  preventDefault?: boolean;
}

const EDITABLE_TAGS = new Set(['INPUT', 'TEXTAREA', 'SELECT']);

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (EDITABLE_TAGS.has(target.tagName)) return true;
  if (target.isContentEditable) return true;
  return false;
}

function modifiersMatch(e: KeyboardEvent, mods: readonly ModifierKey[]): boolean {
  const need = new Set(mods);
  // `mod` resolves to Meta on Mac, Ctrl elsewhere.
  if (need.has('mod')) {
    const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad|iPod/i.test(navigator.platform || '');
    need.delete('mod');
    need.add(isMac ? 'meta' : 'ctrl');
  }
  const has = {
    meta: e.metaKey,
    ctrl: e.ctrlKey,
    shift: e.shiftKey,
    alt: e.altKey,
  };
  for (const m of ['meta', 'ctrl', 'shift', 'alt'] as const) {
    if (need.has(m) !== has[m]) return false;
  }
  return true;
}

/**
 * Bind a single keystroke to a handler.
 *
 *     useShortcut('k', open, { modifiers: ['mod'] });
 *     useShortcut('Escape', close);
 */
export function useShortcut(
  key: string | readonly string[],
  handler: (e: KeyboardEvent) => void,
  options: ShortcutOptions = {},
): void {
  const handlerRef = useRef(handler);
  handlerRef.current = handler;

  const keys = Array.isArray(key) ? key : [key];

  useEffect(() => {
    if (options.enabled === false) return;
    const onKey = (e: KeyboardEvent) => {
      if (!options.allowInInput && isEditableTarget(e.target)) return;
      if (options.modifiers && !modifiersMatch(e, options.modifiers)) return;
      if (!options.modifiers && (e.metaKey || e.ctrlKey || e.altKey)) {
        // No modifier configured — reject events that carry one to avoid
        // hijacking standard browser shortcuts.
        return;
      }
      const match = keys.some(
        (k) => e.key === k || e.key.toLowerCase() === k.toLowerCase(),
      );
      if (!match) return;
      if (options.preventDefault !== false) e.preventDefault();
      handlerRef.current(e);
    };

    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
    // We intentionally exclude `keys` from deps — recomputed each render but
    // closed over by the handler, which itself reads from a ref.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    options.enabled,
    options.allowInInput,
    options.preventDefault,
    keys.join('|'),
    (options.modifiers ?? []).join('|'),
  ]);
}

/* ─── Sequence handler ──────────────────────────────────────────────── */

interface SequenceState {
  buffer: string[];
  expiresAt: number;
}

/**
 * Bind a set of multi-key sequences (e.g. `'g d'` → go dashboard).
 *
 *     useKeySequence({
 *       'g d': () => navigate('/'),
 *       'g l': () => navigate('/lab'),
 *     });
 *
 * Sequences time out after 1500 ms of inactivity.
 */
export function useKeySequence(
  bindings: Record<string, () => void>,
  options: { windowMs?: number; enabled?: boolean } = {},
): void {
  const bindingsRef = useRef(bindings);
  bindingsRef.current = bindings;

  useEffect(() => {
    if (options.enabled === false) return;
    let state: SequenceState = { buffer: [], expiresAt: 0 };
    const windowMs = options.windowMs ?? 1500;

    const onKey = (e: KeyboardEvent) => {
      if (isEditableTarget(e.target)) return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      // Only single printable keys advance a sequence.
      if (e.key.length !== 1) {
        state = { buffer: [], expiresAt: 0 };
        return;
      }
      const result = stepSequenceCore(
        state,
        e.key,
        Object.keys(bindingsRef.current),
        Date.now(),
        windowMs,
      );
      state = result.state;
      if (result.fired) {
        e.preventDefault();
        const fn = bindingsRef.current[result.fired];
        if (fn) fn();
      }
    };

    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [options.enabled, options.windowMs]);
}
