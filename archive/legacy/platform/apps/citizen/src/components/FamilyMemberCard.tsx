import { cn } from '@gula/ui-platform';
import type { FamilyMember } from '../types';

interface FamilyMemberCardProps {
  member: FamilyMember;
  onView?: (id: string) => void;
  onEdit?: (id: string) => void;
  onRemove?: (id: string) => void;
  className?: string;
}

const relationshipLabels: Record<string, string> = {
  spouse: 'زوج/زوجة',
  child: 'ابن/ابنة',
  parent: 'والد/والدة',
  sibling: 'أخ/أخت',
  other: 'آخر',
};

export function FamilyMemberCard({ member, onView, onEdit, onRemove, className }: FamilyMemberCardProps) {
  return (
    <div className={cn('bg-white dark:bg-neutral-800 rounded-2xl p-5 border border-neutral-200 dark:border-neutral-700 shadow-sm', className)}>
      <div className="flex items-center gap-4">
        <div className="w-14 h-14 rounded-2xl bg-primary-50 dark:bg-primary-900/30 flex items-center justify-center text-primary-600 dark:text-primary-400 font-black text-lg shrink-0">
          {member.name.charAt(0)}
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="font-black text-neutral-900 dark:text-neutral-50 truncate">
            {member.name}
          </h3>
          <p className="text-xs text-neutral-500 dark:text-neutral-400">
            {relationshipLabels[member.relationship] || member.relationship}
          </p>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-[10px] text-neutral-400">
              {member.gender === 'male' ? 'ذكر' : 'أنثى'}
            </span>
            <span className="w-1 h-1 rounded-full bg-neutral-300" />
            <span className="text-[10px] text-neutral-400">
              {new Date(member.dateOfBirth).toLocaleDateString('ar-IQ', { year: 'numeric', month: 'short', day: 'numeric' })}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {onView && (
            <button
              onClick={() => onView(member.id)}
              className="w-9 h-9 flex items-center justify-center rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-500"
              aria-label="عرض"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </button>
          )}
          {onEdit && (
            <button
              onClick={() => onEdit(member.id)}
              className="w-9 h-9 flex items-center justify-center rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-500"
              aria-label="تعديل"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
          )}
          {onRemove && (
            <button
              onClick={() => onRemove(member.id)}
              className="w-9 h-9 flex items-center justify-center rounded-xl hover:bg-danger-50 dark:hover:bg-danger-900/30 text-neutral-400 hover:text-danger-500"
              aria-label="حذف"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          )}
        </div>
      </div>

      <div className="flex items-center gap-4 mt-4 pt-4 border-t border-neutral-100 dark:border-neutral-700">
        <div className="flex items-center gap-1.5">
          <div className={cn('w-2 h-2 rounded-full', member.canViewRecords ? 'bg-success-500' : 'bg-neutral-300')} />
          <span className="text-[10px] font-bold text-neutral-500">
            {member.canViewRecords ? 'مشاهدة السجلات' : 'لا يمكن المشاهدة'}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className={cn('w-2 h-2 rounded-full', member.canBookAppointments ? 'bg-success-500' : 'bg-neutral-300')} />
          <span className="text-[10px] font-bold text-neutral-500">
            {member.canBookAppointments ? 'حجز المواعيد' : 'لا يمكن الحجز'}
          </span>
        </div>
      </div>
    </div>
  );
}
