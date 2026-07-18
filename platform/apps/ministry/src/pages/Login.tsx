import { useState } from 'react';
import { motion } from 'motion/react';
import { cn } from '@gula/ui-platform';
import { useNavigate } from 'react-router-dom';
import { Shield, Eye, EyeOff, Loader2, Lock, User } from 'lucide-react';

export function Login() {
  const navigate = useNavigate();
  const [step, setStep] = useState<'credentials' | 'mfa'>('credentials');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    await new Promise(r => setTimeout(r, 800));
    setLoading(false);
    setStep('mfa');
  };

  const handleMfaSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    await new Promise(r => setTimeout(r, 1200));
    localStorage.setItem('gula_ministry_token', 'mock-jwt-token');
    setLoading(false);
    navigate('/dashboard');
  };

  const handleOtpChange = (index: number, value: string) => {
    if (value && !/^\d$/.test(value)) return;
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);
    if (value && index < 5) {
      const next = document.getElementById(`otp-${index + 1}`);
      next?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      const prev = document.getElementById(`otp-${index - 1}`);
      prev?.focus();
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-violet-500/10 rounded-full blur-[120px]" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative w-full max-w-md"
      >
        <div className="text-center mb-10">
          <div className="w-20 h-20 bg-indigo-600 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-2xl shadow-indigo-600/30">
            <Shield size={40} className="text-white" />
          </div>
          <h1 className="text-3xl font-black text-white mb-2">GULA وزارة</h1>
          <p className="text-sm text-slate-400">منصة الرقابة الصحية الوطنية</p>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-3xl p-8 backdrop-blur-xl">
          {step === 'credentials' ? (
            <form onSubmit={handleCredentialsSubmit} className="space-y-6">
              <div>
                <label className="block text-xs font-bold text-slate-400 mb-2">البريد الإلكتروني</label>
                <div className="relative">
                  <User size={18} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder="minister@health.gov.iq"
                    className="w-full pr-12 pl-4 py-3.5 bg-white/5 border border-white/10 rounded-2xl text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500/50 focus:ring-2 focus:ring-indigo-500/20 transition-all"
                    required
                    dir="ltr"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-400 mb-2">كلمة المرور</label>
                <div className="relative">
                  <Lock size={18} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    className="w-full pr-12 pl-12 py-3.5 bg-white/5 border border-white/10 rounded-2xl text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500/50 focus:ring-2 focus:ring-indigo-500/20 transition-all"
                    required
                    dir="ltr"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              {error && <p className="text-xs text-rose-400 font-medium">{error}</p>}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-2xl font-bold text-sm transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading && <Loader2 size={18} className="animate-spin" />}
                تسجيل الدخول
              </button>

              <p className="text-center text-[10px] text-slate-500 mt-4">
                بيئة آمنة وحساسة - دخول مصرح به فقط
              </p>
            </form>
          ) : (
            <form onSubmit={handleMfaSubmit} className="space-y-6">
              <div className="text-center mb-6">
                <div className="w-14 h-14 bg-indigo-600/20 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-indigo-500/30">
                  <Shield size={28} className="text-indigo-400" />
                </div>
                <h2 className="text-lg font-bold text-white mb-1">التحقق بخطوتين</h2>
                <p className="text-xs text-slate-400">أدخل رمز التحقق المرسل إلى بريدك الإلكتروني</p>
              </div>

              <div className="flex justify-center gap-3" dir="ltr">
                {otp.map((digit, i) => (
                  <input
                    key={i}
                    id={`otp-${i}`}
                    type="text"
                    maxLength={1}
                    value={digit}
                    onChange={e => handleOtpChange(i, e.target.value)}
                    onKeyDown={e => handleOtpKeyDown(i, e)}
                    className="w-12 h-14 text-center bg-white/5 border border-white/10 rounded-xl text-lg font-black text-white focus:outline-none focus:border-indigo-500/50 focus:ring-2 focus:ring-indigo-500/20 transition-all"
                  />
                ))}
              </div>

              {error && <p className="text-xs text-rose-400 font-medium text-center">{error}</p>}

              <button
                type="submit"
                disabled={loading || otp.some(d => !d)}
                className="w-full py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-2xl font-bold text-sm transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading && <Loader2 size={18} className="animate-spin" />}
                تحقق
              </button>

              <button
                type="button"
                onClick={() => setStep('credentials')}
                className="w-full text-center text-xs text-slate-500 hover:text-slate-300 transition-colors"
              >
                العودة إلى تسجيل الدخول
              </button>
            </form>
          )}
        </div>
      </motion.div>
    </div>
  );
}
