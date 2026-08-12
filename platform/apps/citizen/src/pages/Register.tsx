import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button, Input, Select, cn } from '@gula/ui-platform';
import { useAuth } from '../contexts/AuthContext';
import { registerCitizen, loginWithPhone, verifyOTP } from '../services/auth';
import { validateIraqiNationalId, validatePhone, validateName, validateDateOfBirth } from '../utils/validation';
import { ROUTES } from '../utils/routes';
import { GENDERS } from '../utils/constants';

export function Register() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [step, setStep] = useState<'info' | 'otp'>('info');
  const [nationalId, setNationalId] = useState('');
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [gender, setGender] = useState('');
  const [otp, setOtp] = useState('');
  const [verificationId, setVerificationId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmitInfo() {
    setError('');
    const idValidation = validateIraqiNationalId(nationalId);
    if (!idValidation.valid) { setError(idValidation.error || ''); return; }
    const nameValidation = validateName(name);
    if (!nameValidation.valid) { setError(nameValidation.error || ''); return; }
    const phoneValidation = validatePhone(phone);
    if (!phoneValidation.valid) { setError(phoneValidation.error || ''); return; }
    const dobValidation = validateDateOfBirth(dateOfBirth);
    if (!dobValidation.valid) { setError(dobValidation.error || ''); return; }
    if (!gender) { setError('الرجاء اختيار الجنس'); return; }

    setIsLoading(true);
    try {
      const response = await loginWithPhone(phone);
      setVerificationId(response.verificationId);
      setStep('otp');
    } catch (err) {
      setError((err as Error).message || 'فشل إرسال رمز التحقق');
    } finally {
      setIsLoading(false);
    }
  }

  async function handleVerify() {
    setError('');
    setIsLoading(true);
    try {
      await verifyOTP(verificationId, otp);
      const user = await registerCitizen({
        nationalId,
        name,
        phone,
        email: email || undefined,
        dateOfBirth,
        gender: gender as 'male' | 'female',
      });
      login(user.user);
      navigate(ROUTES.HOME, { replace: true });
    } catch (err) {
      setError((err as Error).message || 'فشل التسجيل');
    } finally {
      setIsLoading(false);
    }
  }

  const genderOptions = GENDERS.map((g) => ({
    value: g.key,
    label: g.label,
  }));

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white dark:from-neutral-900 dark:to-neutral-950 flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-xl shadow-primary-200 dark:shadow-primary-900/30">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          </div>
          <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-50">إنشاء حساب جديد</h1>
          <p className="text-sm text-neutral-500 mt-1">السجل الصحي الوطني GULA</p>
        </div>

        {step === 'info' ? (
          <>
            <div className="space-y-4">
              <Input
                label="الرقم الوطني"
                placeholder="أدخل الرقم الوطني (14 رقم)"
                value={nationalId}
                onChange={(e) => setNationalId(e.target.value.replace(/\D/g, '').slice(0, 14))}
                inputSize="lg"
                inputMode="numeric"
              />
              <Input
                label="الاسم الكامل"
                placeholder="الاسم الثلاثي"
                value={name}
                onChange={(e) => setName(e.target.value)}
                inputSize="lg"
              />
              <Input
                label="رقم الهاتف"
                placeholder="07XX XXX XXXX"
                value={phone}
                onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 11))}
                inputSize="lg"
                inputMode="tel"
              />
              <Input
                label="البريد الإلكتروني (اختياري)"
                placeholder="example@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                inputSize="lg"
                inputMode="email"
              />
              <Input
                label="تاريخ الميلاد"
                type="date"
                value={dateOfBirth}
                onChange={(e) => setDateOfBirth(e.target.value)}
                inputSize="lg"
              />
              <Select
                label="الجنس"
                options={genderOptions}
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                placeholder="اختر الجنس"
              />
            </div>
            {error && <p className="text-sm text-danger-600 mt-2">{error}</p>}
            <Button fullWidth size="lg" className="mt-6" loading={isLoading} onClick={handleSubmitInfo}>
              تسجيل
            </Button>
          </>
        ) : (
          <>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 text-center mb-6">
              تم إرسال رمز التحقق إلى {phone}
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
                        const next = document.querySelector(`input[name="reg-otp-${i + 1}"]`) as HTMLInputElement;
                        next?.focus();
                      }
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Backspace' && !otp[i] && i > 0) {
                        const prev = document.querySelector(`input[name="reg-otp-${i - 1}"]`) as HTMLInputElement;
                        prev?.focus();
                      }
                    }}
                    name={`reg-otp-${i}`}
                    className="w-12 h-14 text-center text-xl font-black bg-white dark:bg-neutral-800 border-2 border-neutral-300 dark:border-neutral-600 rounded-xl focus:border-primary-500 focus:ring-4 focus:ring-primary-100 dark:focus:ring-primary-900/30 outline-none transition-all"
                  />
                ))}
              </div>
              {error && <p className="text-sm text-danger-600 mt-2 text-center">{error}</p>}
            </div>
            <Button fullWidth size="lg" loading={isLoading} onClick={handleVerify} disabled={otp.length < 6}>
              تأكيد وإنشاء الحساب
            </Button>
          </>
        )}

        <div className="text-center mt-8">
          <p className="text-xs text-neutral-500">
            لديك حساب بالفعل؟{' '}
            <Link to={ROUTES.LOGIN} className="text-primary-600 dark:text-primary-400 font-bold">
              تسجيل الدخول
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
