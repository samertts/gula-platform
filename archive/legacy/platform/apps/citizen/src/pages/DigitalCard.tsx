import { useState } from 'react';
import { Button, cn } from '@gula/ui-platform';
import { useAuth } from '../contexts/AuthContext';

export function DigitalCard() {
  const { user } = useAuth();
  const [isFlipped, setIsFlipped] = useState(false);

  if (!user) return null;

  return (
    <div className="pb-24 px-4 pt-4">
      <div className="perspective-1000 mb-6">
        <div
          className={cn(
            'relative transition-transform duration-500 cursor-pointer',
            'transform-style-preserve-3d',
            isFlipped && 'rotate-y-180',
          )}
          style={{ minHeight: '320px' }}
          onClick={() => setIsFlipped(!isFlipped)}
        >
          <div className="absolute inset-0 backface-hidden">
            <div className="h-full bg-gradient-to-br from-primary-600 via-primary-700 to-primary-900 rounded-3xl p-6 text-white shadow-2xl flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-6">
                  <svg className="w-8 h-8 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  <span className="text-[10px] font-bold uppercase tracking-widest text-white/50">صحي</span>
                </div>
                <h2 className="text-xl font-black mb-1">{user.name}</h2>
                <p className="text-sm text-white/70 font-medium">
                  {user.nationalId.replace(/(\d{3})(\d{3})(\d{4})(\d{4})/, '$1-$2-$3-$4')}
                </p>
              </div>
              <div className="flex items-end justify-between">
                <div>
                  <p className="text-[9px] font-bold uppercase tracking-widest text-white/50">تاريخ الميلاد</p>
                  <p className="text-sm font-bold">
                    {new Date(user.dateOfBirth).toLocaleDateString('ar-IQ', { year: 'numeric', month: 'short', day: 'numeric' })}
                  </p>
                </div>
                <p className="text-[9px] font-bold uppercase tracking-widest text-white/50">
                  اضغط للقلب
                </p>
              </div>
            </div>
          </div>

          <div className="absolute inset-0 backface-hidden rotate-y-180">
            <div className="h-full bg-gradient-to-br from-neutral-800 to-neutral-900 rounded-3xl p-6 text-white shadow-2xl flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-6">
                  <svg className="w-6 h-6 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <rect x="3" y="3" width="18" height="18" rx="2" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9h18" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 21V9" />
                  </svg>
                  <span className="text-[10px] font-bold uppercase tracking-widest text-white/50">باركود</span>
                </div>
                <div className="flex justify-center mb-4">
                  <div className="bg-white p-3 rounded-2xl">
                    <div className="w-40 h-40 bg-neutral-200 flex items-center justify-center rounded-xl">
                      <span className="text-neutral-400 text-xs font-bold">QR</span>
                    </div>
                  </div>
                </div>
                <p className="text-center text-[10px] text-white/50 font-bold">
                  امسح الرمز للتحقق من الهوية
                </p>
              </div>
              <p className="text-[9px] font-bold uppercase tracking-widest text-white/50 text-center">
                اضغط للعودة
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <Button fullWidth size="lg" variant="primary">
          مشاركة البطاقة
        </Button>
        <Button fullWidth size="lg" variant="outline">
          حفظ نسخة رقمية
        </Button>
      </div>

      <style>{`
        .perspective-1000 { perspective: 1000px; }
        .transform-style-preserve-3d { transform-style: preserve-3d; }
        .backface-hidden { backface-visibility: hidden; }
        .rotate-y-180 { transform: rotateY(180deg); }
      `}</style>
    </div>
  );
}
