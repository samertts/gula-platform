import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { auth, me } from '@/api/endpoints';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
import { Settings, Shield, Bell, Globe, Moon, Sun } from 'lucide-react';

export function SettingsPage() {
  const { t, i18n } = useTranslation();
  const { user, lab } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [dark, setDark] = useState(false);

  const changePasswordMutation = useMutation({
    mutationFn: () => auth.changePassword(currentPassword, newPassword),
    onSuccess: () => {
      toast.success(t('success'));
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    },
    onError: (err: any) => toast.error(err.message),
  });

  const toggleTheme = () => {
    setDark(!dark);
    document.documentElement.classList.toggle('dark');
  };

  const toggleLang = () => {
    const newLang = i18n.language === 'ar' ? 'en' : 'ar';
    i18n.changeLanguage(newLang);
    localStorage.setItem('language', newLang);
    document.documentElement.dir = newLang === 'ar' ? 'rtl' : 'ltr';
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-on-surface">{t('settings')}</h1>
        <p className="text-on-surface-variant mt-1">{t('profileAndSettings')}</p>
      </div>

      <div className="rounded-xl border border-outline bg-surface overflow-hidden">
        <div className="px-6 py-4 border-b border-outline flex items-center gap-2">
          <Settings className="h-5 w-5" />
          <h3 className="font-semibold text-on-surface">{t('profile')}</h3>
        </div>
        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-on-surface-variant">{t('fullName')}</label>
              <p className="text-sm font-medium text-on-surface">{user?.name}</p>
            </div>
            <div>
              <label className="text-sm text-on-surface-variant">{t('email')}</label>
              <p className="text-sm font-medium text-on-surface">{user?.email}</p>
            </div>
            <div>
              <label className="text-sm text-on-surface-variant">{t('role')}</label>
              <p className="text-sm font-medium text-on-surface">{user?.role}</p>
            </div>
            <div>
              <label className="text-sm text-on-surface-variant">{t('labName')}</label>
              <p className="text-sm font-medium text-on-surface">{lab?.name}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-outline bg-surface overflow-hidden">
        <div className="px-6 py-4 border-b border-outline flex items-center gap-2">
          <Shield className="h-5 w-5" />
          <h3 className="font-semibold text-on-surface">{t('changePassword')}</h3>
        </div>
        <div className="p-6 space-y-4">
          <Input
            label={t('currentPassword')}
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label={t('newPassword')}
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
            <Input
              label={t('confirmPassword')}
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </div>
          <Button
            onClick={() => changePasswordMutation.mutate()}
            isLoading={changePasswordMutation.isPending}
            disabled={!currentPassword || !newPassword || newPassword !== confirmPassword}
          >
            {t('changePassword')}
          </Button>
        </div>
      </div>

      <div className="rounded-xl border border-outline bg-surface overflow-hidden">
        <div className="px-6 py-4 border-b border-outline flex items-center gap-2">
          <Globe className="h-5 w-5" />
          <h3 className="font-semibold text-on-surface">{t('language')} & {t('theme')}</h3>
        </div>
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-on-surface">{t('language')}</p>
              <p className="text-xs text-on-surface-variant">{i18n.language === 'ar' ? 'العربية' : 'English'}</p>
            </div>
            <Button variant="outline" size="sm" onClick={toggleLang}>
              <Globe className="h-4 w-4" />
              {i18n.language === 'ar' ? 'English' : 'العربية'}
            </Button>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-on-surface">{t('theme')}</p>
              <p className="text-xs text-on-surface-variant">{dark ? t('darkMode') : t('lightMode')}</p>
            </div>
            <Button variant="outline" size="sm" onClick={toggleTheme}>
              {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              {dark ? t('lightMode') : t('darkMode')}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
