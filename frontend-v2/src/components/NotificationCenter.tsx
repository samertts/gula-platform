import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Bell, 
  CheckCheck, 
  Trash2, 
  AlertTriangle, 
  Clock, 
  Info, 
  Database, 
  FlaskConical,
  X,
  ChevronRight
} from 'lucide-react';
import { useNotifications } from '../contexts/NotificationContext';
import { useLanguage } from '../contexts/LanguageContext';
import { cn } from '../lib/utils';
import { GulaEvent } from '../types/domain';

interface NotificationCenterProps {
  isOpen: boolean;
  onClose: () => void;
}

export const NotificationCenter: React.FC<NotificationCenterProps> = ({ isOpen, onClose }) => {
  const { notifications, unreadCount, markAsRead, markAllAsRead } = useNotifications();
  const { dir } = useLanguage();
  const isRtl = dir === 'rtl';

  const getIcon = (type: string, priority: string) => {
    if (priority === 'stat' || type === 'critical_alert') return <AlertTriangle className="text-red-500" />;
    if (type === 'expiring_reagent') return <Clock className="text-amber-500" />;
    if (type === 'lab_result_ready') return <FlaskConical className="text-green-500" />;
    if (type === 'inventory_low') return <Database className="text-orange-500" />;
    return <Info className="text-indigo-500" />;
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40 bg-transparent" 
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10, x: isRtl ? -20 : 20 }}
            animate={{ opacity: 1, scale: 1, y: 0, x: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            className={cn(
              "absolute top-20 z-50 w-80 sm:w-96 bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden",
              isRtl ? "left-6" : "right-6"
            )}
          >
            <div className="p-6 border-b border-slate-50 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-slate-900">Notifications</h3>
                {unreadCount > 0 && (
                  <span className="bg-indigo-600 text-white text-[10px] font-black px-2 py-0.5 rounded-full">
                    {unreadCount}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button 
                  onClick={markAllAsRead}
                  className="p-2 text-slate-400 hover:text-indigo-600 transition-colors"
                  title="Mark all as read"
                >
                  <CheckCheck size={18} />
                </button>
                <button 
                  onClick={onClose}
                  className="p-2 text-slate-400 hover:text-slate-600 transition-colors"
                >
                  <X size={18} />
                </button>
              </div>
            </div>

            <div className="max-h-[400px] overflow-y-auto custom-scrollbar">
              {notifications.length === 0 ? (
                <div className="p-12 text-center text-slate-400">
                  <Bell className="w-12 h-12 mx-auto mb-4 opacity-20" />
                  <p className="text-sm font-medium">All caught up!</p>
                </div>
              ) : (
                <div className="divide-y divide-slate-50">
                  {notifications.map((n) => (
                    <motion.div
                      key={n.id}
                      layout
                      className={cn(
                        "p-4 flex gap-4 hover:bg-slate-50 transition-colors cursor-pointer group relative",
                        !n.read && "bg-indigo-50/30"
                      )}
                      onClick={() => markAsRead(n.id)}
                    >
                      <div className={cn(
                        "w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-sm",
                        !n.read ? "bg-white" : "bg-slate-50"
                      )}>
                        {getIcon(n.type, n.priority)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-0.5">
                          <p className="font-bold text-sm text-slate-900 truncate pr-4">{n.title}</p>
                          <span className="text-[10px] text-slate-400 whitespace-nowrap">
                            {n.createdAt?.seconds ? new Date(n.createdAt.seconds * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Now'}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">
                          {n.message}
                        </p>
                        {!n.read && (
                          <div className="absolute right-4 top-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-indigo-600 rounded-full" />
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>

            <button className="w-full py-4 bg-slate-50 text-[10px] font-black uppercase tracking-widest text-slate-400 hover:text-indigo-600 hover:bg-slate-100 transition-all border-t border-slate-100">
              View All History
            </button>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
