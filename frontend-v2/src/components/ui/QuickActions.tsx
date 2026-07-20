import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, User, Calendar, FileText, FlaskConical, Pill, Activity, X } from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { cn } from '../../lib/utils';
import { motion, AnimatePresence } from 'motion/react';

interface QuickAction {
  id: string;
  icon: any;
  label: string;
  description: string;
  path: string;
  shortcut?: string;
}

const ACTIONS: QuickAction[] = [
  { id: 'patient', icon: User, label: 'Register Patient', description: 'New patient record', path: '/citizen/register' },
  { id: 'appointment', icon: Calendar, label: 'Schedule Appointment', description: 'Book a visit', path: '/appointments' },
  { id: 'order', icon: FileText, label: 'New Lab Order', description: 'Create test order', path: '/lab/queue' },
  { id: 'result', icon: FlaskConical, label: 'Enter Result', description: 'Record test results', path: '/lab/queue' },
  { id: 'medication', icon: Pill, label: 'Prescribe', description: 'Add medication', path: '/citizen/medications' },
  { id: 'vital', icon: Activity, label: 'Record Vitals', description: 'Log patient vitals', path: '/patients' },
];

export function QuickActions() {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();
  const { t, isRtl } = useLanguage();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setIsOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleAction = useCallback((path: string) => {
    navigate(path);
    setIsOpen(false);
  }, [navigate]);

  return (
    <div ref={ref} className="fixed bottom-6 right-6 z-50">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="absolute bottom-16 right-0 bg-white border border-slate-200 rounded-2xl shadow-2xl p-2 min-w-[220px]"
          >
            <div className="px-3 py-2 text-[9px] font-black uppercase tracking-widest text-slate-400 border-b border-slate-100 mb-1">
              {t.quickActions || 'Quick Actions'}
            </div>
            {ACTIONS.map(action => (
              <button
                key={action.id}
                onClick={() => handleAction(action.path)}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 hover:bg-indigo-50 hover:text-indigo-600 transition-all"
              >
                <div className="w-8 h-8 bg-slate-100 rounded-xl flex items-center justify-center text-slate-500 shrink-0">
                  <action.icon size={16} />
                </div>
                <div className="flex flex-col items-start">
                  <span className="text-sm font-bold">{action.label}</span>
                  <span className="text-[9px] text-slate-400">{action.description}</span>
                </div>
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'w-14 h-14 rounded-2xl shadow-2xl flex items-center justify-center transition-all active:scale-90',
          isOpen ? 'bg-slate-900 text-white rotate-45' : 'bg-indigo-600 text-white hover:bg-indigo-500'
        )}
      >
        {isOpen ? <X size={24} /> : <Plus size={24} />}
      </button>
    </div>
  );
}
