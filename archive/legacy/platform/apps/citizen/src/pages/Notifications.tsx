import { cn } from '@gula/ui-platform';
import { useNotifications } from '../contexts/NotificationContext';

const typeIcons: Record<string, string> = {
  lab_result: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z',
  appointment: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
  medication: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
  consent: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z',
  emergency: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z',
  system: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z',
  family: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
};

const typeColors: Record<string, string> = {
  lab_result: 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400',
  appointment: 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400',
  medication: 'bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400',
  consent: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400',
  emergency: 'bg-danger-100 text-danger-600 dark:bg-danger-900/30 dark:text-danger-400',
  system: 'bg-neutral-100 text-neutral-600 dark:bg-neutral-900/30 dark:text-neutral-400',
  family: 'bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400',
};

export function Notifications() {
  const { notifications, unreadCount, isLoading, markAsRead, markAllAsRead } = useNotifications();

  return (
    <div className="pb-24 px-4 pt-4">
      <div className="flex items-center justify-between mb-6">
        <p className="text-xs text-neutral-500">
          {unreadCount > 0 ? `${unreadCount} إشعارات غير مقروءة` : 'جميع الإشعارات مقروءة'}
        </p>
        {unreadCount > 0 && (
          <button
            onClick={markAllAsRead}
            className="text-xs font-bold text-primary-600 dark:text-primary-400"
          >
            تحديد الكل كمقروء
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-neutral-100 dark:bg-neutral-800 rounded-2xl h-20 animate-pulse" />
          ))}
        </div>
      ) : notifications.length === 0 ? (
        <div className="text-center py-16">
          <svg className="w-16 h-16 mx-auto text-neutral-300 dark:text-neutral-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <p className="text-sm text-neutral-500 mb-2">لا توجد إشعارات</p>
          <p className="text-[10px] text-neutral-400">ستظهر الإشعارات هنا عند ورودها</p>
        </div>
      ) : (
        <div className="space-y-3">
          {notifications.map((notification) => (
            <button
              key={notification.id}
              onClick={() => !notification.read && markAsRead(notification.id)}
              className={cn(
                'w-full text-right bg-white dark:bg-neutral-800 rounded-2xl p-4 border transition-all',
                notification.read
                  ? 'border-neutral-200 dark:border-neutral-700'
                  : 'border-primary-200 dark:border-primary-800 shadow-sm',
              )}
            >
              <div className="flex items-start gap-3">
                <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center shrink-0', typeColors[notification.type] || 'bg-neutral-100 text-neutral-500')}>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={typeIcons[notification.type] || typeIcons.system} />
                  </svg>
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className={cn('text-sm truncate', notification.read ? 'font-medium text-neutral-600 dark:text-neutral-400' : 'font-bold text-neutral-900 dark:text-neutral-50')}>
                      {notification.title}
                    </h4>
                    {!notification.read && (
                      <div className="w-2 h-2 rounded-full bg-primary-500 shrink-0" />
                    )}
                  </div>
                  <p className={cn('text-xs mt-0.5', notification.read ? 'text-neutral-400' : 'text-neutral-500')}>
                    {notification.body}
                  </p>
                  <p className="text-[10px] text-neutral-400 mt-1">
                    {new Date(notification.createdAt).toLocaleDateString('ar-IQ', { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
