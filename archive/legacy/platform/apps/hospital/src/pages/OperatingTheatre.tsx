import { useState } from 'react';
import {
  Card, CardHeader, CardBody, Badge, Button, Select, LayoutContent, useRTL,
} from '@gula/ui-platform';

interface SurgerySchedule {
  id: string;
  patientName: string;
  patientNameAr: string;
  procedure: string;
  procedureAr: string;
  surgeon: string;
  surgeonAr: string;
  anaesthetist: string;
  anaesthetistAr: string;
  theatre: string;
  date: string;
  startTime: string;
  estimatedDuration: number;
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled' | 'delayed';
  priority: 'elective' | 'urgent' | 'emergency';
  notes: string;
}

const MOCK_SURGERIES: SurgerySchedule[] = [
  { id: '1', patientName: 'Ali Hassan', patientNameAr: 'علي حسن', procedure: 'Laparoscopic Cholecystectomy', procedureAr: 'استئصال المرارة بالمنظار', surgeonAr: 'د. خالد العاني', anaesthetistAr: 'د. محمد سامي', theatre: 'OT-1', date: '2026-07-16', startTime: '08:00', estimatedDuration: 120, status: 'scheduled', priority: 'elective', notes: '' },
  { id: '2', patientName: 'Zainab Noor', patientNameAr: 'زينب نور', procedure: 'C-Section', procedureAr: 'ولادة قيصرية', surgeonAr: 'د. ليلى رشيد', anaesthetistAr: 'د. أحمد جاسم', theatre: 'OT-2', date: '2026-07-16', startTime: '09:00', estimatedDuration: 90, status: 'scheduled', priority: 'urgent', notes: '' },
  { id: '3', patientName: 'Mohammed Ali', patientNameAr: 'محمد علي', procedure: 'Open Appendectomy', procedureAr: 'استئصال الزائدة الدودية', surgeonAr: 'د. خالد العاني', anaesthetistAr: 'د. محمد سامي', theatre: 'OT-1', date: '2026-07-16', startTime: '10:30', estimatedDuration: 75, status: 'scheduled', priority: 'emergency', notes: '' },
  { id: '4', patientName: 'Huda Karim', patientNameAr: 'هدى كريم', procedure: 'Hysteroscopy', procedureAr: 'تنظير الرحم', surgeonAr: 'د. ليلى رشيد', anaesthetistAr: 'د. سارة نور', theatre: 'OT-3', date: '2026-07-16', startTime: '11:00', estimatedDuration: 60, status: 'in_progress', priority: 'elective', notes: '' },
  { id: '5', patientName: 'Qasim Yousif', patientNameAr: 'قاسم يوسف', procedure: 'Hernia Repair', procedureAr: 'إصلاح فتق', surgeonAr: 'د. سامر جبوري', anaesthetistAr: 'د. محمد سامي', theatre: 'OT-2', date: '2026-07-16', startTime: '13:00', estimatedDuration: 90, status: 'scheduled', priority: 'elective', notes: '' },
  { id: '6', patientName: 'Layla Abbas', patientNameAr: 'ليلى عباس', procedure: 'Knee Replacement', procedureAr: 'استبدال الركبة', surgeonAr: 'د. قاسم العبيدي', anaesthetistAr: 'د. أحمد جاسم', theatre: 'OT-1', date: '2026-07-16', startTime: '14:00', estimatedDuration: 150, status: 'scheduled', priority: 'elective', notes: '' },
  { id: '7', patientName: 'Rami Jassim', patientNameAr: 'رامي جاسم', procedure: 'Emergency Laparotomy', procedureAr: 'فتح البطن الاستعجالي', surgeonAr: 'د. خالد العاني', anaesthetistAr: 'د. محمد سامي', theatre: 'OT-3', date: '2026-07-16', startTime: '15:30', estimatedDuration: 120, status: 'scheduled', priority: 'emergency', notes: '' },
  { id: '8', patientName: 'Sara Mohammed', patientNameAr: 'سارة محمد', procedure: 'Tonsillectomy', procedureAr: 'استئصال اللوزتين', surgeonAr: 'د. مريم الكاظمي', anaesthetistAr: 'د. سارة نور', theatre: 'OT-2', date: '2026-07-16', startTime: '08:30', estimatedDuration: 60, status: 'completed', priority: 'elective', notes: '' },
];

