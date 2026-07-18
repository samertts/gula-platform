import { cn } from '@gula/ui-platform';
import type { CarePlan } from '@/utils/types';

interface CarePlanCardProps {
  plan: CarePlan;
  onClick?: () => void;
}

const statusColors: Record<string, string> = {
  active: 'bg-success-100 text-success-700 dark:bg-success-900/30 dark:text-success-400 border-success-300 dark:border-success-700',
  completed: 'bg-neutral-100 text-neutral-600 dark:bg-neutral-700 dark:text-neutral-400 border-neutral-300 dark:border-neutral-600',
  revised: 'bg-warning-100 text-warning-700 dark:bg-warning-900/30 dark:text-warning-400 border-warning-300 dark:border-warning-700',
};

export function CarePlanCard({ plan, onClick }: CarePlanCardProps) {
  const totalGoals = plan.goals.length;
  const achievedGoals = plan.goals.filter(g => g.status === 'achieved').length;
  const progress = totalGoals > 0 ? Math.round((achievedGoals / totalGoals) * 100) : 0;

  const activeInterventions = plan.interventions.filter(i => i.status === 'active').length;

  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full text-right bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 p-4 hover:shadow-md transition-all duration-200 space-y-4"
    >
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <h3 className="font-bold text-neutral-900 dark:text-neutral-100 truncate">{plan.patientName}</h3>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">{plan.diagnosis}</p>
        </div>
        <span className={cn('text-[10px] px-2 py-0.5 rounded-lg font-bold border', statusColors[plan.status])}>
          {plan.status === 'active' ? 'نشط' : plan.status === 'completed' ? 'مكتمل' : 'مُراجع'}
        </span>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between text-xs">
          <span className="text-neutral-500 dark:text-neutral-400">تقدم الأهداف</span>
          <span className="font-bold text-neutral-700 dark:text-neutral-300">{achievedGoals}/{totalGoals}</span>
        </div>
        <div className="h-2 bg-neutral-100 dark:bg-neutral-700 rounded-full overflow-hidden">
          <div
            className={cn(
              'h-full rounded-full transition-all duration-500',
              progress === 100 ? 'bg-success-500' : progress > 50 ? 'bg-primary-500' : 'bg-warning-500',
            )}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className="bg-neutral-50 dark:bg-neutral-700/50 p-2.5 rounded-xl">
          <p className="text-[10px] text-neutral-400 dark:text-neutral-500">التدخلات النشطة</p>
          <p className="text-lg font-black text-neutral-800 dark:text-neutral-200">{activeInterventions}</p>
        </div>
        <div className="bg-neutral-50 dark:bg-neutral-700/50 p-2.5 rounded-xl">
          <p className="text-[10px] text-neutral-400 dark:text-neutral-500">تاريخ المراجعة</p>
          <p className="text-sm font-bold text-neutral-800 dark:text-neutral-200">
            {new Date(plan.reviewDate).toLocaleDateString('ar-IQ')}
          </p>
        </div>
      </div>

      {plan.goals.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-[10px] font-bold text-neutral-500 dark:text-neutral-400">الأهداف</p>
          {plan.goals.slice(0, 3).map(goal => (
            <div key={goal.id} className="flex items-start gap-2">
              <span className={cn(
                'w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0 mt-0.5 text-[8px] font-bold',
                goal.status === 'achieved'
                  ? 'bg-success-500 border-success-500 text-white'
                  : goal.status === 'revised'
                    ? 'bg-warning-500 border-warning-500 text-white'
                    : 'border-neutral-300 dark:border-neutral-600',
              )}>
                {goal.status === 'achieved' ? '✓' : goal.status === 'revised' ? '!' : ''}
              </span>
              <span className="text-xs text-neutral-600 dark:text-neutral-400">{goal.description}</span>
            </div>
          ))}
          {plan.goals.length > 3 && (
            <p className="text-[10px] text-primary-500">+{plan.goals.length - 3} أهداف أخرى</p>
          )}
        </div>
      )}
    </button>
  );
}
