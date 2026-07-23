import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  Bell, CheckCheck, AlertTriangle, Clock, Info, Database, FlaskConical,
  X, } from 'lucide-react';
import { useNotifications } from '../contexts/NotificationContext';
import { useLanguage } from '../contexts/LanguageContext';
import { cn, formatTime } from '../lib/utils';
import { } from '../types/domain';
import {Badge} from './ui';
interface NotificationCenterProps {
  isOpen: boolean;
  onClose: () => void;
}
type FilterMode = 'all' | 'unread' | 'critical' | 'alerts' | 'results';
export const NotificationCenter: React.FC<NotificationCenterProps> = ({ isOpen, onClose }) => {
  const { notifications, unreadCount, markAsRead, markAllAsRead } = useNotifications();
  const { t, dir, language } = useLanguage();
  const isRtl = dir === 'rtl';
  const [filter, setFilter] = useState<FilterMode>('all');
  const getIcon = (type: string, priority: string) => {
    if (priority === 'stat' || type === 'critical_alert') return <AlertTriangle className="text-red-500" size={16} />;
    if (type === 'expiring_reagent') return <Clock className="text-amber-500" size={16} />;
    if (type === 'lab_result_ready') return <FlaskConical className="text-emerald-500" size={16} />;
    if (type === 'inventory_low') return <Database className="text-orange-500" size={16} />;
    return <Info className="text-indigo-500" size={16} />;
  };
  const filtered = notifications.filter(n => {
    if (filter === 'unread') return !n.read;
    if (filter === 'critical') return n.priority === 'stat' || n.type === 'critical_alert';
    if (filter === 'alerts') return ['critical_alert', 'expiring_reagent', 'inventory_low'].includes(n.type);
    if (filter === 'results') return n.type === 'lab_result_ready';
    return true;
  });
  const filters: { key: FilterMode; label: string; count?: number }[] = [
    { key: 'all', label: 'All', count: notifications.length },
    { key: 'unread', label: 'Unread', count: unreadCount },
    { key: 'critical', label: 'Critical' },
    { key: 'alerts', label: 'Alerts' },
    { key: 'results', label: 'Results' },
  ];
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <div className="fixed inset-0 z-40 bg-transparent" onClick={onClose} />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10, x: isRtl ? -20 : 20 }}
            animate={{ opacity: 1, scale: 1, y: 0, x: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            className={cn('absolute top-16 z-50 w-80 sm:w-96 bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden', isRtl ? 'left-6' : 'right-6')}
          >
            {/* Header */}
            <div className="p-5 border-b border-slate-100 bg-slate-50/50">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Bell size={16} className="text-slate-600" />
                  <h3 className="font-bold text-slate-900 text-sm">{t.notifications || 'Notifications'}</h3>
                  {unreadCount > 0 && <Badge count={unreadCount} variant="danger" />}
                </div>
                <div className="flex items-center gap-1">
                  <button onClick={markAllAsRead} className="p-1.5 text-slate-400 hover:text-indigo-600 rounded-lg hover:bg-indigo-50 transition-all" title="Mark all as read">
                    <CheckCheck size={16} />
                  </button>
                  <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-all">
                    <X size={16} />
                  </button>
                </div>
              </div>
              {/* Filter pills */}
              <div className="flex gap-1.5 overflow-x-auto no-scrollbar pb-1">
                {filters.map(f => (
                  <button
                    key={f.key}
                    onClick={() => setFilter(f.key)}
                    className={cn(
                      'flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all whitespace-nowrap',
                      filter === f.key ? 'bg-indigo-600 text-white shadow-sm' : 'bg-white text-slate-500 hover:bg-slate-100 border border-slate-200'
                    )}
                  >
                    {f.label}
                    {f.count !== undefined && filter !== f.key && ` (${f.count})`}
                  </button>
                ))}
              </div>
            </div>
            {/* Notification list */}
            <div className="max-h-[400px] overflow-y-auto custom-scrollbar">
              {filtered.length === 0 ? (
                <div className="p-12 text-center text-slate-400">
                  <Bell size={36} className="mx-auto mb-3 opacity-20" />
                  <p className="text-sm font-medium">All clear!</p>
                  <p className="text-[10px] text-slate-300 mt-1">No notifications match this filter.</p>
                </div>
              ) : (
                <div className="divide-y divide-slate-50">
                  {filtered.map((n) => (
                    <motion.div
                      key={n.id} layout
                      className={cn('p-4 flex gap-3 hover:bg-slate-50 transition-colors cursor-pointer group relative', !n.read && 'bg-indigo-50/20')}
                      onClick={() => markAsRead(n.id)}
                    >
                      <div className={cn('w-9 h-9 rounded-xl flex items-center justify-center shrink-0 shadow-sm', !n.read ? 'bg-white' : 'bg-slate-50')}>
                        {getIcon(n.type, n.priority || '')}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-0.5">
                          <p className={cn('text-sm truncate pr-4', n.read ? 'font-medium text-slate-700' : 'font-bold text-slate-900')}>
                            {n.title}
                          </p>
                          <span className="text-[9px] text-slate-400 whitespace-nowrap shrink-0">
                            {n.createdAt ? formatTime(new Date(n.createdAt), language) : 'Now'}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">{n.message}</p>
                        <div className="flex items-center gap-2 mt-1.5">
                          {n.priority === 'stat' && <Badge variant="danger" className="text-[8px]">CRITICAL</Badge>}
                          {n.type === 'lab_result_ready' && <Badge variant="success" className="text-[8px]">READY</Badge>}
                          {n.type === 'inventory_low' && <Badge variant="warning" className="text-[8px]">LOW</Badge>}
                        </div>
                      </div>
                      <div className="absolute right-3 top-1/2 -translate-y-1/2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button className="p-1 text-slate-400 hover:text-indigo-600 rounded" title="Snooze">
                          <Clock size={12} />
                        </button>
                        <button className="p-1 text-slate-400 hover:text-red-500 rounded" title="Dismiss">
                          <X size={12} />
                        </button>
                      </div>
                      {!n.read && <div className="absolute left-2 top-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-indigo-600 rounded-full" />}
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
            {/* Footer */}
            <div className="p-3 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
              <button className="text-[10px] font-black text-indigo-600 hover:text-indigo-700 uppercase tracking-widest transition-all">
                View All History
              </button>
              <span className="text-[9px] text-slate-400">
                {unreadCount} unread
              </span>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};