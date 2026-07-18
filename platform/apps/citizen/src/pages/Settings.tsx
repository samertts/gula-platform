import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, cn } from '@gula/ui-platform';
import { useAuth } from '../contexts/AuthContext';
import { useOffline } from '../contexts/OfflineContext';
import { clearAllCachedData, getCacheSize } from '../services/offline';
import { requestPermission } from '../services/notifications';
import { ROUTES } from '../utils/routes';

interface SettingRowProps {
  label: string;
  description?: string;
  action?: React.ReactNode;
  onClick?: () => void;
  danger?: boolean;
}

function SettingRow({ label, description, action, onClick, danger }: SettingRowProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-right flex items-center justify-between p-4 bg-white dark:bg-neutral-800 rounded-2xl border shadow-sm',
        danger ? 'border-danger-200 dark:border-danger-800' : 'border-neutral-200 dark:border-neutral-700',
      )}
    >
      <div className="min-w-0 flex-1">
        <p className={cn('text-sm font-bold', danger ? 'text-danger-600 dark:text-danger-400' : 'text-neutral-900 dark:text-neutral-50')}>
          {label}
        </p>
        {description && <p className="text-[10px] text-neutral-500 mt-0.5">{description}</p>}
      </div>
      {action || (
        <svg className="w-5 h-5 text-neutral-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      )}
    </button>
  );
}

export function Settings() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { isOnline } = useOffline();
  const [notifPermission, setNotifPermission] = useState<NotificationPermission>('default');
  const [cacheSize, setCacheSize] = useState('');

  useEffect(() => {
    if ('Notification' in window) {
      setNotifPermission(Notification.permission);
    }
    getCacheSize().then(setCacheSize);
  }, []);

  async function handleNotificationPermission() {
    const result = await requestPermission();
    setNotifPermission(result);
  }

  async function handleClearCache() {
    await clearAllCachedData();
    const size = await getCacheSize();
    setCacheSize(size);
  }

  function handleLanguageToggle() {
    const current = document.documentElement.lang;
    const newLang = current === 'ar' ? 'en' : 'ar';
    document.documentElement.lang = newLang;
    document.documentElement.dir = newLang === 'ar' ? 'rtl' : 'ltr';
    localStorage.setItem('gula-locale', newLang);
    window.location.reload();
  }

  function handleThemeToggle() {
    const isDark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('gula-theme-mode', isDark ? 'dark' : 'light');
  }

  return (
    <div className="pb-24 px-4 pt-4 space-y-4">
      <div className="bg-white dark:bg-neutral-800 rounded-3xl p-6 border border-neutral-200 dark:border-neutral-700 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-primary-50 dark:bg-primary-900/30 flex items-center justify-center text-primary-600 dark:text-primary-400 font-black text-xl">
            {user?.name?.charAt(0) || 'U'}
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="font-black text-neutral-900 dark:text-neutral-50 truncate">{user?.name}</h3>
            <p className="text-xs text-neutral-500">{user?.phone}</p>
            {user?.email && <p className="text-[10px] text-neutral-400">{user.email}</p>}
          </div>
          <button
            onClick={() => navigate(ROUTES.PROFILE)}
            className="shrink-0 px-4 py-2 bg-primary-500 text-white rounded-xl text-xs font-bold"
          >
            تعديل
          </button>
        </div>
      </div>

      <div>
        <p className="text-xs font-bold text-neutral-500 uppercase tracking-widest mb-3 px-1">التفضيلات</p>
        <div className="space-y-3">
          <SettingRow
            label="اللغة"
            description={document.documentElement.lang === 'ar' ? 'العربية' : 'English'}
            onClick={handleLanguageToggle}
          />
          <SettingRow
            label="المظهر"
            description={document.documentElement.classList.contains('dark') ? 'داكن' : 'فاتح'}
            onClick={handleThemeToggle}
          />
          <SettingRow
            label="الإشعارات"
            description={notifPermission === 'granted' ? 'مفعلة' : notifPermission === 'denied' ? 'معطلة' : 'غير مفعلة'}
            onClick={handleNotificationPermission}
          />
        </div>
      </div>

      <div>
        <p className="text-xs font-bold text-neutral-500 uppercase tracking-widest mb-3 px-1">البيانات</p>
        <div className="space-y-3">
          <SettingRow
            label="مسح التخزين المؤقت"
            description={`${cacheSize} - البيانات المحفوظة بدون اتصال`}
            onClick={handleClearCache}
          />
          <SettingRow
            label="المحفظة غير المتصلة"
            description="إدارة البيانات الصحية المتوفرة بدون إنترنت"
            onClick={() => navigate(ROUTES.OFFLINE_WALLET)}
          />
          <SettingRow
            label="بطاقة الطوارئ"
            description="معلومات الطوارئ المتوفرة بدون إنترنت"
            onClick={() => navigate(ROUTES.EMERGENCY_CARD)}
          />
        </div>
      </div>

      <div>
        <p className="text-xs font-bold text-neutral-500 uppercase tracking-widest mb-3 px-1">الحساب</p>
        <div className="space-y-3">
          <SettingRow
            label="إدارة الموافقات"
            description="التحكم في مشاركة البيانات الصحية"
            onClick={() => navigate(ROUTES.CONSENT)}
          />
          <SettingRow
            label="سجل الأمان"
            description="مراجعة نشاطات الدخول والتعديل"
            onClick={() => navigate(ROUTES.SETTINGS)}
          />
          <SettingRow
            label="حذف الحساب"
            description="حذف الحساب وجميع البيانات المرتبطة"
            danger
            onClick={() => {}}
          />
        </div>
      </div>

      <div className="pt-4">
        <Button
          fullWidth
          variant="outline"
          className="border-danger-200 text-danger-600 hover:bg-danger-50"
          onClick={() => {
            logout();
            navigate(ROUTES.LOGIN, { replace: true });
          }}
        >
          تسجيل الخروج
        </Button>
      </div>

      <div className="text-center py-4">
        <p className="text-[10px] text-neutral-400">GULA Health v2.1.0</p>
        <p className="text-[9px] text-neutral-400 mt-0.5">السجل الصحي الوطني</p>
      </div>
    </div>
  );
}
