import { useState, useEffect } from 'react';
import { Button, cn } from '@gula/ui-platform';
import { apiRequest } from '../services/api';
import type { TelemedicineSession } from '../types';

const statusLabels: Record<string, string> = {
  scheduled: 'مجدول',
  in_progress: 'قيد التنفيذ',
  completed: 'مكتمل',
  cancelled: 'ملغي',
};

const statusColors: Record<string, string> = {
  scheduled: 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400',
  in_progress: 'bg-success-100 text-success-700 dark:bg-success-900/30 dark:text-success-400',
  completed: 'bg-neutral-100 text-neutral-600',
  cancelled: 'bg-danger-100 text-danger-600',
};

export function Telemedicine() {
  const [sessions, setSessions] = useState<TelemedicineSession[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadSessions();
  }, []);

  async function loadSessions() {
    try {
      const response = await apiRequest<{ sessions: TelemedicineSession[] }>('/citizen/telemedicine');
      setSessions(response.sessions);
    } catch {} finally {
      setIsLoading(false);
    }
  }

  const upcomingSessions = sessions.filter(
    (s) => s.status === 'scheduled' || s.status === 'in_progress',
  );

  if (isLoading) {
    return (
      <div className="pb-24 px-4 pt-4 space-y-4">
        {[1, 2].map((i) => (
          <div key={i} className="bg-neutral-100 dark:bg-neutral-800 rounded-2xl h-32 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="pb-24 px-4 pt-4">
      <div className="bg-gradient-to-br from-primary-500 to-primary-700 text-white rounded-3xl p-6 mb-6 shadow-xl">
        <div className="flex items-center gap-3 mb-4">
          <svg className="w-8 h-8 text-white/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/70">الاستشارات عن بعد</p>
            <p className="text-lg font-black">Telemedicine</p>
          </div>
        </div>
        <p className="text-sm text-white/80">تواصل مع مقدمي الرعاية الصحية عبر الفيديو من منزلك</p>
        <Button
          className="mt-4 bg-white text-primary-600 hover:bg-white/90"
          onClick={() => {}}
        >
          حجز استشارة جديدة
        </Button>
      </div>

      {sessions.length === 0 ? (
        <div className="text-center py-16">
          <svg className="w-16 h-16 mx-auto text-neutral-300 dark:text-neutral-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <p className="text-sm text-neutral-500 mb-2">لا توجد استشارات سابقة</p>
          <p className="text-[10px] text-neutral-400">سيتم عرض جلسات الاستشارات عن بعد هنا</p>
        </div>
      ) : (
        <div className="space-y-4">
          {upcomingSessions.map((session) => (
            <div key={session.id} className="bg-white dark:bg-neutral-800 rounded-2xl p-5 border border-neutral-200 dark:border-neutral-700 shadow-sm">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-bold text-neutral-900 dark:text-neutral-50">{session.providerName}</h3>
                  <p className="text-xs text-neutral-500">{session.providerSpecialty}</p>
                </div>
                <span className={cn('px-2 py-0.5 rounded-lg text-[10px] font-bold', statusColors[session.status])}>
                  {statusLabels[session.status]}
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs text-neutral-500 mb-4">
                <span>{new Date(session.scheduledDate).toLocaleDateString('ar-IQ')}</span>
                <span className="w-1 h-1 rounded-full bg-neutral-300" />
                <span>{session.duration ? `${session.duration} دقيقة` : '-'}</span>
              </div>
              {session.status === 'scheduled' && (
                <div className="flex gap-2">
                  <Button
                    fullWidth
                    size="sm"
                    onClick={() => window.open(session.meetingUrl, '_blank')}
                  >
                    انضم الآن
                  </Button>
                </div>
              )}
              {session.notes && (
                <p className="mt-3 text-xs text-neutral-500 italic">{session.notes}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
