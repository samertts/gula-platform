import { cn } from '@gula/ui-platform';
import type { BedAssignment } from '@/utils/types';

interface WardMapProps {
  beds: BedAssignment[];
  onBedClick?: (bed: BedAssignment) => void;
  className?: string;
  columns?: number;
}

const bedStatusColors: Record<string, string> = {
  occupied: 'bg-success-500 hover:bg-success-600 border-success-600',
  available: 'bg-neutral-200 dark:bg-neutral-600 hover:bg-neutral-300 dark:hover:bg-neutral-500 border-neutral-300 dark:border-neutral-500',
  cleaning: 'bg-warning-300 dark:bg-warning-700 hover:bg-warning-400 dark:hover:bg-warning-600 border-warning-400 dark:border-warning-600',
  maintenance: 'bg-danger-300 dark:bg-danger-700 hover:bg-danger-400 dark:hover:bg-danger-600 border-danger-400 dark:border-danger-600',
};

const isolationBadges: Record<string, string> = {
  contact: 'bg-yellow-500',
  airborne: 'bg-red-500',
  droplet: 'bg-blue-500',
  protective: 'bg-purple-500',
};

export function WardMap({ beds, onBedClick, className, columns = 4 }: WardMapProps) {
  const rows = [];
  for (let i = 0; i < beds.length; i += columns) {
    rows.push(beds.slice(i, i + columns));
  }

  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex items-center gap-4 text-xs flex-wrap">
        {[
          { color: 'bg-success-500', label: 'مشغول' },
          { color: 'bg-neutral-200 dark:bg-neutral-600', label: 'متاح' },
          { color: 'bg-warning-300 dark:bg-warning-700', label: 'تنظيف' },
          { color: 'bg-danger-300 dark:bg-danger-700', label: 'صيانة' },
        ].map(s => (
          <div key={s.label} className="flex items-center gap-1.5">
            <span className={cn('w-3 h-3 rounded', s.color)} />
            <span className="text-neutral-500 dark:text-neutral-400">{s.label}</span>
          </div>
        ))}
      </div>

      <div className="space-y-3">
        {rows.map((row, ri) => (
          <div key={ri} className="flex gap-3">
            {row.map(bed => (
              <button
                key={bed.bed}
                type="button"
                onClick={() => onBedClick?.(bed)}
                disabled={bed.status === 'maintenance'}
                className={cn(
                  'flex-1 p-3 rounded-2xl border-2 text-center transition-all min-w-0',
                  bedStatusColors[bed.status] || 'bg-neutral-200 dark:bg-neutral-600',
                  bed.isolation && 'ring-2 ring-yellow-500',
                )}
              >
                <div className="flex items-center justify-center gap-1 mb-1">
                  <span className="text-xs font-bold text-white drop-shadow-sm">
                    {bed.bed}
                  </span>
                  {bed.isolation && (
                    <span className={cn('w-2 h-2 rounded-full', isolationBadges[bed.isolation])} />
                  )}
                </div>
                {bed.status === 'occupied' && bed.patientName && (
                  <p className="text-[10px] text-white font-medium truncate">
                    {bed.patientName}
                  </p>
                )}
                {bed.status === 'available' && (
                  <p className="text-[10px] text-neutral-500 dark:text-neutral-400">متاح</p>
                )}
                {bed.status === 'cleaning' && (
                  <p className="text-[10px] text-white/70">تنظيف</p>
                )}
                {bed.status === 'maintenance' && (
                  <p className="text-[10px] text-white/70">صيانة</p>
                )}
              </button>
            ))}
            {row.length < columns && Array.from({ length: columns - row.length }).map((_, i) => (
              <div key={`empty-${i}`} className="flex-1" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
