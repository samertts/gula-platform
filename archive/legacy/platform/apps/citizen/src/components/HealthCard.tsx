import { cn } from '@gula/ui-platform';
import type { CitizenUser } from '../types';

interface HealthCardProps {
  user: CitizenUser;
  qrData?: string;
  className?: string;
}

export function HealthCard({ user, qrData, className }: HealthCardProps) {
  const bloodTypeColors: Record<string, string> = {
    'A+': 'bg-red-500',
    'A-': 'bg-red-400',
    'B+': 'bg-blue-500',
    'B-': 'bg-blue-400',
    'AB+': 'bg-purple-500',
    'AB-': 'bg-purple-400',
    'O+': 'bg-green-500',
    'O-': 'bg-green-400',
  };

  return (
    <div className={cn('relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary-600 to-primary-900 text-white shadow-2xl', className)}>
      <div className="absolute top-0 right-0 w-48 h-48 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/4" />
      <div className="absolute bottom-0 left-0 w-32 h-32 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/4" />

      <div className="relative p-6 space-y-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/70">
              الهوية الصحية الوطنية
            </p>
            <h2 className="text-xl font-black mt-1 leading-tight">
              {user.name}
            </h2>
          </div>
          {user.bloodType && (
            <div className={cn(
              'w-12 h-12 rounded-2xl flex items-center justify-center text-white font-black text-lg shadow-lg',
              bloodTypeColors[user.bloodType] || 'bg-neutral-500',
            )}>
              {user.bloodType}
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-[9px] font-bold uppercase tracking-widest text-white/50">الرقم الوطني</p>
            <p className="text-sm font-bold mt-0.5">{user.nationalId.replace(/(\d{3})(\d{3})(\d{4})(\d{4})/, '$1-$2-$3-$4')}</p>
          </div>
          <div>
            <p className="text-[9px] font-bold uppercase tracking-widest text-white/50">الجنس</p>
            <p className="text-sm font-bold mt-0.5">{user.gender === 'male' ? 'ذكر' : 'أنثى'}</p>
          </div>
          <div>
            <p className="text-[9px] font-bold uppercase tracking-widest text-white/50">تاريخ الميلاد</p>
            <p className="text-sm font-bold mt-0.5">{new Date(user.dateOfBirth).toLocaleDateString('ar-IQ', { year: 'numeric', month: 'short', day: 'numeric' })}</p>
          </div>
          <div>
            <p className="text-[9px] font-bold uppercase tracking-widest text-white/50">مستوى التحقق</p>
            <p className="text-sm font-bold mt-0.5">
              {user.verificationLevel === 'Level_3' ? 'بيومتري' : user.verificationLevel === 'Level_2' ? 'موثق' : 'أساسي'}
            </p>
          </div>
        </div>

        {qrData && (
          <div className="flex justify-center pt-2">
            <div className="bg-white p-3 rounded-2xl">
              <img
                src={`https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(qrData)}`}
                alt="QR Code"
                className="w-28 h-28"
              />
            </div>
          </div>
        )}

        <div className="flex items-center justify-center gap-1.5">
          <svg className="w-4 h-4 text-white/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <rect x="2" y="5" width="20" height="14" rx="2" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2 10h20" />
            <circle cx="8" cy="14" r="1" fill="currentColor" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14h4" />
          </svg>
          <p className="text-[9px] font-bold text-white/50 uppercase tracking-[0.2em]">
            GULA National Health ID
          </p>
        </div>
      </div>
    </div>
  );
}
