import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '../lib/utils';

interface ClickToCopyProps {
  text: string;
  className?: string;
}

export function ClickToCopy({ text, className }: ClickToCopyProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy!', err);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className={cn(
        "group flex items-center gap-2 hover:text-indigo-600 transition-colors relative",
        className
      )}
    >
      <span className="font-mono">{text}</span>
      <div className="relative w-4 h-4">
        <AnimatePresence mode="wait">
          {copied ? (
            <motion.div
              key="check"
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
            >
              <Check size={14} className="text-emerald-500" />
            </motion.div>
          ) : (
            <motion.div
              key="copy"
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
            >
              <Copy size={14} className="opacity-40 group-hover:opacity-100 transition-opacity" />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      
      {copied && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: -20 }}
          exit={{ opacity: 0 }}
          className="absolute left-1/2 -translate-x-1/2 bg-slate-900 text-white text-[9px] font-black uppercase tracking-widest px-2 py-1 rounded shadow-xl pointer-events-none"
        >
          Copied
        </motion.div>
      )}
    </button>
  );
}
