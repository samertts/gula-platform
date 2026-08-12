import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { cn } from '@gula/ui-platform';
import { useLab } from '@/contexts/LabContext';
import { ROUTES } from '@/utils/routes';

export function Login() {
  const navigate = useNavigate();
  const { login, isLoading } = useLab();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('يرجى إدخال البريد الإلكتروني وكلمة المرور');
      return;
    }

    try {
      await login(email, password);
      navigate(ROUTES.DASHBOARD, { replace: true });
    } catch (err) {
      setError((err as Error).message || 'فشل تسجيل الدخول. يرجى التحقق من بيانات الدخول.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-primary-50 dark:from-neutral-950 dark:via-neutral-900 dark:to-neutral-950 p-4">
      <div className="w-full max-w-md">
        <div className="bg-white dark:bg-neutral-800 rounded-3xl shadow-2xl shadow-primary-500/10 border border-neutral-200 dark:border-neutral-700 p-8 sm:p-12">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-primary-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary-200 dark:shadow-primary-900">
              <span className="text-white font-black text-2xl">G</span>
            </div>
            <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">
              GULA مختبر
            </h1>
            <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
              نظام إدارة معلومات المختبرات
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <label htmlFor="email" className="block text-xs font-bold text-neutral-600 dark:text-neutral-400">
                البريد الإلكتروني
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="name@lab.example.com"
                dir="ltr"
                autoComplete="email"
                autoFocus
                className="w-full px-4 py-3.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-2xl text-sm font-medium text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 dark:focus:border-primary-400 focus:outline-none transition-colors"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="block text-xs font-bold text-neutral-600 dark:text-neutral-400">
                كلمة المرور
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  className="w-full px-4 py-3.5 pl-12 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-2xl text-sm font-medium text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 dark:focus:border-primary-400 focus:outline-none transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 transition-colors"
                >
                  {showPassword ? (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                      <line x1="1" y1="1" x2="23" y2="23" />
                    </svg>
                  ) : (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {error && (
              <div className="px-4 py-3 bg-danger-50 dark:bg-danger-900/30 border border-danger-200 dark:border-danger-700 rounded-2xl text-sm text-danger-600 dark:text-danger-400 font-medium">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className={cn(
                'w-full py-3.5 bg-primary-500 text-white rounded-2xl font-bold text-sm hover:bg-primary-600 active:bg-primary-700 transition-colors',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'focus:outline-none focus-visible:ring-4 focus-visible:ring-primary-200 dark:focus-visible:ring-primary-800',
              )}
            >
              {isLoading ? (
                <span className="inline-flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  جاري تسجيل الدخول...
                </span>
              ) : (
                'تسجيل الدخول'
              )}
            </button>

            <div className="text-center">
              <button
                type="button"
                className="text-xs font-medium text-primary-500 hover:text-primary-600 transition-colors"
              >
                نسيت كلمة المرور؟
              </button>
            </div>
          </form>

          <div className="mt-8 pt-6 border-t border-neutral-100 dark:border-neutral-700">
            <p className="text-[10px] text-center text-neutral-400 dark:text-neutral-500 leading-relaxed">
              هذا النظام مخصص لموظفي المختبر المعتمدين فقط.
              <br />
              جميع الإجراءات مسجلة في سجل التدقيق.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
