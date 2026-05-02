import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Fingerprint, Camera, ShieldCheck, FileText, 
  ChevronRight, AlertCircle, CheckCircle2, Clock
} from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { cn } from '../../lib/utils';

type VerificationStep = 'biometric' | 'document' | 'face' | 'review';

export const IdentityVerificationView: React.FC = () => {
  const { t, language } = useLanguage();
  const [currentStep, setCurrentStep] = useState<VerificationStep>('biometric');
  const isRtl = language === 'AR' || language === 'KU' || language === 'SY';

  const steps: { id: VerificationStep; title: string; icon: any; loa: string }[] = [
    { id: 'biometric', title: 'Biometric Scan', icon: Fingerprint, loa: 'LoA 3' },
    { id: 'document', title: 'Document Upload', icon: FileText, loa: 'LoA 2' },
    { id: 'face', title: 'Liveness Check', icon: Camera, loa: 'LoA 3' },
    { id: 'review', title: 'Manual Review', icon: Clock, loa: 'Final' },
  ];

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-12">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 mb-2">{t.identVerification}</h1>
          <div className="flex items-center gap-3">
             <span className="px-3 py-1 bg-indigo-100 text-indigo-700 text-[10px] font-bold rounded-full uppercase tracking-widest">{t.identityLevel}: 3</span>
             <p className="text-slate-500 text-sm">{t.loaTitle}: <span className="font-bold text-slate-900">High Assurance</span></p>
          </div>
        </div>
        <div className="bg-amber-50 border border-amber-100 p-4 rounded-2xl flex items-center gap-3 text-amber-700">
          <ShieldCheck className="w-6 h-6" />
          <div className="text-sm">
            <p className="font-bold">Encryption Active</p>
            <p className="opacity-80">E2EE Protocol Layer 7</p>
          </div>
        </div>
      </div>

      {/* Progress Pipeline */}
      <div className="grid grid-cols-4 gap-4 mb-12">
        {steps.map((s, i) => {
          const isActive = s.id === currentStep;
          const isDone = steps.findIndex(x => x.id === currentStep) > i;
          
          return (
            <div key={s.id} className="relative">
              <div className={cn(
                "h-1.5 rounded-full transition-all duration-500",
                isDone ? "bg-green-500" : isActive ? "bg-indigo-600" : "bg-slate-200"
              )} />
              <div className="mt-4 flex flex-col items-center text-center">
                <div className={cn(
                  "p-2 rounded-lg mb-2 transition-colors",
                  isDone ? "bg-green-100 text-green-600" : isActive ? "bg-indigo-100 text-indigo-600" : "bg-slate-50 text-slate-400"
                )}>
                  <s.icon className="w-5 h-5" />
                </div>
                <span className={cn(
                  "text-[10px] font-bold uppercase tracking-widest",
                  isActive ? "text-indigo-600" : "text-slate-400"
                )}>{s.title}</span>
                <span className="text-[8px] font-medium text-slate-300 mt-0.5">{s.loa}</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden min-h-[400px] flex flex-col">
        <div className="p-8 flex-1">
          <AnimatePresence mode="wait">
            {currentStep === 'biometric' && (
              <motion.div
                key="biometric"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="text-center space-y-8"
              >
                <div className="mx-auto w-32 h-32 bg-slate-50 rounded-3xl border-2 border-dashed border-slate-200 flex items-center justify-center text-slate-300 relative overflow-hidden group hover:border-indigo-600 transition-colors cursor-pointer">
                  <Fingerprint className="w-16 h-16 group-hover:text-indigo-600 transition-colors" />
                  <div className="absolute inset-0 bg-indigo-600/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
                <div className="max-w-md mx-auto">
                  <h3 className="text-xl font-bold text-slate-900 mb-2">Scan Your Fingerprint</h3>
                  <p className="text-slate-500 text-sm italic">Place your finger on the reader device or use the mobile app integration for biometric capture.</p>
                </div>
                <div className="p-4 bg-blue-50 text-blue-700 rounded-2xl flex items-start gap-3 text-left">
                  <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                  <p className="text-xs leading-relaxed font-medium">This encrypted template is never stored on our servers. It is compared directly with the National Register at hardware level.</p>
                </div>
              </motion.div>
            )}

            {currentStep === 'document' && (
              <motion.div
                key="doc"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="grid md:grid-cols-2 gap-8"
              >
                <div className="space-y-6">
                   <h3 className="text-xl font-bold text-slate-900">Document Authenticity</h3>
                   <p className="text-slate-500 text-sm">Please upload high-resolution photos of your National ID card (Front & Back).</p>
                   
                   <div className="space-y-3">
                     {['Front View', 'Back View'].map(label => (
                       <div key={label} className="p-4 bg-slate-50 border border-slate-200 rounded-2xl flex items-center justify-between">
                         <div className="flex items-center gap-3 text-slate-600">
                           <FileText className="w-5 h-5" />
                           <span className="font-bold text-sm tracking-wide uppercase">{label}</span>
                         </div>
                         <button className="bg-indigo-600 text-white px-4 py-2 rounded-xl text-xs font-bold">Upload</button>
                       </div>
                     ))}
                   </div>
                </div>
                <div className="bg-slate-900 rounded-2xl p-6 text-white flex flex-col justify-center items-center text-center space-y-4">
                  <Camera className="w-12 h-12 text-indigo-400" />
                  <p className="text-sm font-medium">Auto-align camera to capture ID with OCR enhancement</p>
                  <button className="w-full bg-white text-slate-900 py-3 rounded-xl font-bold">Launch Camera</button>
                </div>
              </motion.div>
            )}

            {currentStep === 'face' && (
              <motion.div
                key="face"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center space-y-8"
              >
                <div className="mx-auto w-48 h-48 rounded-full border-4 border-indigo-600 bg-slate-100 overflow-hidden flex items-center justify-center relative">
                  <img src="https://picsum.photos/seed/face/400/400" className="opacity-50 grayscale" alt="" referrerPolicy="no-referrer" />
                  <div className="absolute inset-0 bg-gradient-to-t from-indigo-900/40 to-transparent" />
                  <div className="absolute top-1/2 left-0 w-full h-0.5 bg-indigo-400 animate-scan" />
                  <Camera className="absolute w-12 h-12 text-white drop-shadow-lg" />
                </div>
                <div>
                   <h3 className="text-xl font-bold text-slate-900">Liveness Detection</h3>
                   <p className="text-slate-500 text-sm">Follow the on-screen prompts: Blink twice, then turn your head slowly to the left.</p>
                </div>
              </motion.div>
            )}

            {currentStep === 'review' && (
              <motion.div
                key="review"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center space-y-6 flex flex-col items-center py-12"
              >
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center text-green-600">
                  <CheckCircle2 className="w-10 h-10" />
                </div>
                <div>
                   <h3 className="text-2xl font-bold text-slate-900">Pending Government Review</h3>
                   <p className="text-slate-500 max-w-md">Your verification package has been submitted to the Ministry of Health. Average turnaround time: 2-4 hours.</p>
                </div>
                <div className="flex gap-4">
                  <span className="px-4 py-2 bg-slate-100 rounded-full text-xs font-bold text-slate-500 uppercase">BATCH #88219</span>
                  <span className="px-4 py-2 bg-indigo-100 rounded-full text-xs font-bold text-indigo-600 uppercase tracking-widest flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-pulse" />
                    Monitoring Status
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="p-6 bg-slate-50 border-t border-slate-100 flex justify-between items-center">
          <button 
             onClick={() => {
                const idx = steps.findIndex(x => x.id === currentStep);
                if(idx > 0) setCurrentStep(steps[idx-1].id);
             }}
             className="text-slate-500 font-bold text-sm"
          >
            {t.previousStep}
          </button>
          
          <button 
             onClick={() => {
                const idx = steps.findIndex(x => x.id === currentStep);
                if(idx < steps.length - 1) setCurrentStep(steps[idx+1].id);
             }}
             className="bg-indigo-600 text-white px-8 py-3 rounded-2xl font-bold flex items-center gap-2 hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100"
          >
            {currentStep === 'review' ? 'Finish' : t.nextStep} <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
