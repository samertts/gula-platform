import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardBody, Input, Button, Alert } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import { useAuth } from '../contexts/AuthContext';

export function Login() {
  const { isRtl } = useRTL();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [step, setStep] = useState<'credentials' | 'mfa'>('credentials');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mfaCode, setMfaCode] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await new Promise(r => setTimeout(r, 1000));
      if (email && password) {
        setStep('mfa');
      } else {
        setError(isRtl ? 'الرجاء إدخال البريد الإلكتروني وكلمة المرور' : 'Please enter email and password');
      }
    } catch {
      setError(isRtl ? 'فشل تسجيل الدخول' : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleMfa = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await new Promise(r => setTimeout(r, 800));
      if (mfaCode.length === 6) {
        login('mock-token', 'mock-refresh', {
          id: 'd1',
          name: 'Ahmed Al-Jubouri',
          nameAr: 'أحمد الجبوري',
          email: 'ahmed@gula.health',
          title: 'Consultant Physician',
          titleAr: 'استشاري باطنية',
          specialization: 'Internal Medicine',
          specializationAr: 'الطب الباطني',
          licenseNumber: 'IQ-MOH-2024-12345',
          labId: 'lab1',
          facilityId: 'fac1',
          department: 'Internal Medicine',
          role: 'consultant',
          permissions: ['read', 'write', 'sign', 'prescribe', 'order_lab', 'order_radiology', 'refer'],
          mfaEnabled: true,
        });
        navigate('/dashboard');
      } else {
        setError(isRtl ? 'رمز التحقق غير صحيح' : 'Invalid verification code');
      }
    } catch {
      setError(isRtl ? 'فشل التحقق' : 'Verification failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-primary-50 to-primary-100 dark:from-neutral-950 dark:to-primary-950">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-primary-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary-200 dark:shadow-primary-900/30">
            <span className="text-white font-bold text-2xl">G</span>
          </div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">GULA طبيب</h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            {isRtl ? 'تطبيق الطبيب الوطني - السجل الصحي العراقي' : 'National Doctor Application - Iraqi Health Record'}
          </p>
        </div>

        <Card variant="elevated" padding="lg">
          <CardHeader
            title={step === 'credentials'
              ? (isRtl ? 'تسجيل الدخول' : 'Sign In')
              : (isRtl ? 'التحقق بخطوتين' : 'Two-Factor Authentication')}
            subtitle={step === 'mfa' ? (isRtl ? 'أدخل رمز التحقق المرسل إلى جهازك' : 'Enter the verification code sent to your device') : undefined}
          />
          <CardBody>
            {error && (
              <Alert variant="danger" className="mb-4">
                {error}
              </Alert>
            )}

            {step === 'credentials' ? (
              <form onSubmit={handleLogin} className="space-y-4">
                <Input
                  label={isRtl ? 'البريد الإلكتروني' : 'Email'}
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="doctor@example.com"
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
            ) : (
              <form onSubmit={handleMfa} className="space-y-4">
                <div className="text-center">
                  <p className="text-sm text-neutral-500 dark:text-neutral-400 mb-4">
                    {isRtl
                      ? 'تم إرسال رمز تحقق مكون من 6 أرقام إلى بريدك الإلكتروني المسجل'
                      : 'A 6-digit verification code was sent to your registered email'}
                  </p>
                  <Input
                    value={mfaCode}
                    onChange={e => setMfaCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    placeholder="000000"
                    maxLength={6}
                    className="text-center text-2xl tracking-widest text-center"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                  />
                </div>
                <Button type="submit" fullWidth loading={isLoading}>
                  {isRtl ? 'تحقق' : 'Verify'}
                </Button>
                <button
                  type="button"
                  onClick={() => setStep('credentials')}
                  className="w-full text-sm text-primary-600 dark:text-primary-400 hover:underline text-center"
                >
                  {isRtl ? 'العودة لتسجيل الدخول' : 'Back to sign in'}
                </button>
              </form>
            )}
          </CardBody>
        </Card>

        <p className="text-center text-xs text-neutral-400 mt-6">
          {isRtl ? 'هذا التطبيق مخصص للاستخدام الطبي المهني فقط' : 'This application is for professional medical use only'}
          <br />
          &copy; 2024 GULA Health. {isRtl ? 'جميع الحقوق محفوظة' : 'All rights reserved.'}
        </p>
      </div>
    </div>
  );
}
