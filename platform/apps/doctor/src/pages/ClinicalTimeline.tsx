import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { LayoutContent, LoadingSpinner, Card, CardHeader, CardBody, Button, Badge } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import { PatientTimeline } from '../components/PatientTimeline';
import { getClinicalTimeline, type ClinicalTimelineEvent } from '../services/clinical';

export function ClinicalTimeline() {
  const { patientId } = useParams<{ patientId: string }>();
  const { isRtl } = useRTL();
  const navigate = useNavigate();
  const [events, setEvents] = useState<ClinicalTimelineEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    if (!patientId) return;
    setIsLoading(true);
    getClinicalTimeline(patientId)
      .then(setEvents)
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, [patientId]);

  const filteredEvents = filter === 'all' ? events : events.filter(e => e.type === filter);

  const filterTypes = [
    { value: 'all', label: isRtl ? 'الكل' : 'All' },
    { value: 'visit', label: isRtl ? 'زيارات' : 'Visits' },
    { value: 'diagnosis', label: isRtl ? 'تشخيصات' : 'Diagnoses' },
    { value: 'lab_result', label: isRtl ? 'مختبر' : 'Lab' },
    { value: 'prescription', label: isRtl ? 'أدوية' : 'Medications' },
    { value: 'radiology', label: isRtl ? 'أشعة' : 'Radiology' },
  ];

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="p-2 rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-800">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d={isRtl ? "M19 12H5M12 19l-7-7 7-7" : "M5 12h14M12 5l7 7-7 7"} />
            </svg>
          </button>
          <div>
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
              {isRtl ? 'التاريخ السريري' : 'Clinical Timeline'}
            </h1>
            <p className="text-sm text-neutral-500">
              {isRtl ? 'السجل السريري الكامل للمريض' : 'Complete patient clinical history'}
            </p>
          </div>
        </div>

        <div className="flex gap-2 overflow-x-auto pb-2">
          {filterTypes.map(ft => (
            <button
              key={ft.value}
              onClick={() => setFilter(ft.value)}
              className={`shrink-0 px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                filter === ft.value
                  ? 'bg-primary-500 text-white shadow-sm'
                  : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-700'
              }`}
            >
              {ft.label}
            </button>
          ))}
        </div>

        <PatientTimeline events={filteredEvents} onEventClick={(event) => {}} maxEvents={100} />
      </div>
    </LayoutContent>
  );
}
