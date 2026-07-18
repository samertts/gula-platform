import { useMedicalHistory } from '../hooks/useHealthData';
import { HealthTimeline } from '../components/HealthTimeline';

export function MedicalHistory() {
  const { data: history, isLoading, error } = useMedicalHistory();

  if (isLoading) {
    return (
      <div className="pb-24 px-4 pt-4 space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-neutral-100 dark:bg-neutral-800 rounded-2xl h-24 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="pb-24 px-4 pt-4">
      {error && (
        <div className="mb-4 p-4 bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 rounded-2xl">
          <p className="text-xs text-danger-600 dark:text-danger-400">{error}</p>
        </div>
      )}
      <HealthTimeline records={history} />
    </div>
  );
}
