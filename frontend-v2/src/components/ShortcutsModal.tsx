import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Keyboard, X, Command } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';

interface Shortcut {
  keys: string[];
  label: string;
  category: 'Global' | 'Navigation' | 'Laboratory';
}

const SHORTCUTS: Shortcut[] = [
  { keys: ['CMD', 'K'], label: 'Open Command Palette', category: 'Global' },
  { keys: ['?'], label: 'Open Shortcuts Help', category: 'Global' },
  { keys: ['ESC'], label: 'Close Modal / Cancel', category: 'Global' },
  { keys: ['G', 'D'], label: 'Go to Dashboard', category: 'Navigation' },
  { keys: ['G', 'L'], label: 'Go to Laboratory', category: 'Navigation' },
  { keys: ['G', 'S'], label: 'Go to Settings', category: 'Navigation' },
  { keys: ['S', 'B'], label: 'Scan Biometrics', category: 'Laboratory' },
];

export function ShortcutsModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const { isRtl } = useLanguage();

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[110] flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-slate-900/80 backdrop-blur-md"
          />
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            className="relative bg-white w-full max-w-2xl rounded-[3rem] shadow-[0_50px_100px_-20px_rgba(0,0,0,0.5)] overflow-hidden border border-slate-100"
          >
            <div className="p-10 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-6">
                <div className="w-14 h-14 bg-indigo-600 rounded-[1.5rem] flex items-center justify-center text-white shadow-2xl shadow-indigo-500/20">
                   <Keyboard size={28} />
                </div>
                <div>
                   <h3 className="text-2xl font-black uppercase tracking-tight">System Shortcuts</h3>
                   <p className="text-[10px] font-black text-indigo-400 uppercase tracking-[0.2em]">Discover GULA Power Commands</p>
                </div>
              </div>
              <button 
                onClick={onClose}
                className="p-4 text-slate-300 hover:text-rose-500 transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            <div className="p-10 grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-8 max-h-[60vh] overflow-y-auto custom-scrollbar">
              {['Global', 'Navigation', 'Laboratory'].map(cat => (
                <div key={cat} className="space-y-4">
                  <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-400 mb-6">{cat}</h4>
                  <div className="space-y-3">
                    {SHORTCUTS.filter(s => s.category === cat).map((s, i) => (
                      <div key={i} className="flex items-center justify-between group">
                        <span className="text-sm font-bold text-slate-600 group-hover:text-slate-900 transition-colors">{s.label}</span>
                        <div className="flex gap-1.5">
                          {s.keys.map(k => (
                             <kbd key={k} className="px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-[10px] font-black text-slate-400 shadow-sm min-w-[32px] text-center">
                               {k === 'CMD' ? <Command size={10} /> : k}
                             </kbd>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="p-8 bg-slate-50 border-t border-slate-100 flex justify-center">
               <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Sovereign OS Intelligence Interface v4.0.1</p>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
