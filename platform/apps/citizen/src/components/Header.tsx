import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useNotifications } from '../contexts/NotificationContext';
import { useOffline } from '../contexts/OfflineContext';
import { ARABIC_NAMES } from '../utils/routes';
import { ROUTES } from '../utils/routes';

export function Header() {
  const { user } = useAuth();
  const { unreadCount } = useNotifications();
  const { isOnline } = useOffline();
  const location = useLocation();

  const pageName = ARABIC_NAMES[location.pathname] || 'GULA';

  return (
    <header className="sticky top-0 z-40 bg-white/80 dark:bg-neutral-900/80 backdrop-blur-xl border-b border-neutral-200/50 dark:border-neutral-700/50">
      <div className="flex items-center justify-between h-14 px-4 max-w-lg mx-auto">
        <div className="flex items-center gap-3 min-w-0">
          {location.pathname !== ROUTES.HOME && (
            <button
              onClick={() => window.history.back()}
              className="shrink-0 w-9 h-9 flex items-center justify-center rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-600 dark:text-neutral-400"
              aria-label="الرجوع"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
          )}
          <h1 className="text-base font-black text-neutral-900 dark:text-neutral-50 truncate">
            {pageName}
          </h1>
        </div>

        <div className="flex items-center gap-2">
          {!isOnline && (
            <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" title="غير متصل" />
          )}

          <Link
            to={ROUTES.NOTIFICATIONS}
            className="relative w-9 h-9 flex items-center justify-center rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-600 dark:text-neutral-400"
            aria-label="الإشعارات"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -end-0.5 bg-danger-500 text-white text-[9px] font-bold min-w-[18px] h-[18px] flex items-center justify-center rounded-full px-1 shadow-lg">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </Link>

          <Link
            to={ROUTES.PROFILE}
            className="w-9 h-9 flex items-center justify-center rounded-xl bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 font-black text-sm"
            aria-label="الملف الشخصي"
          >
            {user?.name?.charAt(0) || 'U'}
          </Link>
        </div>
      </div>
    </header>
  );
}
