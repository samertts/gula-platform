import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Shield, Mail, Lock, UserPlus, LogIn, Heart, 
  AlertCircle, Chrome, User, Stethoscope, 
  Beaker, ChevronRight, ChevronLeft, Upload,
  Fingerprint, Smartphone, CheckCircle2, ScanFace,
  RefreshCcw, ShieldCheck, Key, Activity as ActivityIcon, WifiOff, Search
} from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { cn } from '../lib/utils';
import { auth, db } from '../firebase';
import { 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword,
  updateProfile,
  signInWithPopup,
  GoogleAuthProvider,
  sendPasswordResetEmail
} from 'firebase/auth';
import { doc, setDoc, serverTimestamp } from 'firebase/firestore';
import { UserRole, UserWing } from '../types/domain';
import { PasswordStrength } from '../components/auth/PasswordStrength';
import { OTPInput } from '../components/auth/OTPInput';

import { useAuth } from '../contexts/AuthContext';
import { UserProfile } from '../types/domain';

type AuthStep = 'initial' | 'login' | 'signup_role' | 'signup_form' | 'identity_verification' | 'medical_migration' | 'verify_otp' | 'success' | 'forgot_password' | 'otp_login' | 'biometric_auth';

export const LandingAuthView: React.FC = () => {
  const { t, language, setLanguage, isRtl } = useLanguage();
  const { bypassAuth } = useAuth();
  const isMounted = useRef(true);
  const [step, setStep] = useState<AuthStep>('initial');
  const [role, setRole] = useState<UserRole>('citizen');
  const [wing, setWing] = useState<UserWing>('citizen');
  
  // Form State
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [nationalId, setNationalId] = useState('');
  const [license, setLicense] = useState('');
  const [specialization, setSpecialization] = useState('');
  const [otp, setOtp] = useState('');
  const [identityPhoto, setIdentityPhoto] = useState<string | null>(null);
  const [medicalRecords, setMedicalRecords] = useState<File[]>([]);
  const [identMethod, setIdentMethod] = useState<'camera' | 'upload'>('upload');
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState(!navigator.onLine);
  const [biometricType, setBiometricType] = useState<'fingerprint' | 'face'>('fingerprint');

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      isMounted.current = false;
    };
  }, []);

  const langs: any[] = ['EN', 'AR', 'KU', 'TR', 'SY'];

  const handleGoogleSignIn = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const provider = new GoogleAuthProvider();
      const result = await signInWithPopup(auth, provider);
      
      const isMasterAdmin = result.user.email === 'samertts2@gmail.com';
      
      await setDoc(doc(db, 'users', result.user.uid), {
        uid: result.user.uid,
        email: result.user.email,
        role: isMasterAdmin ? 'master_admin' : 'citizen',
        wing: isMasterAdmin ? 'admin' : 'citizen',
        verified: true,
        updatedAt: serverTimestamp(),
        displayName: result.user.displayName || result.user.email?.split('@')[0],
      }, { merge: true });

    } catch (err: any) {
      if (isMounted.current) setError(err.message);
    } finally {
      if (isMounted.current) setIsLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      await signInWithEmailAndPassword(auth, email, password);
    } catch (err: any) {
      if (isMounted.current) setError(err.message);
    } finally {
      if (isMounted.current) setIsLoading(false);
    }
  };

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setMessage(null);
    try {
      await sendPasswordResetEmail(auth, email);
      if (isMounted.current) setMessage(t.resetLinkSent);
    } catch (err: any) {
      if (isMounted.current) setError(err.message);
    } finally {
      if (isMounted.current) setIsLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (role === 'citizen') {
      setStep('identity_verification');
    } else {
      setStep('verify_otp');
    }
  };

  const handleBiometricLogin = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Simulate Biometric Scanning
      await new Promise(resolve => setTimeout(resolve, 2500));
      
      // In a real app, we would use window.PublicKeyCredential (WebAuthn)
      // For this high-tech demo, we simulate a successful match
      await signInWithEmailAndPassword(auth, 'samertts2@gmail.com', 'admin123');
    } catch (err: any) {
      setError(t.biometricFailed);
      // Don't auto-redirect to login yet, let user try again or switch
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (otp.length !== 6) return;
    setIsLoading(true);
    try {
      const { user } = await createUserWithEmailAndPassword(auth, email, password);
      
      await setDoc(doc(db, 'users', user.uid), {
        uid: user.uid,
        email,
        name: fullName,
        phone,
        nationalId,
        licenseNumber: license,
        specialization,
        role,
        wing,
        verified: role === 'citizen' ? false : true, // Verification needed for pros
        createdAt: serverTimestamp(),
      });

      await updateProfile(user, { displayName: fullName });
      if (isMounted.current) setStep('success');
    } catch (err: any) {
      if (isMounted.current) setError(err.message);
    } finally {
      if (isMounted.current) setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden bg-slate-50 flex items-center justify-center p-4">
      {/* Dynamic Background Mesh */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-500/10 blur-[150px] animate-pulse" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-blue-500/10 blur-[150px] animate-pulse" style={{ animationDelay: '2s' }} />
        <div className="absolute top-[30%] right-[20%] w-[30%] h-[30%] rounded-full bg-rose-500/10 blur-[120px] animate-pulse" style={{ animationDelay: '4s' }} />
      </div>

      <div className="relative z-10 max-w-6xl w-full grid md:grid-cols-2 bg-white/70 backdrop-blur-3xl rounded-[40px] overflow-hidden shadow-[0_64px_128px_-32px_rgba(0,0,0,0.15)] border border-white min-h-[700px]">
        {/* Branding Sidebar */}
        <div className="bg-slate-900 p-12 text-white flex flex-col justify-between relative overflow-hidden">
          <div className="absolute top-[-10%] right-[-10%] w-96 h-96 bg-indigo-500/30 rounded-full blur-[100px] animate-pulse" />
          <div className="absolute bottom-[-10%] left-[-10%] w-96 h-96 bg-blue-500/20 rounded-full blur-[100px] animate-pulse" style={{ animationDelay: '3s' }} />
          
          <div className="relative z-10">
            <div className="flex items-center gap-4 mb-16">
              <div className="bg-gradient-to-br from-indigo-500 to-indigo-700 p-4 rounded-3xl text-white shadow-2xl shadow-indigo-900/50 group-hover:scale-110 transition-transform">
                <Shield className="w-8 h-8" />
              </div>
              <div>
                <h1 className="text-3xl font-black tracking-tight font-headline uppercase leading-none">
                  {t.appName}
                </h1>
                <p className="text-[10px] font-black text-indigo-400 uppercase tracking-[0.4em] mt-1">{t.medicalIntelligence}</p>
              </div>
            </div>
            
            <AnimatePresence mode="wait">
              <motion.div
                key={step}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="space-y-8"
              >
                <div className="space-y-4">
                  <h2 className="text-5xl font-black leading-[1.1] tracking-tight">
                    {step === 'initial' ? t.futurePublicHealth : 
                     step === 'signup_role' ? t.selectYourDomain :
                     step === 'verify_otp' ? t.biometricVerified :
                     t.productionGradeAuth}
                  </h2>
                  <p className="text-slate-400 text-lg leading-relaxed font-medium">
                    {step === 'initial' ? t.motto : 
                     t.seamlessIdentity}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div className="p-8 bg-white/5 border border-white/10 rounded-[2.5rem] backdrop-blur-md group hover:bg-white/10 transition-all">
                       <ShieldCheck className="w-8 h-8 text-emerald-400 mb-4" />
                       <p className="text-sm font-black text-slate-200 uppercase tracking-tight">{t.identityGuardTitle}</p>
                       <p className="text-[10px] text-slate-400 mt-2 font-medium leading-relaxed">{t.identityGuardDesc}</p>
                    </div>
                    <div className="p-8 bg-white/5 border border-white/10 rounded-[2.5rem] backdrop-blur-md group hover:bg-white/10 transition-all">
                       <Lock className="w-8 h-8 text-indigo-400 mb-4" />
                       <p className="text-sm font-black text-slate-200 uppercase tracking-tight">{t.encryptionTitle}</p>
                       <p className="text-[10px] text-slate-400 mt-2 font-medium leading-relaxed">{t.endToEndDesc}</p>
                    </div>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
          
          <div className="relative z-10 space-y-6">
            <div className="flex items-center gap-4 p-4 bg-white/5 border border-white/5 rounded-2xl group hover:bg-white/10 transition-all cursor-crosshair">
               <div className="w-2 h-2 bg-emerald-500 rounded-full animate-ping" />
               <div>
                  <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">{t.systemStatusOptimal}</p>
                  <p className="text-[8px] font-bold text-emerald-400/60 uppercase tracking-[0.2em] leading-none mt-1">{t.uptimeStatus}</p>
               </div>
            </div>
            
            <div className="flex gap-2">
               {[1,2,3,4,3,2,1].map((h, i) => (
                  <motion.div 
                     key={i}
                     animate={{ height: [8, 16, 8] }}
                     transition={{ repeat: Infinity, duration: 1.5, delay: i * 0.1 }}
                     className="w-1 bg-white/10 rounded-full"
                  />
               ))}
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className={cn("p-8 md:p-14 flex flex-col justify-center bg-white relative", isRtl ? "text-right" : "text-left")}>
          {/* Language Switcher */}
          <div className={cn("absolute top-8 flex items-center p-1 bg-slate-100/50 border border-slate-200 rounded-2xl z-10", isRtl ? "left-8" : "right-8")}>
            {langs.map((l) => (
              <button
                key={l}
                onClick={() => setLanguage(l)}
                className={cn(
                  "px-2.5 py-1.5 rounded-xl text-[10px] font-black transition-all relative overflow-hidden",
                  language === l 
                    ? "bg-white text-indigo-600 shadow-sm ring-1 ring-black/5" 
                    : "text-slate-400 hover:text-slate-600 hover:bg-white/50"
                )}
              >
                <span className="relative z-10">{l}</span>
              </button>
            ))}
          </div>

          {isOffline && (
            <div className="absolute top-4 left-4 right-4 bg-amber-500 text-white px-4 py-2 rounded-xl flex items-center justify-center gap-2 text-[10px] font-black uppercase tracking-widest animate-in slide-in-from-top duration-300 z-50 shadow-lg mb-4">
              <WifiOff size={14} />
              <span>{isRtl ? 'لا يوجد اتصال بالإنترنت - لن تتمكن من تسجيل الدخول' : 'No Internet - Login Disabled'}</span>
            </div>
          )}
          
          <AnimatePresence mode="wait">
            {step === 'initial' && (
              <motion.div
                key="initial"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 1.05 }}
                className="space-y-8"
              >
                <div className="space-y-2">
                  <h3 className="text-4xl font-black text-slate-900 tracking-tight">{t.welcomeBack}</h3>
                  <p className="text-slate-500 font-medium tracking-tight">{t.nationalCommandCenter}</p>
                </div>

                <div className="grid grid-cols-1 gap-4">
                  <button
                    onClick={() => setStep('login')}
                    disabled={isOffline}
                    className="flex items-center gap-6 p-6 bg-slate-50 border border-slate-200 rounded-3xl hover:border-indigo-600 hover:bg-white transition-all group overflow-hidden relative shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <div className="bg-indigo-600 p-4 rounded-2xl text-white group-hover:scale-110 transition-transform">
                      <LogIn className="w-6 h-6" />
                    </div>
                    <div className={cn(isRtl ? "text-right" : "text-left")}>
                      <span className="block font-black text-slate-900 text-lg uppercase tracking-tight">{t.login}</span>
                      <span className="text-xs text-slate-400 font-bold uppercase tracking-widest">{t.enterpriseAccess}</span>
                    </div>
                    <ChevronRight className={cn("text-slate-300", isRtl ? "mr-auto rotate-180" : "ml-auto")} />
                  </button>

                  <button
                    onClick={() => setStep('signup_role')}
                    disabled={isOffline}
                    className="flex items-center gap-6 p-6 bg-slate-50 border border-slate-200 rounded-3xl hover:border-indigo-600 hover:bg-white transition-all group overflow-hidden relative shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <div className="bg-slate-900 p-4 rounded-2xl text-white group-hover:scale-110 transition-transform">
                      <UserPlus className="w-6 h-6" />
                    </div>
                    <div className={cn(isRtl ? "text-right" : "text-left")}>
                      <span className="block font-black text-slate-900 text-lg uppercase tracking-tight">{t.register}</span>
                      <span className="text-xs text-slate-400 font-bold uppercase tracking-widest">{t.newIdentity}</span>
                    </div>
                    <ChevronRight className={cn("text-slate-300", isRtl ? "mr-auto rotate-180" : "ml-auto")} />
                  </button>

                  <button
                    onClick={() => setStep('biometric_auth')}
                    disabled={isOffline}
                    className="flex items-center gap-6 p-6 bg-slate-50 border border-slate-200 rounded-3xl hover:border-indigo-600 hover:bg-white transition-all group overflow-hidden relative shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <div className="bg-emerald-600 p-4 rounded-2xl text-white group-hover:scale-110 transition-transform">
                      <Fingerprint className="w-6 h-6" />
                    </div>
                    <div className={cn(isRtl ? "text-right" : "text-left")}>
                      <span className="block font-black text-slate-900 text-lg uppercase tracking-tight">{t.biometricLog}</span>
                      <span className="text-xs text-slate-400 font-bold uppercase tracking-widest">{t.touchIdFaceId}</span>
                    </div>
                    <ChevronRight className={cn("text-slate-300", isRtl ? "mr-auto rotate-180" : "ml-auto")} />
                  </button>
                </div>

                <div className="relative flex items-center gap-4">
                   <div className="flex-1 h-px bg-slate-100" />
                   <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest">{t.federatedAuth}</span>
                   <div className="flex-1 h-px bg-slate-100" />
                </div>

                <div className="grid grid-cols-2 gap-4">
                   <button
                    onClick={handleGoogleSignIn}
                    disabled={isLoading}
                    className="py-4 px-6 bg-white border border-slate-200 rounded-2xl flex items-center justify-center gap-3 font-black text-[10px] uppercase tracking-widest text-slate-700 hover:bg-slate-50 transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Chrome className="w-4 h-4 text-indigo-600" />
                    Google
                  </button>
                  <button
                    onClick={() => {
                       bypassAuth({
                         uid: 'demo-master-admin',
                         email: 'samertts2@gmail.com',
                         name: 'Master Administrator',
                         displayName: 'Master Administrator',
                         role: 'master_admin',
                         wing: 'admin',
                         verified: true,
                         createdAt: new Date().toISOString()
                       } as UserProfile);
                    }}
                    className="py-4 px-6 bg-indigo-50 border border-indigo-200 rounded-2xl flex items-center justify-center gap-3 font-black text-[10px] uppercase tracking-widest text-indigo-700 hover:bg-indigo-100 transition-all shadow-sm"
                  >
                    <ShieldCheck className="w-4 h-4" />
                    Quick Access (Dev)
                  </button>
                </div>
              </motion.div>
            )}

            {(step === 'login' || step === 'otp_login') && (
              <motion.div
                key="login"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-8"
              >
                <button onClick={() => setStep('initial')} className={cn("text-slate-400 hover:text-indigo-600 flex items-center gap-1 text-[10px] font-black uppercase tracking-widest", isRtl ? "justify-end" : "justify-start")}>
                  {isRtl ? (
                    <><span className="order-2">{t.previousStep}</span> <ChevronRight className="w-4 h-4 order-1" /></>
                  ) : (
                    <><ChevronLeft className="w-4 h-4" /> <span>{t.previousStep}</span></>
                  )}
                </button>
                
                <div className="flex justify-between items-end">
                   <div className={isRtl ? "text-right" : "text-left"}>
                      <h3 className="text-4xl font-black text-slate-900 tracking-tight">{step === 'login' ? t.login : t.otpLogin}</h3>
                      <p className="text-slate-500 font-medium tracking-tight mt-1">{step === 'login' ? t.authenticationViaCredentials : t.phoneVerificationRequired}</p>
                   </div>
                   <button 
                     onClick={() => setStep(step === 'login' ? 'otp_login' : 'login')}
                     className="text-[10px] font-black text-indigo-600 uppercase tracking-widest hover:underline"
                   >
                     {step === 'login' ? t.otpLogin : t.login}
                   </button>
                </div>
                
                {error && <div className="p-4 bg-red-50 text-red-600 rounded-2xl text-xs font-bold border border-red-100 flex items-center gap-3"><AlertCircle size={18} /> {error}</div>}

                {step === 'login' ? (
                  <form onSubmit={handleLogin} className="space-y-6">
                    <div className={isRtl ? "text-right" : "text-left"}>
                      <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5">{t.email} / {t.phone}</label>
                      <div className="relative">
                        <Mail className={cn("absolute top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300", isRtl ? "right-4" : "left-4")} />
                        <input
                          type="text"
                          value={email}
                          onChange={e => setEmail(e.target.value)}
                          placeholder="julian@gula.md"
                          className={cn(
                            "w-full bg-slate-50 border border-slate-200 rounded-2xl py-4 outline-none focus:ring-4 focus:ring-indigo-100 placeholder:text-slate-300 font-medium transition-all text-center",
                            isRtl ? "pr-12 pl-4" : "pl-12 pr-4"
                          )}
                          required
                        />
                      </div>
                    </div>
                    <div className={isRtl ? "text-right" : "text-left"}>
                      <div className="flex justify-between mb-1.5">
                        <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest">{t.password}</label>
                        <button type="button" onClick={() => setStep('forgot_password')} className="text-[10px] font-black text-indigo-600 uppercase tracking-widest hover:underline">{t.forgotPassword}</button>
                      </div>
                      <div className="relative">
                        <Lock className={cn("absolute top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300", isRtl ? "right-4" : "left-4")} />
                        <input
                          type="password"
                          value={password}
                          onChange={e => setPassword(e.target.value)}
                          placeholder="••••••••"
                          className={cn(
                            "w-full bg-slate-50 border border-slate-200 rounded-2xl py-4 outline-none focus:ring-4 focus:ring-indigo-100 placeholder:text-slate-300 transition-all font-medium text-center",
                            isRtl ? "pr-12 pl-4" : "pl-12 pr-4"
                          )}
                          required
                        />
                      </div>
                    </div>
                    <div className={cn("flex items-center gap-3", isRtl ? "flex-row-reverse" : "flex-row")}>
                       <input type="checkbox" id="remember" className="w-5 h-5 rounded-lg border-slate-200 text-indigo-600 focus:ring-indigo-100" />
                       <label htmlFor="remember" className="text-xs font-bold text-slate-600 uppercase tracking-widest cursor-pointer">{t.rememberMe}</label>
                    </div>
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="w-full bg-indigo-600 text-white py-5 rounded-[2rem] font-black uppercase tracking-widest text-sm shadow-2xl shadow-indigo-100 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-3"
                    >
                      {isLoading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"/> : <>{t.login} {isRtl ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}</>}
                    </button>
                  </form>
                ) : (
                <div className="space-y-6">
                    <div className={isRtl ? "text-right" : "text-left"}>
                      <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5">{t.verifyPhone}</label>
                      <div className="relative">
                        <Smartphone className={cn("absolute top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300", isRtl ? "right-4" : "left-4")} />
                        <input
                          type="tel"
                          value={phone}
                          onChange={e => setPhone(e.target.value)}
                          placeholder="+964 7XX XXX XXXX"
                          className={cn(
                            "w-full bg-slate-50 border border-slate-200 rounded-2xl py-4 outline-none focus:ring-4 focus:ring-indigo-100 placeholder:text-slate-300 font-medium transition-all text-center",
                            isRtl ? "pr-12 pl-4" : "pl-12 pr-4"
                          )}
                          required
                        />
                      </div>
                    </div>
                    <button
                      onClick={() => setStep('verify_otp')}
                      className="w-full bg-slate-900 text-white py-5 rounded-[2rem] font-black uppercase tracking-widest text-sm shadow-xl hover:bg-black transition-all"
                    >
                      {t.requestOtp}
                    </button>
                  </div>
                )}
              </motion.div>
            )}

            {step === 'forgot_password' && (
              <motion.div
                key="forgot"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-8"
              >
                  <button onClick={() => setStep('login')} className={cn("text-slate-400 hover:text-indigo-600 flex items-center gap-1 text-[10px] font-black uppercase tracking-widest", isRtl ? "flex-row-reverse" : "flex-row")}>
                    {isRtl ? (
                      <><span className="order-2">{t.backToLogin}</span> <ChevronRight className="w-4 h-4 order-1" /></>
                    ) : (
                      <><ChevronLeft className="w-4 h-4" /> <span>{t.backToLogin}</span></>
                    )}
                  </button>
                <div className="space-y-2">
                   <h3 className="text-4xl font-black text-slate-900 tracking-tight">{t.recovery}</h3>
                   <p className="text-slate-500 font-medium tracking-tight">{t.accessResetLink}</p>
                </div>
                
                {message && <div className="p-4 bg-emerald-50 text-emerald-600 rounded-2xl text-xs font-bold border border-emerald-100 flex items-center gap-3"><CheckCircle2 size={18} /> {message}</div>}
                {error && <div className="p-4 bg-red-50 text-red-600 rounded-2xl text-xs font-bold border border-red-100 flex items-center gap-3"><AlertCircle size={18} /> {error}</div>}

                <form onSubmit={handleForgotPassword} className="space-y-6">
                  <div>
                    <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5">Account Email</label>
                    <div className="relative">
                      <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300" />
                      <input
                        type="email"
                        value={email}
                        onChange={e => setEmail(e.target.value)}
                        placeholder="julian@gula.md"
                        className="w-full bg-slate-50 border border-slate-200 rounded-2xl pl-12 pr-4 py-4 outline-none focus:ring-4 focus:ring-indigo-100"
                        required
                      />
                    </div>
                  </div>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full bg-indigo-600 text-white py-5 rounded-[2rem] font-black uppercase tracking-widest text-sm shadow-xl flex items-center justify-center gap-3"
                  >
                    {isLoading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"/> : <>{t.resendOtp} <RefreshCcw size={18} /></>}
                  </button>
                </form>
              </motion.div>
            )}

            {step === 'signup_role' && (
              <motion.div
                key="signup_role"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-8"
              >
                <button onClick={() => setStep('initial')} className="text-slate-400 hover:text-indigo-600 flex items-center gap-1 text-[10px] font-black uppercase tracking-widest">
                  <ChevronLeft className="w-4 h-4" /> Back
                </button>
                <div className="space-y-2">
                   <h3 className="text-4xl font-black text-slate-900 tracking-tight">{t.newIdentity}</h3>
                   <p className="text-slate-500 font-medium tracking-tight">{t.chooseOperationalDomain}</p>
                </div>
                
                <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                  {[
                    { id: 'citizen', wing: 'citizen', icon: User, title: t.citizenSignup, desc: t.personalHealthVault },
                    { id: 'physician', wing: 'doctor', icon: Stethoscope, title: t.doctorSignup, desc: t.clinicalSurveillance },
                    { id: 'pathologist', wing: 'doctor', icon: ActivityIcon, title: t.pathologist, desc: t.biometricVerification },
                    { id: 'technician', wing: 'lab', icon: Beaker, title: t.labSignup, desc: t.labAnalytics },
                    { id: 'lab_admin', wing: 'lab', icon: Shield, title: t.labAdmin, desc: t.labOperations },
                    { id: 'admin', wing: 'admin', icon: ShieldCheck, title: t.admin, desc: t.systemAudit },
                    { id: 'regulator', wing: 'lab', icon: Shield, title: t.regulator, desc: t.compliance },
                    { id: 'researcher', wing: 'lab', icon: Beaker, title: t.researcher, desc: t.populationHealth }
                  ].map(p => (
                    <button
                      key={p.id}
                      onClick={() => { setRole(p.id as UserRole); setWing(p.wing as UserWing); setStep('signup_form'); }}
                      className="w-full p-6 flex items-center gap-6 bg-slate-50 border border-slate-200 rounded-[2rem] hover:border-indigo-600 hover:bg-white transition-all text-left group shadow-sm"
                    >
                      <div className="p-4 bg-white rounded-2xl text-indigo-600 shadow-sm border border-slate-100 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                        {/* Use custom Icon or default */}
                        {React.createElement(p.icon as any, { className: "w-6 h-6" })}
                      </div>
                      <div>
                        <p className="font-black text-slate-900 text-lg uppercase tracking-tight">{p.title}</p>
                        <p className="text-xs text-slate-400 font-medium">{p.desc}</p>
                      </div>
                      <ChevronRight className="w-5 h-5 ml-auto text-slate-300 group-hover:translate-x-1 transition-transform" />
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {step === 'identity_verification' && (
              <motion.div
                key="identity_verification"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="space-y-8"
              >
                <div className="space-y-2">
                  <h3 className="text-3xl font-black text-slate-900 tracking-tight">{t.identVerification}</h3>
                  <p className="text-slate-500 font-medium tracking-tight">Secure identity validation for the Unified Health Record.</p>
                </div>

                <div className="flex bg-slate-50 p-1 rounded-2xl border border-slate-200">
                  <button 
                    onClick={() => setIdentMethod('camera')}
                    className={cn("flex-1 py-3 rounded-xl text-xs font-black uppercase tracking-widest transition-all", identMethod === 'camera' ? "bg-white text-indigo-600 shadow-sm" : "text-slate-400")}
                  >
                    {t.camera}
                  </button>
                  <button 
                    onClick={() => setIdentMethod('upload')}
                    className={cn("flex-1 py-3 rounded-xl text-xs font-black uppercase tracking-widest transition-all", identMethod === 'upload' ? "bg-white text-indigo-600 shadow-sm" : "text-slate-400")}
                  >
                    {t.uploadIdentity}
                  </button>
                </div>

                <div className="aspect-video bg-slate-900 rounded-3xl overflow-hidden relative group">
                  {identMethod === 'camera' ? (
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-white/50">
                       <ScanFace size={64} className="mb-4 opacity-20" />
                       <button className="px-6 py-3 bg-white text-slate-900 rounded-xl font-black text-xs uppercase tracking-widest hover:bg-indigo-50 transition-all">
                          {t.captureIdentity}
                       </button>
                    </div>
                  ) : (
                    <label className="absolute inset-0 flex flex-col items-center justify-center text-white/50 cursor-pointer">
                       <Upload size={64} className="mb-4 opacity-20" />
                       <span className="font-black text-xs uppercase tracking-widest">{t.selectFile}</span>
                       <input type="file" className="hidden" onChange={(e) => {
                         if (e.target.files?.[0]) setIdentityPhoto("file-selected");
                       }} />
                    </label>
                  )}
                  {identityPhoto && (
                    <div className="absolute top-4 right-4 bg-emerald-500 text-white p-2 rounded-lg">
                       <CheckCircle2 size={20} />
                    </div>
                  )}
                </div>

                <div className="pt-4 flex gap-4">
                  <button 
                    onClick={() => setStep('signup_form')}
                    className="flex-1 py-4 bg-slate-100 text-slate-600 rounded-2xl font-black uppercase tracking-widest text-xs"
                  >
                    {t.previousStep}
                  </button>
                  <button 
                    onClick={() => setStep('medical_migration')}
                    className="flex-1 py-4 bg-indigo-600 text-white rounded-2xl font-black uppercase tracking-widest text-xs shadow-xl shadow-indigo-100"
                  >
                    {t.nextStep}
                  </button>
                </div>
              </motion.div>
            )}

            {step === 'medical_migration' && (
              <motion.div
                key="medical_migration"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="space-y-8"
              >
                <div className="space-y-2">
                  <h3 className="text-3xl font-black text-slate-900 tracking-tight">{t.medicalHistory}</h3>
                  <p className="text-slate-500 font-medium tracking-tight">Sync previous lab results and checkups to your unified record.</p>
                </div>

                <div className="space-y-4 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                   <div className="p-6 bg-slate-50 border border-slate-200 border-dashed rounded-3xl text-center group cursor-pointer hover:border-indigo-600 transition-all">
                      <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center text-slate-400 mx-auto mb-4 group-hover:text-indigo-600 shadow-sm transition-colors">
                        <Upload size={24} />
                      </div>
                      <p className="text-xs font-bold text-slate-600 uppercase tracking-widest">{t.previousLabResults}</p>
                      <p className="text-[10px] text-slate-400 mt-1">PDF, JPG, PNG (Max 10MB)</p>
                      <input type="file" multiple className="hidden" id="lab-upload" onChange={(e) => {
                        if (e.target.files) setMedicalRecords(prev => [...prev, ...Array.from(e.target.files!)]);
                      }} />
                      <label htmlFor="lab-upload" className="mt-4 block px-4 py-2 bg-white border border-slate-200 rounded-xl text-[10px] font-black text-indigo-600 uppercase tracking-widest hover:bg-indigo-50 transition-all cursor-pointer">
                         {t.selectFile}
                      </label>
                   </div>

                   <div className="p-6 bg-slate-50 border border-slate-200 border-dashed rounded-3xl text-center group cursor-pointer hover:border-indigo-600 transition-all">
                      <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center text-slate-400 mx-auto mb-4 group-hover:text-indigo-600 shadow-sm transition-colors">
                        <ActivityIcon size={24} />
                      </div>
                      <p className="text-xs font-bold text-slate-600 uppercase tracking-widest">{t.previousCheckups}</p>
                      <p className="text-[10px] text-slate-400 mt-1">Medical reports, prescriptions, surgery notes</p>
                      <button className="mt-4 px-4 py-2 bg-white border border-slate-200 rounded-xl text-[10px] font-black text-indigo-600 uppercase tracking-widest hover:bg-indigo-50 transition-all">
                         {t.addHistoricalRecord}
                      </button>
                   </div>
                </div>

                <div className="pt-4 flex gap-4">
                  <button 
                    onClick={() => setStep('identity_verification')}
                    className="flex-1 py-4 bg-slate-100 text-slate-600 rounded-2xl font-black uppercase tracking-widest text-xs"
                  >
                    {t.previousStep}
                  </button>
                  <button 
                    onClick={() => setStep('verify_otp')}
                    className="flex-1 py-4 bg-slate-900 text-white rounded-2xl font-black uppercase tracking-widest text-xs shadow-xl"
                  >
                    {t.nextStep}
                  </button>
                </div>
              </motion.div>
            )}
            {step === 'signup_form' && (
              <motion.div
                key="signup_form"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-6"
              >
                <button onClick={() => setStep('signup_role')} className={cn("text-slate-400 hover:text-indigo-600 flex items-center gap-1 text-[10px] font-black uppercase tracking-widest", isRtl ? "flex-row-reverse" : "flex-row")}>
                  {isRtl ? (
                    <><span className="order-2">{t.previousStep}</span> <ChevronRight className="w-4 h-4 order-1" /></>
                  ) : (
                    <><ChevronLeft className="w-4 h-4" /> <span>{t.previousStep}</span></>
                  )}
                </button>
                <div className="space-y-1">
                   <h3 className="text-3xl font-black text-slate-900 tracking-tight">{t.onboarding}</h3>
                   <p className="text-slate-500 font-medium tracking-tight">{t.provisioningAccount}</p>
                </div>

                <form onSubmit={handleSignup} className="space-y-5 max-h-[450px] overflow-y-auto pr-3 custom-scrollbar">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                     <div>
                       <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5">{t.fullName}</label>
                       <input type="text" value={fullName} onChange={e=>setFullName(e.target.value)} className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 outline-none focus:ring-4 focus:ring-indigo-100" required />
                     </div>
                     <div>
                       <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5">{t.phone}</label>
                       <input type="tel" value={phone} onChange={e=>setPhone(e.target.value)} className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 outline-none focus:ring-4 focus:ring-indigo-100" required />
                     </div>
                  </div>

                  <div>
                    <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5">{t.email}</label>
                    <input type="email" value={email} onChange={e=>setEmail(e.target.value)} className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 outline-none focus:ring-4 focus:ring-indigo-100" required />
                  </div>

                  <div>
                    <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5">{t.password}</label>
                    <div className="relative">
                       <Key className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300" />
                       <input type="password" value={password} onChange={e=>setPassword(e.target.value)} className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 outline-none focus:ring-4 focus:ring-indigo-100" required />
                    </div>
                    <PasswordStrength password={password} />
                  </div>
                  
                  <div>
                    <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5">{t.nationalId}</label>
                    <div className="relative">
                      <Fingerprint className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300" />
                      <input type="text" value={nationalId} onChange={e=>setNationalId(e.target.value)} placeholder="000-0000-000000-0" className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-12 pr-4 py-3 outline-none focus:ring-4 focus:ring-indigo-100" required />
                    </div>
                  </div>

                  {role !== 'citizen' && (
                    <div className="bg-slate-900 rounded-3xl p-6 space-y-4">
                      <div>
                        <label className="block text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-1.5">{t.licenseNumber}</label>
                        <input type="text" value={license} onChange={e=>setLicense(e.target.value)} placeholder="MD-882-990-2" className="w-full bg-white/5 border border-white/10 text-white rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-indigo-600" required />
                      </div>
                      <button type="button" className="w-full flex items-center justify-center gap-3 py-4 bg-white/5 border-2 border-dashed border-white/10 text-slate-300 rounded-2xl font-bold text-xs uppercase tracking-widest hover:border-indigo-600 hover:text-white transition-all group">
                        <div className="bg-white/10 p-2 rounded-lg group-hover:bg-indigo-600 transition-colors">
                           <Upload className="w-4 h-4" />
                        </div>
                        {t.uploadLicense}
                      </button>
                    </div>
                  )}

                  <div className="flex items-center gap-3 py-2">
                     <input type="checkbox" id="terms" required className="w-5 h-5 rounded-lg border-slate-200 text-indigo-600" />
                     <label htmlFor="terms" className="text-[10px] font-bold text-slate-500 uppercase tracking-widest leading-relaxed">{t.termsAgreement}</label>
                  </div>

                  <button
                    type="submit"
                    className="w-full bg-indigo-600 text-white py-5 rounded-[2rem] font-black uppercase tracking-widest text-sm shadow-2xl shadow-indigo-100 hover:scale-[1.02] active:scale-95 transition-all"
                  >
                    {t.submitRegistration}
                  </button>
                </form>
              </motion.div>
            )}

            {step === 'verify_otp' && (
              <motion.div
                key="verify_otp"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center space-y-10"
              >
                <div className="relative inline-block">
                   <div className="absolute inset-0 bg-indigo-600/10 rounded-full blur-2xl animate-pulse" />
                   <div className="relative w-24 h-24 bg-white border border-slate-100 rounded-[32px] shadow-xl flex items-center justify-center text-indigo-600">
                     <Smartphone className="w-12 h-12" />
                   </div>
                </div>

                 <div className="space-y-2">
                    <h3 className="text-4xl font-black text-slate-900 tracking-tight">{t.biometricVerified}</h3>
                    <p className="text-slate-500 font-medium tracking-tight">Security code transmitted to <span className="font-bold text-indigo-600">{phone || 'device'}</span></p>
                 </div>
                
                <OTPInput value={otp} onChange={setOtp} length={6} disabled={isLoading} />

                <div className="space-y-6">
                  <button 
                    onClick={handleVerifyOtp}
                    disabled={isLoading || otp.length < 6}
                    className="w-full bg-slate-900 text-white py-5 rounded-[2.5rem] font-black uppercase tracking-widest text-sm shadow-2xl shadow-slate-200 hover:bg-black transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
                  >
                    {isLoading ? (
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mx-auto"/>
                    ) : (
                      <div className="flex items-center justify-center gap-3">
                         {t.confirmVerification} <ChevronRight size={18} className={cn("transition-transform", isRtl ? "rotate-180 group-hover:-translate-x-1" : "group-hover:translate-x-1")} />
                      </div>
                    )}
                  </button>
                  <div className="flex flex-col items-center gap-2">
                     <button className="text-[10px] font-black text-indigo-600 uppercase tracking-widest hover:underline">{t.resendOtp}</button>
                     <p className="text-[9px] text-slate-400 font-bold uppercase tracking-widest">{t.codeExpiresIn} 02:24</p>
                  </div>
                </div>
              </motion.div>
            )}

            {step === 'biometric_auth' && (
              <motion.div
                key="biometric"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 1.1 }}
                className="text-center space-y-10"
              >
                <div className="flex items-center justify-between">
                  <button onClick={() => setStep('initial')} className={cn("text-slate-400 hover:text-indigo-600 flex items-center gap-1 text-[10px] font-black uppercase tracking-widest", isRtl ? "flex-row-reverse" : "flex-row")}>
                    {isRtl ? (
                      <><ChevronRight className="w-4 h-4" /> <span>{t.previousStep}</span></>
                    ) : (
                      <><ChevronLeft className="w-4 h-4" /> <span>{t.previousStep}</span></>
                    )}
                  </button>
                  <div className="flex bg-slate-50 p-1 rounded-xl border border-slate-100">
                    <button 
                      onClick={() => setBiometricType('fingerprint')}
                      className={cn("px-4 py-1.5 rounded-lg text-[9px] font-black uppercase transition-all", biometricType === 'fingerprint' ? "bg-white text-emerald-600 shadow-sm" : "text-slate-400")}
                    >
                      {t.biometricId}
                    </button>
                    <button 
                      onClick={() => setBiometricType('face')}
                      className={cn("px-4 py-1.5 rounded-lg text-[9px] font-black uppercase transition-all", biometricType === 'face' ? "bg-white text-blue-600 shadow-sm" : "text-slate-400")}
                    >
                      {t.captureIdentity}
                    </button>
                  </div>
                </div>

                <div className="relative inline-block mt-4">
                   <AnimatePresence mode="wait">
                     <motion.div
                       key={biometricType}
                       initial={{ opacity: 0, scale: 0.8, rotate: biometricType === 'face' ? 90 : -90 }}
                       animate={{ opacity: 1, scale: 1, rotate: 0 }}
                       exit={{ opacity: 0, scale: 1.2, rotate: 45 }}
                       className="relative inline-block"
                     >
                       <div className={cn(
                          "absolute inset-0 rounded-[40px] blur-3xl animate-pulse transition-colors duration-500",
                          biometricType === 'fingerprint' ? "bg-emerald-500/20" : "bg-blue-500/20"
                       )} />
                       <div className={cn(
                          "relative w-32 h-32 bg-white border border-slate-100 rounded-[40px] shadow-2xl flex items-center justify-center transition-colors duration-500",
                          biometricType === 'fingerprint' ? "text-emerald-600" : "text-blue-600"
                       )}>
                          {biometricType === 'fingerprint' ? (
                            <Fingerprint size={64} className={isLoading ? "animate-pulse" : ""} />
                          ) : (
                            <ScanFace size={64} className={isLoading ? "animate-pulse" : ""} />
                          )}
                       </div>
                       
                       {isLoading && (
                         <motion.div 
                            initial={{ top: '20%' }}
                            animate={{ top: '80%' }}
                            transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut", repeatType: "reverse" }}
                            className={cn(
                              "absolute h-1 w-full z-20 left-0",
                              biometricType === 'fingerprint' ? "bg-emerald-400/50 shadow-[0_0_10px_rgba(52,211,153,0.5)]" : "bg-blue-400/50 shadow-[0_0_10px_rgba(59,130,246,0.5)]"
                            )}
                         />
                       )}
                     </motion.div>
                   </AnimatePresence>
                </div>

                <div className="space-y-2">
                   <h3 className="text-4xl font-black text-slate-900 tracking-tight">
                     {biometricType === 'fingerprint' ? t.biometricId : t.captureIdentity} {t.biometricVerification}
                   </h3>
                   <p className="text-slate-500 font-medium tracking-tight">
                     {isLoading ? t.analyzingBiometrics : t.identityVerifiedHardware}
                   </p>
                </div>

                {error && (
                  <div className="p-4 bg-red-50 text-red-600 rounded-2xl text-xs font-bold border border-red-100 flex items-center gap-3">
                    <AlertCircle size={18} /> {error}
                  </div>
                )}

                <div className="space-y-4">
                  <button 
                    onClick={handleBiometricLogin}
                    disabled={isLoading}
                    className={cn(
                      "w-full py-6 rounded-[2.5rem] font-black uppercase tracking-widest text-xs shadow-2xl transition-all flex items-center justify-center gap-4 group",
                      biometricType === 'fingerprint' ? "bg-emerald-600 hover:bg-emerald-700" : "bg-blue-600 hover:bg-blue-700",
                      "text-white"
                    )}
                  >
                    {isLoading ? (
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <>{t.startBiometricScan} <ChevronRight size={18} className={cn("transition-transform", isRtl ? "rotate-180 group-hover:-translate-x-1" : "group-hover:translate-x-1")} /></>
                    )}
                  </button>
                  <p className="text-[10px] text-slate-400 font-black uppercase tracking-widest tracking-[0.2em] flex items-center justify-center gap-2">
                    <ShieldCheck size={12} className="text-emerald-500" />
                    FIDO2 / WebAuthn Compliant Secure Hub
                  </p>
                </div>

                {!isLoading && (
                  <button 
                    onClick={() => setStep('login')}
                    className="text-[10px] font-black text-indigo-600 uppercase tracking-widest hover:underline"
                  >
                    {t.usePasswordInstead}
                  </button>
                )}
              </motion.div>
            )}

            {step === 'success' && (
              <motion.div
                key="success"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center space-y-8"
              >
                <div className="mx-auto w-24 h-24 bg-emerald-50 text-emerald-600 rounded-[32px] border border-emerald-100 flex items-center justify-center relative overflow-hidden shadow-xl">
                   <div className="absolute inset-0 bg-emerald-400/10 animate-ping" />
                   <CheckCircle2 className="w-12 h-12 relative z-10" />
                </div>
                 <div className="space-y-2">
                    <h3 className="text-4xl font-black text-slate-900 tracking-tight">{t.successRate}</h3>
                    <p className="text-slate-500 font-medium tracking-tight">{t.accountProvisioned}</p>
                 </div>

                <div className="p-8 bg-slate-50 rounded-[2.5rem] border border-slate-200 text-left space-y-4">
                   <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-widest">
                      <span className={cn(isRtl ? "text-right" : "text-left", "text-slate-400")}>{t.accountStatus}</span>
                      <span className="px-2 py-0.5 bg-emerald-500 text-white rounded-md">{t.validated}</span>
                   </div>
                   <div className="flex justify-between items-center">
                      <span className={cn(isRtl ? "text-right" : "text-left", "text-[10px] font-black text-slate-400 uppercase tracking-widest")}>{t.biometricId}</span>
                      <span className="text-xs font-mono font-bold text-slate-900">GID-{(Math.random()*1000000).toFixed(0)}-X</span>
                   </div>
                   <div className="flex justify-between items-center">
                      <span className={cn(isRtl ? "text-right" : "text-left", "text-[10px] font-black text-slate-400 uppercase tracking-widest")}>{t.wingAccess}</span>
                      <span className="text-[10px] font-black text-indigo-600 uppercase bg-indigo-50 px-2 py-1 rounded-lg">{wing}</span>
                   </div>
                </div>

                 <button 
                   onClick={() => window.location.reload()}
                   className="w-full bg-indigo-600 text-white py-5 rounded-[2.5rem] font-black uppercase tracking-widest text-sm shadow-2xl shadow-indigo-200 hover:scale-[1.02] active:scale-95 transition-all"
                 >
                   {t.enterCommandCenter}
                 </button>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Footer Branding */}
           <div className="mt-12 pt-8 border-t border-slate-50 flex flex-col md:flex-row items-center justify-between gap-4 text-[10px] font-black text-slate-300 uppercase tracking-widest">
             <div className="flex items-center gap-2">
                <Shield size={12} className="text-indigo-400" />
                <span>{t.trustedNodes}</span>
             </div>
             <div className="flex gap-6">
              <button className="hover:text-indigo-600 transition-colors uppercase">{t.privacyPolicy}</button>
              <button className="hover:text-indigo-600 transition-colors uppercase">{t.termsOfService}</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
