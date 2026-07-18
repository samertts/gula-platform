import { cn } from '@gula/ui-platform';
import type { SampleStatus, SpecimenType } from '@/utils/types';

interface SampleTubeProps {
  status: SampleStatus;
  specimenType: SpecimenType;
  volume?: number;
  priority?: 'routine' | 'urgent' | 'stat';
  sampleId?: string;
  patientName?: string;
  selected?: boolean;
  onClick?: () => void;
  className?: string;
}

const volumeColors: Record<string, string> = {
  whole_blood: 'from-red-500 to-red-600',
  serum: 'from-amber-300 to-amber-400',
  plasma: 'from-yellow-300 to-yellow-400',
  urine: 'from-yellow-200 to-yellow-300',
  stool: 'from-amber-700 to-amber-800',
  csf: 'from-blue-100 to-blue-200',
  sputum: 'from-green-200 to-green-300',
  swab: 'from-blue-200 to-blue-300',
  tissue: 'from-red-300 to-red-400',
  bone_marrow: 'from-red-400 to-red-500',
  amniotic: 'from-blue-100 to-blue-200',
  pleural: 'from-blue-100 to-blue-200',
  pericardial: 'from-blue-100 to-blue-200',
  peritoneal: 'from-blue-100 to-blue-200',
  synovial: 'from-amber-100 to-amber-200',
  saliva: 'from-blue-50 to-blue-100',
  hair: 'from-neutral-400 to-neutral-500',
  nail: 'from-neutral-300 to-neutral-400',
  other: 'from-neutral-400 to-neutral-500',
};

const priorityBorder: Record<string, string> = {
  routine: 'border-neutral-300 dark:border-neutral-600',
  urgent: 'border-warning-400 dark:border-warning-500',
  stat: 'border-danger-500 dark:border-danger-400 animate-pulse',
};

const statusLabel: Record<string, string> = {
  ordered: 'مطلوب',
  registered: 'مسجل',
  collected: 'مجموع',
  transporting: 'قيد النقل',
  received: 'مستلم',
  accepted: 'مقبول',
  rejected: 'مرفوض',
  aliquoted: 'مقسم',
  processing: 'قيد المعالجة',
  analyzing: 'قيد التحليل',
  analyzed: 'تم التحليل',
  verified: 'تم التحقق',
  validated: 'معتمد',
  released: 'منشور',
  archived: 'مؤرشف',
  disposed: 'تم التخلص',
};

export function SampleTube({
  status,
  specimenType,
  volume,
  priority = 'routine',
  sampleId,
  patientName,
  selected,
  onClick,
  className,
}: SampleTubeProps) {
  const fillPercent = volume ? Math.min(volume / 10, 1) * 100 : 60;

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'relative flex flex-col items-center gap-1.5 p-3 rounded-2xl border-2 transition-all duration-200',
        'hover:shadow-md hover:scale-105 active:scale-95',
        'focus:outline-none focus-visible:ring-4 focus-visible:ring-primary-200',
        priorityBorder[priority],
        selected && 'ring-4 ring-primary-400 bg-primary-50 dark:bg-primary-900/30',
        !selected && 'bg-white dark:bg-neutral-800',
        className,
      )}
    >
      <div className="relative w-12 h-20">
        <svg viewBox="0 0 48 80" className="w-full h-full">
          <defs>
            <clipPath id="tube-clip">
              <path d="M16 0h16c4 0 8 4 8 8v52c0 6-4 10-8 14l-2 2c-2 2-4 4-4 4s-2-2-4-4l-2-2c-4-4-8-8-8-14V8c0-4 4-8 8-8z" />
            </clipPath>
          </defs>

          <path
            d="M16 0h16c4 0 8 4 8 8v52c0 6-4 10-8 14l-2 2c-2 2-4 4-4 4s-2-2-4-4l-2-2c-4-4-8-8-8-14V8c0-4 4-8 8-8z"
            fill="none"
            stroke={selected ? '#6366f1' : '#cbd5e1'}
            strokeWidth="1.5"
            className="dark:stroke-neutral-600"
          />

          <rect
            x="17"
            y={72 - fillPercent * 0.66}
            width="14"
            height={fillPercent * 0.66}
            fill={`url(#${specimenType})`}
            clipPath="url(#tube-clip)"
            rx="1"
          />
        </svg>
        <defs>
          <linearGradient id={specimenType} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#fff" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#000" stopOpacity="0.1" />
          </linearGradient>
        </defs>

        <div
          className={cn(
            'absolute inset-x-0 bottom-0 rounded-b-lg transition-all',
            volumeColors[specimenType] || 'from-neutral-400 to-neutral-500',
          )}
          style={{
            height: `${fillPercent}%`,
            opacity: 0.85,
            maskImage: 'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 48 80\'%3E%3Cpath d=\'M16 0h16c4 0 8 4 8 8v52c0 6-4 10-8 14l-2 2c-2 2-4 4-4 4s-2-2-4-4l-2-2c-4-4-8-8-8-14V8c0-4 4-8 8-8z\'/%3E%3C/svg%3E")',
            WebkitMaskSize: '100% 100%',
            maskSize: '100% 100%',
          }}
        />
      </div>

      <span className="text-[9px] font-black text-neutral-400 dark:text-neutral-500 uppercase tracking-wider">
        {priority === 'stat' ? 'STAT' : priority === 'urgent' ? 'عاجل' : 'روتين'}
      </span>

      {sampleId && (
        <span className="text-[10px] font-mono font-bold text-neutral-600 dark:text-neutral-400 truncate max-w-[80px]">
          {sampleId}
        </span>
      )}

      {patientName && (
        <span className="text-[9px] text-neutral-500 dark:text-neutral-500 truncate max-w-[80px]">
          {patientName}
        </span>
      )}

      <span className={cn(
        'text-[8px] font-black px-1.5 py-0.5 rounded-md',
        status === 'rejected' ? 'bg-danger-50 text-danger-600 dark:bg-danger-900/30 dark:text-danger-400' :
        status === 'verified' || status === 'validated' ? 'bg-success-50 text-success-600 dark:bg-success-900/30 dark:text-success-400' :
        status === 'processing' || status === 'analyzing' ? 'bg-warning-50 text-warning-600 dark:bg-warning-900/30 dark:text-warning-400' :
        'bg-neutral-100 text-neutral-500 dark:bg-neutral-700 dark:text-neutral-400',
      )}>
        {statusLabel[status] || status}
      </span>
    </button>
  );
}
