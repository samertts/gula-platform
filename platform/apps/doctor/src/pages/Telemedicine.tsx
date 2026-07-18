import { useState } from 'react';
import { Card, CardHeader, CardBody, Button, Badge, LayoutContent } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';

interface Consultation {
  id: string;
  patientName: string;
  patientNameAr: string;
  type: 'video' | 'audio' | 'chat';
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled';
  date: string;
  duration: number;
  chiefComplaint: string;
  chiefComplaintAr: string;
}

const MOCK_CONSULTATIONS: Consultation[] = [
  { id: 'c1', patientName: 'Ahmed Ali', patientNameAr: 'أحمد علي', type: 'video', status: 'scheduled', date: '2024-12-16T10:00:00', duration: 30, chiefComplaint: 'Follow up on blood pressure', chiefComplaintAr: 'متابعة ضغط الدم' },
  { id: 'c2', patientName: 'Sara Mohammed', patientNameAr: 'سارة محمد', type: 'video', status: 'in_progress', date: '2024-12-15T14:00:00', duration: 45, chiefComplaint: 'Diabetes management', chiefComplaintAr: 'إدارة السكري' },
  { id: 'c3', patientName: 'Hassan Ibrahim', patientNameAr: 'حسن إبراهيم', type: 'chat', status: 'completed', date: '2024-12-14T09:00:00', duration: 20, chiefComplaint: 'Medication refill', chiefComplaintAr: 'إعادة صرف دواء' },
];

export function Telemedicine() {
  const { isRtl } = useRTL();
  const [consultations] = useState(MOCK_CONSULTATIONS);

  const typeIcons: Record<string, string> = { video: '📹', audio: '🎧', chat: '💬' };
  const statusColors: Record<string, 'success' | 'warning' | 'info' | 'danger'> = {
    scheduled: 'info',
    in_progress: 'success',
    completed: 'default',
    cancelled: 'danger',
  };

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
            {isRtl ? 'الاستشارات عن بعد' : 'Telemedicine'}
          </h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            {isRtl ? 'استشارات المرضى عن بعد عبر الفيديو أو الصوت أو المحادثة' : 'Remote patient consultations via video, audio, or chat'}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center gap-3 p-4 rounded-xl bg-primary-50 dark:bg-primary-950 border border-primary-100 dark:border-primary-900">
            <span className="text-2xl">📹</span>
            <div>
              <p className="text-lg font-bold">{consultations.filter(c => c.type === 'video').length}</p>
              <p className="text-xs text-neutral-500">{isRtl ? 'فيديو' : 'Video'}</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-4 rounded-xl bg-success-50 dark:bg-success-950 border border-success-100 dark:border-success-900">
            <span className="text-2xl">🎧</span>
            <div>
              <p className="text-lg font-bold">{consultations.filter(c => c.type === 'audio').length}</p>
              <p className="text-xs text-neutral-500">{isRtl ? 'صوت' : 'Audio'}</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-4 rounded-xl bg-warning-50 dark:bg-warning-950 border border-warning-100 dark:border-warning-900">
            <span className="text-2xl">💬</span>
            <div>
              <p className="text-lg font-bold">{consultations.filter(c => c.type === 'chat').length}</p>
              <p className="text-xs text-neutral-500">{isRtl ? 'محادثة' : 'Chat'}</p>
            </div>
          </div>
        </div>

        <div className="space-y-3">
          {consultations.map(consult => (
            <Card key={consult.id} padding="md">
              <CardBody>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{typeIcons[consult.type]}</span>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-sm">{isRtl ? consult.patientNameAr : consult.patientName}</p>
                        <Badge variant={statusColors[consult.status]} size="xs">
                          {consult.status === 'scheduled' ? (isRtl ? 'مجدول' : 'Scheduled') :
                           consult.status === 'in_progress' ? (isRtl ? 'قيد التشغيل' : 'In Progress') :
                           consult.status === 'completed' ? (isRtl ? 'مكتمل' : 'Completed') :
                           (isRtl ? 'ملغي' : 'Cancelled')}
                        </Badge>
                      </div>
                      <p className="text-xs text-neutral-500">{isRtl ? consult.chiefComplaintAr : consult.chiefComplaint}</p>
                      <p className="text-xs text-neutral-400 mt-0.5">
                        {new Date(consult.date).toLocaleDateString(isRtl ? 'ar-IQ' : 'en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                        {' | '}{consult.duration} min
                      </p>
                    </div>
                  </div>
                  {consult.status === 'in_progress' && (
                    <Button variant="primary" size="sm">
                      {isRtl ? 'انضمام' : 'Join'}
                    </Button>
                  )}
                  {consult.status === 'scheduled' && (
                    <Button variant="outline" size="sm">
                      {isRtl ? 'بدء' : 'Start'}
                    </Button>
                  )}
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      </div>
    </LayoutContent>
  );
}
