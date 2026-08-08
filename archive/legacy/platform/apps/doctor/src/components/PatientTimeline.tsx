import { useState } from 'react';
import { Card, CardHeader, CardBody, Badge } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import type { ClinicalTimelineEvent } from '../services/clinical';

interface PatientTimelineProps {
  events: ClinicalTimelineEvent[];
  onEventClick?: (event: ClinicalTimelineEvent) => void;
  maxEvents?: number;
}

const typeConfig: Record<string, {
  icon: string;
  color: string;
  bg: string;
}> = {
  visit: { icon: '🏥', color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-100 dark:bg-blue-900/20' },
  diagnosis: { icon: '📋', color: 'text-purple-600 dark:text-purple-400', bg: 'bg-purple-100 dark:bg-purple-900/20' },
  lab_result: { icon: '🔬', color: 'text-green-600 dark:text-green-400', bg: 'bg-green-100 dark:bg-green-900/20' },
  radiology: { icon: '📡', color: 'text-orange-600 dark:text-orange-400', bg: 'bg-orange-100 dark:bg-orange-900/20' },
  prescription: { icon: '💊', color: 'text-teal-600 dark:text-teal-400', bg: 'bg-teal-100 dark:bg-teal-900/20' },
  procedure: { icon: '🛠️', color: 'text-red-600 dark:text-red-400', bg: 'bg-red-100 dark:bg-red-900/20' },
  note: { icon: '📝', color: 'text-neutral-600 dark:text-neutral-400', bg: 'bg-neutral-100 dark:bg-neutral-900' },
  vaccination: { icon: '💉', color: 'text-indigo-600 dark:text-indigo-400', bg: 'bg-indigo-100 dark:bg-indigo-900/20' },
  allergy: { icon: '⚠️', color: 'text-warning-600 dark:text-warning-400', bg: 'bg-warning-100 dark:bg-warning-900/20' },
  admission: { icon: '🚪', color: 'text-red-600 dark:text-red-400', bg: 'bg-red-100 dark:bg-red-900/20' },
  discharge: { icon: '✅', color: 'text-green-600 dark:text-green-400', bg: 'bg-green-100 dark:bg-green-900/20' },
};

export function PatientTimeline({ events, onEventClick, maxEvents = 50 }: PatientTimelineProps) {
  const { isRtl } = useRTL();
  const [showAll, setShowAll] = useState(false);

  const sorted = [...events].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  const displayed = showAll ? sorted : sorted.slice(0, maxEvents);

  const groupedByDate = displayed.reduce<Record<string, ClinicalTimelineEvent[]>>((acc, event) => {
    const dateKey = new Date(event.date).toLocaleDateString(isRtl ? 'ar-IQ' : 'en-US', {
      year: 'numeric', month: 'long', day: 'numeric',
    });
    if (!acc[dateKey]) acc[dateKey] = [];
    acc[dateKey].push(event);
    return acc;
  }, {});

  if (events.length === 0) {
    return (
      <Card>
        <CardHeader title={isRtl ? 'التاريخ السريري' : 'Clinical History'} />
        <CardBody>
          <p className="text-sm text-neutral-500 text-center py-8">
            {isRtl ? 'لا توجد أحداث سريرية' : 'No clinical events'}
          </p>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader
        title={isRtl ? 'التاريخ السريري' : 'Clinical Timeline'}
        subtitle={`${events.length} ${isRtl ? 'حدث' : 'events'}`}
      />
      <CardBody>
        <div className="relative">
          <div className="absolute right-4 top-0 bottom-0 w-0.5 bg-neutral-200 dark:bg-neutral-700" />

          {Object.entries(groupedByDate).map(([dateKey, dateEvents]) => (
            <div key={dateKey} className="mb-6">
              <div className="sticky top-0 z-10 bg-white dark:bg-neutral-800 pb-2 pt-1">
                <span className="text-xs font-bold text-neutral-500 dark:text-neutral-400 bg-neutral-100 dark:bg-neutral-700 px-3 py-1 rounded-full">
                  {dateKey}
                </span>
              </div>

              <div className="space-y-3 mr-8">
                {dateEvents.map(event => {
                  const config = typeConfig[event.type] || typeConfig.note;
                  return (
                    <div
                      key={event.id}
                      onClick={() => onEventClick?.(event)}
                      className="relative flex items-start gap-3 p-3 rounded-xl bg-neutral-50 dark:bg-neutral-900 border border-neutral-100 dark:border-neutral-800 cursor-pointer hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors group"
                    >
                      <div className={`w-8 h-8 rounded-full ${config.bg} flex items-center justify-center text-sm shrink-0`}>
                        {config.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-sm text-neutral-900 dark:text-neutral-50">
                            {isRtl ? event.titleAr : event.title}
                          </p>
                          {event.severity === 'critical' && (
                            <Badge variant="danger" size="xs">{isRtl ? 'حرج' : 'Critical'}</Badge>
                          )}
                        </div>
                        {event.description && (
                          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5 line-clamp-2">
                            {isRtl ? (event.descriptionAr || event.description) : event.description}
                          </p>
                        )}
                        <p className="text-[10px] text-neutral-400 mt-1">
                          {new Date(event.date).toLocaleTimeString(isRtl ? 'ar-IQ' : 'en-US', {
                            hour: '2-digit', minute: '2-digit',
                          })}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {events.length > maxEvents && (
          <div className="text-center mt-4">
            <button
              onClick={() => setShowAll(!showAll)}
              className="text-sm text-primary-600 dark:text-primary-400 font-medium hover:underline"
            >
              {showAll
                ? (isRtl ? 'عرض أقل' : 'Show less')
                : (isRtl ? `عرض الكل (${events.length})` : `View all (${events.length})`)}
            </button>
          </div>
        )}
      </CardBody>
    </Card>
  );
}
