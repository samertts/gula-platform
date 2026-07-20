import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import {
  Menu, Bell, Search, Moon, Sun, LogOut, User, Settings,
  Globe, ChevronDown,
} from 'lucide-react';

interface TopBarProps {
  onMenuToggle: () => void;
  onSearchToggle: () => void;
}

export function TopBar({ onMenuToggle, onSearchToggle }: TopBarProps) {
  const { t, i18n } = useTranslation();
  const { user, lab, logout } = useAuth();
  const navigate = useNavigate();
  const [showProfile, setShowProfile] = useState(false);
  const [showLang, setShowLang] = useState(false);
  const [dark, setDark] = useState(false);

  const isRtl = i18n.language === 'ar';

  const toggleLang = () => {
    const newLang = i18n.language === 'ar' ? 'en' : 'ar';
    i18n.changeLanguage(newLang);
    localStorage.setItem('language', newLang);
    document.documentElement.dir = newLang === 'ar' ? 'rtl' : 'ltr';
    setShowLang(false);
  };

  const toggleTheme = () => {
    setDark(!dark);
    document.documentElement.classList.toggle('dark');
  };

  return (
    <header className={cn(
      'fixed top-0 right-0 left-0 h-16 z-20 flex items-center justify-between px-4 bg-surface/80 backdrop-blur-md border-b border-outline',
      isRtl ? 'lg:pr-64' : 'lg:pl-64'
    )}>
      <div className="flex items-center gap-3">
        <button onClick={onMenuToggle} className="p-2 rounded-lg hover:bg-surface-container-high lg:hidden">
          <Menu className="h-5 w-5" />
        </button>
        <button onClick={onSearchToggle} className="p-2 rounded-lg hover:bg-surface-container-high">
          <Search className="h-5 w-5" />
        </button>
      </div>

      <div className="flex items-center gap-2">
        <button onClick={toggleLang} className="relative p-2 rounded-lg hover:bg-surface-container-high" onMouseEnter={() => setShowLang(true)} onMouseLeave={() => setShowLang(false)}>
          <Globe className="h-5 w-5" />
          {showLang && (
            <div className="absolute top-full mt-1 right-0 bg-surface border border-outline rounded-lg shadow-lg py-1 min-w-[120px] z-50">
              <button className="w-full px-3 py-1.5 text-sm text-left hover:bg-surface-container-high" onClick={toggleLang}>
                {i18n.language === 'ar' ? 'English' : 'العربية'}
              </button>
            </div>
          )}
        </button>

        <button onClick={toggleTheme} className="p-2 rounded-lg hover:bg-surface-container-high">
          {dark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </button>

        <button className="relative p-2 rounded-lg hover:bg-surface-container-high">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-error" />
        </button>

        <div className="relative">
          <button
            onClick={() => setShowProfile(!showProfile)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-surface-container-high"
          >
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
              <span className="text-sm font-medium text-primary">
                {user?.name?.charAt(0)?.toUpperCase() || 'U'}
              </span>
            </div>
            <div className="hidden md:block text-left">
              <p className="text-sm font-medium text-on-surface leading-tight">{user?.name}</p>
              <p className="text-xs text-on-surface-variant leading-tight">{lab?.name}</p>
            </div>
            <ChevronDown className="h-4 w-4 text-on-surface-variant hidden md:block" />
          </button>
          {showProfile && (
            <div className={cn(
              'absolute top-full mt-1 bg-surface border border-outline rounded-lg shadow-lg py-1 min-w-[180px] z-50',
              isRtl ? 'left-0' : 'right-0'
            )}>
              <button
                onClick={() => { setShowProfile(false); navigate('/profile'); }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-surface-container-high"
              >
                <User className="h-4 w-4" /> {t('profile')}
              </button>
              <button
                onClick={() => { setShowProfile(false); navigate('/settings'); }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-surface-container-high"
              >
                <Settings className="h-4 w-4" /> {t('settings')}
              </button>
              <hr className="my-1 border-outline" />
              <button
                onClick={() => { setShowProfile(false); logout(); }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-error hover:bg-error-container"
              >
                <LogOut className="h-4 w-4" /> {t('signOut')}
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
