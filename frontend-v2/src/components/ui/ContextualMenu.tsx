import { useEffect, useRef, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Copy, Edit3, Trash2, ExternalLink, History, Star, Pin, Share2, Download } from 'lucide-react';
import { cn } from '../../lib/utils';
import { motion, AnimatePresence } from 'motion/react';
interface ContextAction {
  id: string;
  icon: any;
  label: string;
  action: () => void;
  destructive?: boolean;
}
interface ContextualMenuProps {
  items: ContextAction[];
  children: React.ReactNode;
  className?: string;
}
export function ContextualMenu({ items, children, className }: ContextualMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const handler = () => setIsOpen(false);
    document.addEventListener('mousedown', handler);
    document.addEventListener('scroll', handler);
    return () => {
      document.removeEventListener('mousedown', handler);
      document.removeEventListener('scroll', handler);
    };
  }, []);
  const handleContextMenu = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setPos({ x: e.clientX, y: e.clientY });
    setIsOpen(true);
  }, []);
  const handleLongPress = useCallback((e: React.TouchEvent) => {
    e.preventDefault();
    setPos({ x: e.touches[0]!.clientX, y: e.touches[0]!.clientY });
    setIsOpen(true);
  }, []);
  return (
    <div ref={ref} onContextMenu={handleContextMenu} onTouchStart={handleLongPress} className={cn('relative', className)}>
      {children}
      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-[100]"
              onClick={() => setIsOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              style={{ left: pos.x, top: pos.y }}
              className="fixed z-[101] bg-white border border-slate-200 rounded-2xl shadow-2xl p-1.5 min-w-[180px]"
            >
              {items.map(item => (
                <button
                  key={item.id}
                  onClick={() => { item.action(); setIsOpen(false); }}
                  className={cn(
                    'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all',
                    item.destructive
                      ? 'text-red-600 hover:bg-red-50'
                      : 'text-slate-700 hover:bg-indigo-50 hover:text-indigo-600'
                  )}
                >
                  <item.icon size={16} className={item.destructive ? 'text-red-400' : 'text-slate-400'} />
                  <span>{item.label}</span>
                </button>
              ))}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}