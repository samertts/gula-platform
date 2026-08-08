import { useState } from 'react';
import { Card, CardHeader, CardBody, Button, Badge, LayoutContent } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';

interface Appointment {
  id: string;
  patientName: string;
  patientNameAr: string;
  time: string;
  type: string;
  typeAr: string;
  status: 'scheduled' | 'confirmed' | 'in_progress' | 'completed' | 'cancelled' | 'no_show';
  chiefComplaint: string;
  chiefComplaintAr: string;
}

const MOCK_APPOINTMENTS: Appointment[] = [
  { id: 'ap1', patientName: 'Ahmed Ali', patientNameAr: 'أحمد علي', time: '09:00', type: 'checkup', typeAr: 'فحص دوري', status: 'confirmed', chiefComplaint: 'Annual checkup', chiefComplaintAr: 'فحص سنوي' },
  { id: 'ap2', patientName: 'Sara Mohammed', patientNameAr: 'سارة محمد', time: '10:00', type: 'follow_up', typeAr: 'متابعة', status: 'in_progress', chiefComplaint: 'BP follow up', chiefComplaintAr: 'متابعة ضغط' },
  { id: 'ap3', patientName: 'Hassan Ibrahim', patientNameAr: 'حسن إبراهيم', time: '11:00', type: 'consultation', typeAr: 'استشارة', status: 'scheduled', chiefComplaint: 'Chest pain', chiefComplaintAr: 'ألم صدر' },
  { id: 'ap4', patientName: 'Noor Khalid', patientNameAr: 'نور خالد', time: '12:00', type: 'lab_test', typeAr: 'تحليل', status: 'scheduled', chiefComplaint: 'Lab result review', chiefComplaintAr: 'مراجعة نتائج' },
  { id: 'ap5', patientName: 'Omar Hassan', patientNameAr: 'عمر حسن', time: '14:00', type: 'follow_up', typeAr: 'متابعة', status: 'scheduled', chiefComplaint: 'Diabetes follow up', chiefComplaintAr: 'متابعة سكري' },
  { id: 'ap6', patientName: 'Layla Abbas', patientNameAr: 'ليلى عباس', time: '15:00', type: 'checkup', typeAr: 'فحص دوري', status: 'scheduled', chiefComplaint: 'Wellness check', chiefComplaintAr: 'فحص صحي' },
];

const timeSlots = ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '14:00', '14:30', '15:00', '15:30', '16:00'];

export function Schedule() {
  const { isRtl } = useRTL();
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [appointments] = useState(MOCK_APPOINTMENTS);

  const statusColors: Record<string, 'success' | 'warning' | 'info' | 'default' | 'danger'> = {
    confirmed: 'info',
    in_progress: 'success',
    scheduled: 'default',
    completed: 'success',
    cancelled: 'danger',
    no_show: 'danger',
  };

  const getAppointmentForSlot = (time: string) => appointments.find(a => a.time === time);

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
            {isRtl ? 'جدول المواعيد' : 'Schedule'}
          </h1>
          <input
            type="date"
            value={selectedDate}
            onChange={e => setSelectedDate(e.target.value)}
            className="rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-3 py-2 text-sm"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {timeSlots.map(slot => {
            const apt = getAppointmentForSlot(slot);
            return (
              <div
                key={slot}
                className={`p-4 rounded-xl border-2 transition-colors ${
                  apt
                    ? apt.status === 'in_progress'
                      ? 'border-success-500 bg-success-50 dark:bg-success-950'
                      : 'border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800'
                    : 'border-dashed border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-900'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="text-center min-w-[48px]">
                      <p className="text-lg font-bold text-neutral-900 dark:text-neutral-50">{slot}</p>
                    </div>
                    {apt ? (
                      <div>
                        <p className="font-medium text-sm">{isRtl ? apt.patientNameAr : apt.patientName}</p>
                        <p className="text-xs text-neutral-500">{isRtl ? apt.chiefComplaintAr : apt.chiefComplaint}</p>
                        <div className="flex gap-1 mt-1">
                          <Badge variant="default" size="xs">{isRtl ? apt.typeAr : apt.type}</Badge>
                          <Badge variant={statusColors[apt.status]} size="xs">
                            {apt.status === 'confirmed' ? (isRtl ? 'مؤكد' : 'Confirmed') :
                             apt.status === 'in_progress' ? (isRtl ? 'قيد التشغيل' : 'In Progress') :
                             apt.status === 'scheduled' ? (isRtl ? 'مجدول' : 'Scheduled') :
                             apt.status === 'completed' ? (isRtl ? 'مكتمل' : 'Completed') :
                             apt.status === 'cancelled' ? (isRtl ? 'ملغي' : 'Cancelled') :
                             (isRtl ? 'لم يحضر' : 'No Show')}
                          </Badge>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-neutral-400">{isRtl ? 'موعد متاح' : 'Available'}</p>
                    )}
                  </div>
                  {apt && apt.status === 'scheduled' && (
                    <div className="flex gap-1">
                      <button className="p-1.5 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 text-primary-600">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
                      </button>
                      <button className="p-1.5 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 text-success-600">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12" /></svg>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </LayoutContent>
  );
}