export function OperatingTheatre() {
  const { isRtl } = useRTL();
  const [surgeries] = useState(MOCK_SURGERIES);
  const [filterStatus, setFilterStatus] = useState('all');

  const filtered = filterStatus === 'all' ? surgeries : surgeries.filter(s => s.status === filterStatus);

  const statusColors: Record<string, 'warning' | 'success' | 'danger' | 'info' | 'primary'> = {
    scheduled: 'primary',
    in_progress: 'warning',
    completed: 'success',
    cancelled: 'danger',
    delayed: 'info',
  };

  const priorityColors: Record<string, 'success' | 'warning' | 'danger'> = {
    elective: 'success',
    urgent: 'warning',
    emergency: 'danger',
  };

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
              {isRtl ? 'غرف العمليات' : 'Operating Theatre'}
            </h1>
            <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
              {isRtl ? 'جدولة وإدارة غرف العمليات الجراحية' : 'Surgical theatre scheduling and management'}
            </p>
          </div>
          <Button>{isRtl ? 'إضافة عملية' : 'Add Surgery'}</Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { label: 'مجدول', labelEn: 'Scheduled', value: surgeries.filter(s => s.status === 'scheduled').length, color: 'bg-blue-500' },
            { label: 'قيد الإجراء', labelEn: 'In Progress', value: surgeries.filter(s => s.status === 'in_progress').length, color: 'bg-yellow-500' },
            { label: 'مكتملة', labelEn: 'Completed', value: surgeries.filter(s => s.status === 'completed').length, color: 'bg-green-500' },
            { label: 'غرف العمليات', labelEn: 'OT Rooms', value: 3, color: 'bg-purple-500' },
          ].map(s => (
            <Card key={s.label} variant="elevated" padding="md">
              <CardBody>
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${s.color}`} />
                  <div>
                    <p className="text-sm text-neutral-500">{isRtl ? s.label : s.labelEn}</p>
                    <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">{s.value}</p>
                  </div>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>

        <Card>
          <CardHeader
            title={isRtl ? 'جدول العمليات' : 'Surgery Schedule'}
            action={
              <Select
                value={filterStatus}
                onChange={v => setFilterStatus(v as string)}
                options={[
                  { value: 'all', label: isRtl ? 'الكل' : 'All' },
                  { value: 'scheduled', label: isRtl ? 'مجدول' : 'Scheduled' },
                  { value: 'in_progress', label: isRtl ? 'قيد الإجراء' : 'In Progress' },
                  { value: 'completed', label: isRtl ? 'مكتمل' : 'Completed' },
                  { value: 'cancelled', label: isRtl ? 'ملغي' : 'Cancelled' },
                ]}
                className="w-36"
              />
            }
          />
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-neutral-200 dark:border-neutral-700">
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الوقت' : 'Time'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'المريض' : 'Patient'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الإجراء' : 'Procedure'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الجراح' : 'Surgeon'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الغرفة' : 'OT'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'المدة' : 'Duration'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الأولوية' : 'Priority'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الحالة' : 'Status'}</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(s => (
                    <tr key={s.id} className="border-b border-neutral-100 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800/50">
                      <td className="p-3 font-medium">{s.startTime}</td>
                      <td className="p-3">
                        <p className="font-medium text-neutral-900 dark:text-neutral-50">{isRtl ? s.patientNameAr : s.patientName}</p>
                      </td>
                      <td className="p-3 text-neutral-700 dark:text-neutral-300">{isRtl ? s.procedureAr : s.procedure}</td>
                      <td className="p-3 text-sm text-neutral-500">{isRtl ? s.surgeonAr : s.surgeon}</td>
                      <td className="p-3">
                        <Badge variant="info">{s.theatre}</Badge>
                      </td>
                      <td className="p-3 text-sm text-neutral-500">{s.estimatedDuration} {isRtl ? 'دقيقة' : 'min'}</td>
                      <td className="p-3">
                        <Badge variant={priorityColors[s.priority]}>{isRtl ? (
                          s.priority === 'elective' ? 'اختياري' : s.priority === 'urgent' ? 'عاجل' : 'طارئ'
                        ) : s.priority}</Badge>
                      </td>
                      <td className="p-3">
                        <Badge variant={statusColors[s.status]}>{isRtl ? (
                          s.status === 'scheduled' ? 'مجدول' : s.status === 'in_progress' ? 'قيد الإجراء' : s.status === 'completed' ? 'مكتمل' : s.status === 'cancelled' ? 'ملغي' : 'متأخر'
                        ) : s.status}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      </div>
    </LayoutContent>
  );
}
