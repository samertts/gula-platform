import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardBody, Button, Badge, LayoutContent, Input } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';

interface VisitRecord {
  id: string;
  date: string;
  type: string;
  typeAr: string;
  chiefComplaint: string;
  chiefComplaintAr: string;
  diagnosis: string;
  diagnosisAr: string;
  doctor: string;
  status: string;
  statusAr: string;
}

const MOCK_VISITS: VisitRecord[] = [
  { id: 'v1', date: '2024-12-15T09:30:00', type: 'follow_up', typeAr: 'متابعة', chiefComplaint: 'Chest pain', chiefComplaintAr: 'ألم في الصدر', diagnosis: 'Angina', diagnosisAr: 'ذبحة صدرية', doctor: 'Dr. Ali', status: 'completed', statusAr: 'مكتمل' },
  { id: 'v2', date: '2024-11-20T14:00:00', type: 'outpatient', typeAr: 'عيادة خارجية', chiefComplaint: 'Dizziness', chiefComplaintAr: 'دوخة', diagnosis: 'Orthostatic hypotension', diagnosisAr: 'انخفاض ضغط انتصابي', doctor: 'Dr. Sara', status: 'completed', statusAr: 'مكتمل' },
  { id: 'v3', date: '2024-10-05T11:15:00', type: 'emergency', typeAr: 'طوارئ', chiefComplaint: 'Severe headache', chiefComplaintAr: 'صداع شديد', diagnosis: 'Migraine', diagnosisAr: 'شقيقة', doctor: 'Dr. Ahmed', status: 'completed', statusAr: 'مكتمل' },
];

export function Visits() {
  const { isRtl } = useRTL();
  const navigate = useNavigate();
  const [visits] = useState<VisitRecord[]>(MOCK_VISITS);

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={() => navigate(-1)} className="p-2 rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-800">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d={isRtl ? "M19 12H5M12 19l-7-7 7-7" : "M5 12h14M12 5l7 7-7 7"} />
              </svg>
            </button>
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
              {isRtl ? 'الزيارات' : 'Visits'}
            </h1>
          </div>
          <Button variant="primary">{isRtl ? 'زيارة جديدة' : 'New Visit'}</Button>
        </div>

        <div className="space-y-3">
          {visits.map(visit => (
            <Card key={visit.id} hover padding="md" onClick={() => {}}>
              <CardBody>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant={visit.type === 'emergency' ? 'danger' : visit.type === 'follow_up' ? 'info' : 'default'} size="sm">
                        {isRtl ? visit.typeAr : visit.type}
                      </Badge>
                      <span className="text-xs text-neutral-400">
                        {new Date(visit.date).toLocaleDateString(isRtl ? 'ar-IQ' : 'en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <p className="font-medium text-sm text-neutral-900 dark:text-neutral-50">
                      {isRtl ? visit.chiefComplaintAr : visit.chiefComplaint}
                    </p>
                    <p className="text-xs text-neutral-500 mt-0.5">
                      {isRtl ? 'التشخيص' : 'Diagnosis'}: {isRtl ? visit.diagnosisAr : visit.diagnosis}
                    </p>
                    <p className="text-xs text-neutral-400 mt-1">{visit.doctor}</p>
                  </div>
                  <Badge variant={visit.status === 'completed' ? 'success' : 'warning'}>{isRtl ? visit.statusAr : visit.status}</Badge>
                </div>
              </CardBody>
            </Card>
          ))}
          {visits.length === 0 && (
            <p className="text-sm text-neutral-500 text-center py-8">{isRtl ? 'لا توجد زيارات' : 'No visits'}</p>
          )}
        </div>
      </div>
    </LayoutContent>
  );
}
