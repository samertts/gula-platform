import { useEffect, useMemo, useRef, useState } from 'react';
import { motion } from 'motion/react';
import { ChevronRight, Command as CommandIcon, Search } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { cn } from '../lib/utils';
import {
  type CommandDefinition,
  commandsForProfile,
  searchCommands,
} from '../lib/commandRegistry';

/**
 * Production-grade command palette.
 *
 * - Cmd/Ctrl+K toggles open. Window also listens for the legacy
 *   `open-command-palette` CustomEvent so the existing TopBar input still
 *   triggers it.
 * - Full keyboard navigation: Up/Down/Home/End/Enter/Escape.
 * - Restores focus to the previously-focused element when closed.
 * - Filters commands by the user's wing/role so the palette never offers an
 *   action the user cannot reach.
 * - aria roles: combobox (input) + listbox (results) + option (rows).
 * - Visual identity preserved from the previous version.
 */
export function CommandPalette() {
  const { t, language } = useLanguage();
  const { profile } = useAuth();
  const navigate = useNavigate();
  const isRtl = language === 'AR' || language === 'KU' || language === 'SY';

  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);

  const inputRef = useRef<HTMLInputElement | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);
  const previouslyFocused = useRef<HTMLElement | null>(null);

  // Build the available command set once per profile change.
  const availableCommands = useMemo(
    () => commandsForProfile(profile),
    [profile],
  );

  // Re-sort/filter on every query change.
  const results = useMemo(
    () => searchCommands(availableCommands, t, query),
    [availableCommands, t, query],
  );

  // Reset highlight whenever results change.
  useEffect(() => {
    setActiveIndex(0);
  }, [query, isOpen]);

  /** Open / close handlers. */
  const open = () => {
    previouslyFocused.current =
      typeof document !== 'undefined'
        ? (document.activeElement as HTMLElement | null)
        : null;
    setIsOpen(true);
  };

  const close = () => {
    setIsOpen(false);
    setQuery('');
    // Return focus to whatever was active before the palette opened so the
    // user lands back where they started — important for screen readers.
    queueMicrotask(() => {
      const el = previouslyFocused.current;
      if (el && typeof el.focus === 'function') el.focus();
      previouslyFocused.current = null;
    });
  };

  /** Keyboard wiring. */
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (isOpen) close();
        else open();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    const onOpenEvent = () => open();
    window.addEventListener('open-command-palette', onOpenEvent);
    return () => {
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('open-command-palette', onOpenEvent);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  // Autofocus the input when opening.
  useEffect(() => {
    if (isOpen) {
      // requestAnimationFrame so the modal has a chance to mount first.
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [isOpen]);

  const runCommand = (cmd: CommandDefinition) => {
    cmd.run({
      navigate,
      t,
      profile,
      openShortcuts: () =>
        window.dispatchEvent(new CustomEvent('open-shortcuts')),
    });
    close();
  };

  const onInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      close();
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((i) => (results.length === 0 ? 0 : (i + 1) % results.length));
      return;
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((i) =>
        results.length === 0 ? 0 : (i - 1 + results.length) % results.length,
      );
      return;
    }
    if (e.key === 'Home') {
      e.preventDefault();
      setActiveIndex(0);
      return;
    }
    if (e.key === 'End') {
      e.preventDefault();
      setActiveIndex(Math.max(0, results.length - 1));
      return;
    }
    if (e.key === 'Enter') {
      e.preventDefault();
      const cmd = results[activeIndex];
      if (cmd) runCommand(cmd);
      return;
    }
  };

  // Keep the active row scrolled into view.
  useEffect(() => {
    if (!isOpen) return;
    const el = listRef.current?.querySelector<HTMLElement>(
      `[data-cmd-idx="${activeIndex}"]`,
    );
    el?.scrollIntoView({ block: 'nearest' });
  }, [activeIndex, isOpen]);

  if (!isOpen) return null;

  // Group results by category for readability while preserving the flat
  // index used for keyboard navigation.
  const grouped: Array<{ category: string; entries: { cmd: CommandDefinition; idx: number }[] }> = [];
  results.forEach((cmd, idx) => {
    const last = grouped[grouped.length - 1];
    if (last && last.category === cmd.category) {
      last.entries.push({ cmd, idx });
    } else {
      grouped.push({ category: cmd.category, entries: [{ cmd, idx }] });
    }
  });

  return (
    <div
      className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] px-4"
      // Stop pointer events from leaking through to the underlying app
      // while the palette is open.
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) close();
      }}
    >
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={close}
          className="absolute inset-0 bg-slate-900/40 backdrop-blur-md"
          aria-hidden="true"
        />

        <motion.div
          role="dialog"
          aria-modal="true"
          aria-label={t.searchCommands || 'Command palette'}
          initial={{ opacity: 0, scale: 0.96, y: -16 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: -16 }}
          transition={{ duration: 0.15 }}
          className="relative w-full max-w-2xl bg-white rounded-[2.5rem] shadow-2xl shadow-indigo-500/20 overflow-hidden border border-slate-100"
          dir={isRtl ? 'rtl' : 'ltr'}
        >
          <div className="p-6 border-b border-slate-100 flex items-center gap-5">
            <div className="w-12 h-12 bg-indigo-600 rounded-2xl flex items-center justify-center text-white shadow-xl shadow-indigo-100 shrink-0">
              <CommandIcon size={24} />
            </div>
            <input
              ref={inputRef}
              type="text"
              role="combobox"
              aria-expanded="true"
              aria-controls="command-palette-list"
              aria-activedescendant={
                results[activeIndex] ? `cmd-${results[activeIndex].id}` : undefined
              }
              autoComplete="off"
              spellCheck={false}
              placeholder={
                t.searchCommands || 'Universal Command Search (Ctrl+K)…'
              }
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={onInputKeyDown}
              className="flex-1 bg-transparent border-none outline-none text-xl font-black text-slate-900 placeholder:text-slate-300 tracking-tight"
            />
            <div className="flex items-center gap-2 shrink-0">
              <kbd className="px-2.5 py-1 bg-slate-900 rounded-lg text-[10px] font-black text-white shadow-md">
                ESC
              </kbd>
            </div>
          </div>

          <div
            id="command-palette-list"
            ref={listRef}
            role="listbox"
            aria-label={t.searchCommands || 'Commands'}
            className="p-4 max-h-[60vh] overflow-y-auto custom-scrollbar bg-slate-50/30"
          >
            {results.length === 0 ? (
              <div className="p-12 text-center" data-testid="palette-empty">
                <div className="w-16 h-16 bg-slate-100 rounded-3xl flex items-center justify-center mx-auto mb-4">
                  <Search size={28} className="text-slate-300" />
                </div>
                <p className="text-slate-500 font-bold">
                  {t.noResultsFound || 'No commands match your search.'}
                </p>
                <p className="text-[10px] text-slate-300 font-black uppercase mt-2 tracking-widest">
                  Try a different word or press Esc to close
                </p>
              </div>
            ) : (
              grouped.map((group) => (
                <div key={group.category} className="mb-6 last:mb-0">
                  <div className="px-3 py-2 text-[10px] font-black text-indigo-600 uppercase tracking-[0.2em] mb-2 flex items-center gap-2">
                    <div className="w-1.5 h-1.5 bg-indigo-600 rounded-full" />
                    {group.category}
                  </div>
                  <div className="space-y-1">
                    {group.entries.map(({ cmd, idx }) => {
                      const isActive = idx === activeIndex;
                      return (
                        <button
                          key={cmd.id}
                          id={`cmd-${cmd.id}`}
                          type="button"
                          role="option"
                          aria-selected={isActive}
                          data-cmd-idx={idx}
                          onMouseEnter={() => setActiveIndex(idx)}
                          onClick={() => runCommand(cmd)}
                          className={cn(
                            'w-full flex items-center gap-4 p-3 rounded-2xl transition-colors group text-left',
                            isActive
                              ? 'bg-white shadow-md shadow-indigo-100/60'
                              : 'hover:bg-white/60',
                          )}
                        >
                          <div
                            className={cn(
                              'w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition-colors',
                              isActive
                                ? 'bg-indigo-600 text-white'
                                : 'bg-white border border-slate-100 text-slate-400 group-hover:bg-indigo-50 group-hover:text-indigo-600',
                            )}
                          >
                            <cmd.icon size={20} />
                          </div>
                          <span
                            className={cn(
                              'flex-1 font-bold tracking-tight text-base',
                              isActive ? 'text-indigo-900' : 'text-slate-700',
                            )}
                          >
                            {cmd.label(t)}
                          </span>
                          {cmd.shortcut && (
                            <div className="flex gap-1 shrink-0">
                              {cmd.shortcut.map((s, i) => (
                                <kbd
                                  key={i}
                                  className={cn(
                                    'px-2 py-1 rounded-lg text-[10px] font-black shadow-sm',
                                    isActive
                                      ? 'bg-indigo-600 text-white'
                                      : 'bg-slate-900 text-white',
                                  )}
                                >
                                  {s}
                                </kbd>
                              ))}
                            </div>
                          )}
                          <ChevronRight
                            size={16}
                            className={cn(
                              'shrink-0 transition-transform',
                              isActive
                                ? 'text-indigo-600 translate-x-0.5'
                                : 'text-slate-300',
                              isRtl && 'rotate-180',
                            )}
                          />
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="px-6 py-3 bg-slate-900 border-t border-slate-800 flex justify-between items-center text-[10px] font-bold text-slate-400">
            <div className="flex gap-4">
              <span className="flex items-center gap-2 text-indigo-400">
                <ChevronRight size={12} /> Enter to run
              </span>
              <span className="flex items-center gap-2">
                ↑↓ to navigate
              </span>
            </div>
            <span className="flex items-center gap-2">
              <CommandIcon size={12} /> {results.length} result
              {results.length === 1 ? '' : 's'}
            </span>
          </div>
        </motion.div>
      </div>
  );
}
