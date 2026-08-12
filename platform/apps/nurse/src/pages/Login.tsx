import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { cn } from '@gula/ui-platform';
import { useNurse } from '@/contexts/NurseContext';
import { ROUTES } from '@/utils/routes';

function Login() {
  const navigate = useNavigate();
  const { login, isLoading } = useNurse();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError('يرجى إدخال البريد الإلكتروني وكلمة المرور');
      return;
    }
    setError('');
    try {
      await login(email, password);
      navigate(ROUTES.DASHBOARD, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل تسجيل الدخول');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 dark:from-neutral-950 dark:via-neutral-900 dark:to-neutral-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-20 h-20 bg-primary-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary-500/30">
            <svg className="w-10 h-10 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">نظام التمريض السريري</h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">GULA National Nursing Application</p>
        </div>

        <div className="bg-white dark:bg-neutral-800 rounded-3xl p-8 shadow-xl border border-neutral-200 dark:border-neutral-700">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-2">
                البريد الإلكتروني
              </label>
              <input
                type="email"
                value={email}
                onChange={e => { setEmail(e.target.value); setError(''); }}
                placeholder="nurse@hospital.com"
                className="w-full px-4 py-3 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-2xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none transition-colors"
                autoFocus
                dir="ltr"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-2">
                كلمة المرور
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={e => { setPassword(e.target.value); setError(''); }}
                  placeholder="••••••••"
                  className="w-full px-4 py-3 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-2xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none transition-colors"
                  dir="ltr"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300"
                >
                  {showPassword ? (
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L3 3" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {error && (
              <div className="bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 p-3 rounded-2xl">
                <p className="text-xs text-danger-600 dark:text-danger-400 font-bold flex items-center gap-2">
                  <svg className="w-4 h-4 shrink-0" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" />
                  </svg>
                  {error}
                </p>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className={cn(
                'w-full py-3.5 bg-primary-500 text-white rounded-2xl font-bold text-sm transition-all',
                'hover:bg-primary-600 active:bg-primary-700',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'shadow-lg shadow-primary-500/20 hover:shadow-primary-500/30',
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
          </form>
        </div>

        <p className="text-center text-xs text-neutral-400 dark:text-neutral-600 mt-6">
          GULA Platform v2.1.0 — نظام إدارة التمريض
        </p>
      </div>
    </div>
  );
}

export default Login;
