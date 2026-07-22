import { useEffect, useMemo, useRef, useState, memo } from 'react';
import { motion } from 'motion/react';
import {ChevronRight, Command as CommandIcon, Search} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import { cn } from '../lib/utils';
import {
  type CommandDefinition,
  commandsForProfile,
  searchCommands,
} from '../lib/commandRegistry';
import { Badge, Kbd } from './ui';
export const CommandPalette = memo(function CommandPalette() {
  const { t, language } = useLanguage();
  const { profile } = useAuth();
  const navigate = useNavigate();
  const isRtl = language === 'AR' || language === 'KU' || language === 'SY';
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const [mode, setMode] = useState<'commands' | 'search'>('commands');
  const inputRef = useRef<HTMLInputElement | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);
  const previouslyFocused = useRef<HTMLElement | null>(null);
  const availableCommands = useMemo(() => commandsForProfile(profile), [profile]);
  const results = useMemo(() => searchCommands(availableCommands, t, query), [availableCommands, t, query]);
  useEffect(() => { setActiveIndex(0); }, [query, isOpen]);
  const open = () => {
    previouslyFocused.current = typeof document !== 'undefined' ? (document.activeElement as HTMLElement | null) : null;
    setIsOpen(true);
    setMode(query ? 'search' : 'commands');
  };
  const close = () => {
    setIsOpen(false);
    setQuery('');
    queueMicrotask(() => {
      const el = previouslyFocused.current;
      if (el && typeof el.focus === 'function') el.focus();
      previouslyFocused.current = null;
    });
  };
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
  }, [isOpen, query]);
  useEffect(() => {
    if (isOpen) requestAnimationFrame(() => inputRef.current?.focus());
  }, [isOpen]);
  const runCommand = (cmd: CommandDefinition) => {
    cmd.run({ navigate, t, profile, openShortcuts: () => window.dispatchEvent(new CustomEvent('open-shortcuts')) });
    close();
  };
  const onInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape') { e.preventDefault(); close(); return; }
    if (e.key === 'ArrowDown') { e.preventDefault(); setActiveIndex(i => results.length === 0 ? 0 : (i + 1) % results.length); return; }
    if (e.key === 'ArrowUp') { e.preventDefault(); setActiveIndex(i => results.length === 0 ? 0 : (i - 1 + results.length) % results.length); return; }
    if (e.key === 'Home') { e.preventDefault(); setActiveIndex(0); return; }
    if (e.key === 'End') { e.preventDefault(); setActiveIndex(Math.max(0, results.length - 1)); return; }
    if (e.key === 'Enter') { e.preventDefault(); const cmd = results[activeIndex]; if (cmd) runCommand(cmd); return; }
    if (e.key === 'Tab') {
      e.preventDefault();
      setMode(m => m === 'commands' ? 'search' : 'commands');
    }
  };
  useEffect(() => {
    if (!isOpen) return;
    const el = listRef.current?.querySelector<HTMLElement>(`[data-cmd-idx="${activeIndex}"]`);
    el?.scrollIntoView({ block: 'nearest' });
  }, [activeIndex, isOpen]);
  if (!isOpen) return null;
  const grouped: Array<{ category: string; entries: { cmd: CommandDefinition; idx: number }[] }> = [];
  results.forEach((cmd, idx) => {
    const last = grouped[grouped.length - 1];
    if (last && last.category === cmd.category) last.entries.push({ cmd, idx });
    else grouped.push({ category: cmd.category, entries: [{ cmd, idx }] });
  });
  return (
    <div
      className="fixed inset-0 z-[100] flex items-start justify-center pt-[12vh] px-4"
      onMouseDown={(e) => { if (e.target === e.currentTarget) close(); }}
    >
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        onClick={close} className="absolute inset-0 bg-slate-900/50 backdrop-blur-md" aria-hidden="true"
      />
      <motion.div
        role="dialog" aria-modal="true" aria-label={t.searchCommands || 'Universal Search'}
        initial={{ opacity: 0, scale: 0.96, y: -16 }} animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96, y: -16 }} transition={{ duration: 0.15 }}
        className="relative w-full max-w-2xl bg-white rounded-[2.5rem] shadow-2xl shadow-indigo-500/20 overflow-hidden border border-slate-100"
        dir={isRtl ? 'rtl' : 'ltr'}
      >
        {/* Search header */}
        <div className="p-5 border-b border-slate-100 flex items-center gap-4">
          <div className="w-10 h-10 bg-indigo-600 rounded-2xl flex items-center justify-center text-white shadow-xl shadow-indigo-100 shrink-0">
            <CommandIcon size={22} />
          </div>
          <input
            ref={inputRef} type="text" role="combobox" aria-expanded="true" aria-controls="command-palette-list"
            aria-activedescendant={results[activeIndex] ? `cmd-${results[activeIndex].id}` : undefined}
            autoComplete="off" spellCheck={false}
            placeholder={t.searchEverything || 'Search patients, commands, settings, help...'}
            value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={onInputKeyDown}
            className="flex-1 bg-transparent border-none outline-none text-lg font-bold text-slate-900 placeholder:text-slate-300 tracking-tight"
          />
          <div className="flex items-center gap-2 shrink-0">
            <Kbd size="md" className="bg-slate-900 text-white border-none shadow-md">ESC</Kbd>
          </div>
        </div>
        {/* Mode tabs */}
        <div className="px-5 pt-3 pb-1 flex gap-1">
          <button
            onClick={() => setMode('commands')}
            className={cn(
              'px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider transition-all',
              mode === 'commands' ? 'bg-indigo-100 text-indigo-700' : 'text-slate-400 hover:text-slate-600'
            )}
          >
            <CommandIcon size={12} className="inline mr-1" />
            Commands
          </button>
          <button
            onClick={() => setMode('search')}
            className={cn(
              'px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider transition-all',
              mode === 'search' ? 'bg-indigo-100 text-indigo-700' : 'text-slate-400 hover:text-slate-600'
            )}
          >
            <Search size={12} className="inline mr-1" />
            Search
          </button>
          <span className="ml-auto text-[9px] text-slate-300 flex items-center gap-1">
            Tab to switch <Kbd>⌃Tab</Kbd>
          </span>
        </div>
        {/* Results */}
        <div id="command-palette-list" ref={listRef} role="listbox" aria-label="Commands"
          className="p-4 max-h-[55vh] overflow-y-auto custom-scrollbar bg-slate-50/30"
        >
          {results.length === 0 ? (
            <div className="p-10 text-center">
              <div className="w-14 h-14 bg-slate-100 rounded-3xl flex items-center justify-center mx-auto mb-4">
                <Search size={24} className="text-slate-300" />
              </div>
              <p className="text-slate-500 font-bold">{t.noResultsFound || 'No results found.'}</p>
              <p className="text-[10px] text-slate-300 font-black uppercase mt-2 tracking-widest">Try a different search or press Esc</p>
            </div>
          ) : (
            grouped.map((group) => (
              <div key={group.category} className="mb-5 last:mb-0">
                <div className="px-3 py-2 text-[10px] font-black text-indigo-600 uppercase tracking-[0.2em] mb-1 flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-indigo-600 rounded-full" />
                  {group.category}
                  <Badge variant="primary" className="ml-auto">{group.entries.length}</Badge>
                </div>
                <div className="space-y-1">
                  {group.entries.map(({ cmd, idx }) => {
                    const isActive = idx === activeIndex;
                    return (
                      <button key={cmd.id} id={`cmd-${cmd.id}`} type="button" role="option"
                        aria-selected={isActive} data-cmd-idx={idx}
                        onMouseEnter={() => setActiveIndex(idx)} onClick={() => runCommand(cmd)}
                        className={cn(
                          'w-full flex items-center gap-3 p-3 rounded-2xl transition-colors group text-left',
                          isActive ? 'bg-white shadow-md shadow-indigo-100/60' : 'hover:bg-white/60'
                        )}
                      >
                        <div className={cn(
                          'w-9 h-9 rounded-xl flex items-center justify-center shrink-0 transition-colors',
                          isActive ? 'bg-indigo-600 text-white' : 'bg-white border border-slate-100 text-slate-400 group-hover:bg-indigo-50 group-hover:text-indigo-600'
                        )}>
                          <cmd.icon size={18} />
                        </div>
                        <span className={cn('flex-1 font-bold tracking-tight text-sm', isActive ? 'text-indigo-900' : 'text-slate-700')}>
                          {cmd.label(t)}
                        </span>
                        {cmd.shortcut && (
                          <div className="flex gap-1 shrink-0">
                            {cmd.shortcut.map((s, i) => (
                              <Kbd key={i} className={isActive ? 'bg-indigo-600 text-white border-indigo-500' : ''}>{s}</Kbd>
                            ))}
                          </div>
                        )}
                        <ChevronRight size={14} className={cn('shrink-0 transition-transform', isActive ? 'text-indigo-600 translate-x-0.5' : 'text-slate-300', isRtl && 'rotate-180')} />
                      </button>
                    );
                  })}
                </div>
              </div>
            ))
          )}
        </div>
        {/* Footer */}
        <div className="px-5 py-3 bg-slate-900 border-t border-slate-800 flex justify-between items-center text-[10px] font-bold text-slate-400">
          <div className="flex gap-4">
            <span className="flex items-center gap-1.5 text-indigo-400">
              <ChevronRight size={12} /> <span>Run</span>
            </span>
            <span className="flex items-center gap-1.5">
              ↑↓ <span>Navigate</span>
            </span>
            <span className="flex items-center gap-1.5">
              Tab <span>Switch mode</span>
            </span>
          </div>
          <span className="flex items-center gap-1.5 text-indigo-400">
            <CommandIcon size={12} /> {results.length} result{results.length === 1 ? '' : 's'}
          </span>
        </div>
      </motion.div>
    </div>
  );
});