import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardBody, Input, Button, Alert } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import { useAuth } from '../contexts/AuthContext';

export function Login() {
  const { isRtl } = useRTL();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await new Promise(r => setTimeout(r, 1000));
      if (email && password) {
        login('mock-token', 'mock-refresh', {
          id: 'h1',
          name: 'Ali Al-Hakim',
          nameAr: 'علي الحكيم',
          email: 'admin@gula.health',
          title: 'Hospital Director',
          titleAr: 'مدير المستشفى',
          department: 'Administration',
          departmentAr: 'الإدارة',
          hospitalId: 'hosp1',
          role: 'director',
          permissions: ['read', 'write', 'admin', 'finance', 'hr', 'manage_staff'],
        });
        navigate('/dashboard');
      } else {
        setError(isRtl ? 'الرجاء إدخال البريد الإلكتروني وكلمة المرور' : 'Please enter email and password');
      }
    } catch {
      setError(isRtl ? 'فشل تسجيل الدخول' : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-primary-950 via-neutral-950 to-primary-900">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-primary-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary-200 dark:shadow-primary-900/30">
            <span className="text-white font-bold text-2xl">G</span>
          </div>
          <h1 className="text-2xl font-bold text-neutral-50">GULA مستشفى</h1>
          <p className="text-sm text-neutral-400 mt-1">
            {isRtl ? 'نظام إدارة المستشفيات الوطني' : 'National Hospital Administration'}
          </p>
        </div>

        <Card variant="elevated" padding="lg">
          <CardHeader
            title={isRtl ? 'تسجيل الدخول' : 'Sign In'}
            subtitle={isRtl ? 'منصة إدارة المستشفيات الوطنية' : 'National Hospital Management Platform'}
          />
          <CardBody>
            {error && (
              <Alert variant="danger" className="mb-4">
                {error}
              </Alert>
            )}

            <form onSubmit={handleLogin} className="space-y-4">
              <Input
                label={isRtl ? 'البريد الإلكتروني' : 'Email'}
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="admin@hospital.gula"
                required
                autoComplete="email"
              />
              <Input
                label={isRtl ? 'كلمة المرور' : 'Password'}
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                autoComplete="current-password"
              />
              <div className="flex items-center justify-between text-sm">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="rounded border-neutral-300 dark:border-neutral-600" />
                  <span className="text-neutral-600 dark:text-neutral-400">{isRtl ? 'تذكرني' : 'Remember me'}</span>
                </label>
                <button type="button" className="text-primary-600 dark:text-primary-400 hover:underline">
                  {isRtl ? 'نسيت كلمة المرور؟' : 'Forgot password?'}
                </button>
              </div>
              <Button type="submit" fullWidth loading={isLoading}>
                {isRtl ? 'تسجيل الدخول' : 'Sign In'}
              </Button>
            </form>
          </CardBody>
        </Card>

        <p className="text-center text-xs text-neutral-500 mt-6">
          {isRtl ? 'للاستخدام الإداري والطبي المصرح به فقط' : 'Authorized administrative and medical use only'}
          <br />
          &copy; 2024 GULA Health. {isRtl ? 'جميع الحقوق محفوظة' : 'All rights reserved.'}
        </p>
      </div>
    </div>
  );
}
