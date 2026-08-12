import { useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Keyboard, X, Command } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';

type Category = 'Global' | 'Navigation' | 'Workflow';

interface Shortcut {
  keys: string[];
  label: string;
  category: Category;
}

const SHORTCUTS: readonly Shortcut[] = [
  // Global
  { keys: ['CMD', 'K'], label: 'Open command palette', category: 'Global' },
  { keys: ['/'], label: 'Focus command palette search', category: 'Global' },
  { keys: ['?'], label: 'Show this shortcuts overlay', category: 'Global' },
  { keys: ['ESC'], label: 'Close modal / cancel current action', category: 'Global' },

  // Navigation (Vim-style chords)
  { keys: ['G', 'D'], label: 'Go to Dashboard', category: 'Navigation' },
  { keys: ['G', 'P'], label: 'Go to Patients', category: 'Navigation' },
  { keys: ['G', 'A'], label: 'Go to Appointments', category: 'Navigation' },
  { keys: ['G', 'I'], label: 'Go to Medical Intelligence', category: 'Navigation' },
  { keys: ['G', 'L'], label: 'Go to Laboratory', category: 'Navigation' },
  { keys: ['G', 'Q'], label: 'Go to Lab Work Queue', category: 'Navigation' },
  { keys: ['G', 'S'], label: 'Go to Settings', category: 'Navigation' },
  { keys: ['G', 'H'], label: 'Open this shortcuts overlay', category: 'Navigation' },

  // Workflow
  { keys: ['↑', '↓'], label: 'Move selection in lists & palette', category: 'Workflow' },
  { keys: ['Enter'], label: 'Activate the highlighted item', category: 'Workflow' },
  { keys: ['Tab'], label: 'Move focus across form controls', category: 'Workflow' },
];

const CATEGORIES: readonly Category[] = ['Global', 'Navigation', 'Workflow'];

export function ShortcutsModal({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  // useLanguage isn't strictly required here, but keep it so future i18n
  // additions stay one edit away.
  useLanguage();

  // Close on backdrop ESC even though the parent listener also handles it —
  // belt and braces, mirrors `<dialog>` semantics.
  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Keyboard shortcuts"
          className="fixed inset-0 z-[110] flex items-center justify-center p-4"
        >
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-slate-900/80 backdrop-blur-md"
          />
          <motion.div
            initial={{ scale: 0.92, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.92, opacity: 0, y: 20 }}
            transition={{ duration: 0.18 }}
            className="relative bg-white w-full max-w-3xl rounded-[2.5rem] shadow-[0_50px_100px_-20px_rgba(0,0,0,0.5)] overflow-hidden border border-slate-100"
          >
            <div className="p-8 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-5">
                <div className="w-12 h-12 bg-indigo-600 rounded-2xl flex items-center justify-center text-white shadow-xl shadow-indigo-500/20">
                  <Keyboard size={24} />
                </div>
                <div>
                  <h3 className="text-xl font-black uppercase tracking-tight text-slate-900">
                    Keyboard shortcuts
                  </h3>
                  <p className="text-[10px] font-black text-indigo-500 uppercase tracking-[0.2em] mt-1">
                    Press <kbd className="px-1.5 py-0.5 bg-white border border-slate-200 rounded text-[10px]">?</kbd> any time to reopen
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={onClose}
                aria-label="Close"
                className="p-3 text-slate-400 hover:text-rose-500 transition-colors rounded-xl hover:bg-rose-50"
              >
                <X size={20} />
              </button>
            </div>

            <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-8 max-h-[60vh] overflow-y-auto custom-scrollbar">
              {CATEGORIES.map((cat) => {
                const items = SHORTCUTS.filter((s) => s.category === cat);
                if (!items.length) return null;
                return (
                  <div key={cat} className="space-y-3">
                    <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400">
                      {cat}
                    </h4>
                    <div className="space-y-2.5">
                      {items.map((s, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between gap-4 group"
                        >
                          <span className="text-sm font-medium text-slate-700 group-hover:text-slate-900 transition-colors">
                            {s.label}
                          </span>
                          <div className="flex gap-1 shrink-0">
                            {s.keys.map((k) => (
                              <kbd
                                key={k}
                                className="px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-[10px] font-black text-slate-600 shadow-sm min-w-[28px] text-center"
                              >
                                {k === 'CMD' ? <Command size={10} /> : k}
                              </kbd>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="p-5 bg-slate-50 border-t border-slate-100 flex justify-center">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                Shortcuts are disabled while typing in input fields.
              </p>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
