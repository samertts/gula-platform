import { Outlet } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export function AuthLayout() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/5 via-background to-primary/10 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-primary flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary/20">
            <span className="text-white font-bold text-2xl">G</span>
          </div>
          <h1 className="text-2xl font-bold text-on-surface">{t('appName')}</h1>
        </div>
        <div className="bg-surface rounded-2xl border border-outline shadow-xl p-8">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
