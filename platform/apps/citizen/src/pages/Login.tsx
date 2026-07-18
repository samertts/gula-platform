import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button, Input, cn } from '@gula/ui-platform';
import { useAuth } from '../contexts/AuthContext';
import { loginWithPhone, loginWithNationalId, verifyOTP } from '../services/auth';
import { validatePhone, validateIraqiNationalId, validateOTP } from '../utils/validation';
import { ROUTES } from '../utils/routes';

type LoginMethod = 'national_id' | 'phone' | 'email';

export function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [method, setMethod] = useState<LoginMethod>('national_id');
  const [nationalId, setNationalId] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [verificationId, setVerificationId] = useState('');
  const [step, setStep] = useState<'input' | 'otp'>('input');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSendOTP() {
    setError('');
    if (method === 'national_id') {
      const validation = validateIraqiNationalId(nationalId);
      if (!validation.valid) { setError(validation.error || ''); return; }
    } else if (method === 'phone') {
      const validation = validatePhone(phone);
      if (!validation.valid) { setError(validation.error || ''); return; }
    }

    setIsLoading(true);
    try {
      const identifier = method === 'national_id' ? nationalId : phone;
      const response = await loginWithPhone(identifier);
      setVerificationId(response.verificationId);
      setStep('otp');
    } catch (err) {
      setError((err as Error).message || 'فشل إرسال رمز التحقق');
    } finally {
      setIsLoading(false);
    }
  }

  async function handleVerifyOTP() {
    setError('');
    const validation = validateOTP(otp);
    if (!validation.valid) { setError(validation.error || ''); return; }

    setIsLoading(true);
    try {
      const response = await verifyOTP(verificationId, otp);
      login(response.user);
      navigate(ROUTES.HOME, { replace: true });
    } catch (err) {
      setError((err as Error).message || 'رمز التحقق غير صحيح');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white dark:from-neutral-900 dark:to-neutral-950 flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-xl shadow-primary-200 dark:shadow-primary-900/30">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-50">تسجيل الدخول</h1>
          <p className="text-sm text-neutral-500 mt-1">السجل الصحي الوطني GULA</p>
        </div>

        {step === 'input' ? (
          <>
            <div className="flex gap-2 mb-6">
              {[
                { key: 'national_id' as const, label: 'رقم وطني' },
                { key: 'phone' as const, label: 'هاتف' },
                { key: 'email' as const, label: 'بريد' },
              ].map((m) => (
                <button
                  key={m.key}
                  onClick={() => { setMethod(m.key); setError(''); }}
                  className={cn(
                    'flex-1 py-2.5 rounded-xl text-xs font-bold transition-all',
                    method === m.key
                      ? 'bg-primary-500 text-white shadow-lg shadow-primary-200 dark:shadow-primary-900/30'
                      : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-500 dark:text-neutral-400',
                  )}
                >
                  {m.label}
                </button>
              ))}
            </div>

            {method === 'national_id' && (
              <Input
                label="الرقم الوطني"
                placeholder="أدخل الرقم الوطني (14 رقم)"
                value={nationalId}
                onChange={(e) => setNationalId(e.target.value.replace(/\D/g, '').slice(0, 14))}
                inputSize="lg"
                error={error}
                maxLength={14}
                inputMode="numeric"
              />
            )}
            {method === 'phone' && (
              <Input
                label="رقم الهاتف"
                placeholder="07XX XXX XXXX"
                value={phone}
                onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 11))}
                inputSize="lg"
                error={error}
                maxLength={11}
                inputMode="tel"
              />
            )}
            {method === 'email' && (
              <Input
                label="البريد الإلكتروني"
                placeholder="example@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                inputSize="lg"
                error={error}
                inputMode="email"
              />
            )}

            <Button
              fullWidth
              size="lg"
              className="mt-6"
              loading={isLoading}
              onClick={handleSendOTP}
            >
              إرسال رمز التحقق
            </Button>
          </>
        ) : (
          <>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 text-center mb-6">
              تم إرسال رمز التحقق إلى {method === 'national_id' ? nationalId : phone}
            </p>
            <div className="mb-4">
              <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">
                رمز التحقق
              </label>
              <div className="flex justify-center gap-2">
                {Array.from({ length: 6 }).map((_, i) => (
                  <input
                    key={i}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={otp[i] || ''}
                    onChange={(e) => {
                      const val = e.target.value.replace(/\D/g, '');
                      const newOtp = otp.split('');
                      newOtp[i] = val;
                      setOtp(newOtp.join('').slice(0, 6));
                      if (val && i < 5) {
                        const next = document.querySelector(`input[name="otp-${i + 1}"]`) as HTMLInputElement;
                        next?.focus();
                      }
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Backspace' && !otp[i] && i > 0) {
                        const prev = document.querySelector(`input[name="otp-${i - 1}"]`) as HTMLInputElement;
                        prev?.focus();
                      }
                    }}
                    name={`otp-${i}`}
                    className="w-12 h-14 text-center text-xl font-black bg-white dark:bg-neutral-800 border-2 border-neutral-300 dark:border-neutral-600 rounded-xl focus:border-primary-500 focus:ring-4 focus:ring-primary-100 dark:focus:ring-primary-900/30 outline-none transition-all"
                  />
                ))}
              </div>
              {error && <p className="text-sm text-danger-600 mt-2 text-center">{error}</p>}
            </div>
            <Button
              fullWidth
              size="lg"
              loading={isLoading}
              onClick={handleVerifyOTP}
              disabled={otp.length < 6}
            >
              تحقق
            </Button>
            <button
              onClick={() => setStep('input')}
              className="w-full text-center text-sm text-primary-600 dark:text-primary-400 font-bold mt-4"
            >
              تغيير طريقة تسجيل الدخول
            </button>
          </>
        )}

        <div className="text-center mt-8">
          <p className="text-xs text-neutral-500">
            ليس لديك حساب؟{' '}
            <Link to={ROUTES.REGISTER} className="text-primary-600 dark:text-primary-400 font-bold">
              إنشاء حساب جديد
            </Link>
          </p>
        </div>

        <div className="mt-8 text-center">
          <p className="text-[10px] text-neutral-400 leading-relaxed">
            بتسجيل الدخول، أنت توافق على{' '}
            <span className="underline">شروط الخدمة</span> و{' '}
            <span className="underline">سياسة الخصوصية</span>
          </p>
        </div>
      </div>
    </div>
  );
}
