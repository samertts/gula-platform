import { useState } from 'react';
import {
  Card, CardHeader, CardBody, Badge, Button, LayoutContent, useRTL,
} from '@gula/ui-platform';

interface Clinic {
  id: string;
  name: string;
  nameAr: string;
  department: string;
  departmentAr: string;
  location: string;
  locationAr: string;
  doctor: string;
  doctorAr: string;
  todayAppointments: number;
  completedAppointments: number;
  waitingPatients: number;
  avgWaitTime: number;
  status: 'open' | 'closed' | 'full' | 'break';
  openingHours: string;
}

const MOCK_CLINICS: Clinic[] = [
  { id: '1', name: 'Cardiology Clinic', nameAr: 'عيادة القلب', department: 'Cardiology', departmentAr: 'القلب', location: 'Floor 2, Room 201', locationAr: 'الطابق 2، غرفة 201', doctor: 'Dr. Hamed Najjar', doctorAr: 'د. حامد النجار', todayAppointments: 25, completedAppointments: 18, waitingPatients: 7, avgWaitTime: 22, status: 'open', openingHours: '09:00 - 14:00' },
  { id: '2', name: 'Orthopedic Clinic', nameAr: 'عيادة العظام', department: 'Orthopedics', departmentAr: 'العظام', location: 'Floor 3, Room 305', locationAr: 'الطابق 3، غرفة 305', doctor: 'Dr. Qasim Obaidi', doctorAr: 'د. قاسم العبيدي', todayAppointments: 20, completedAppointments: 12, waitingPatients: 8, avgWaitTime: 35, status: 'open', openingHours: '09:00 - 15:00' },
  { id: '3', name: 'Pediatric Clinic', nameAr: 'عيادة الأطفال', department: 'Pediatrics', departmentAr: 'طب الأطفال', location: 'Floor 4, Room 410', locationAr: 'الطابق 4، غرفة 410', doctor: 'Dr. Maryam Kadhim', doctorAr: 'د. مريم الكاظمي', todayAppointments: 30, completedAppointments: 22, waitingPatients: 8, avgWaitTime: 18, status: 'open', openingHours: '08:30 - 14:30' },
  { id: '4', name: 'OB/GYN Clinic', nameAr: 'عيادة النساء والتوليد', department: 'Maternity', departmentAr: 'النسائية', location: 'Floor 5, Room 501', locationAr: 'الطابق 5، غرفة 501', doctor: 'Dr. Layla Rashid', doctorAr: 'د. ليلى رشيد', todayAppointments: 22, completedAppointments: 15, waitingPatients: 7, avgWaitTime: 28, status: 'open', openingHours: '09:00 - 14:00' },
  { id: '5', name: 'ENT Clinic', nameAr: 'عيادة الأنف والأذن والحنجرة', department: 'ENT', departmentAr: 'الأنف والأذن والحنجرة', location: 'Floor 2, Room 208', locationAr: 'الطابق 2، غرفة 208', doctor: 'Dr. Sami Noor', doctorAr: 'د. سامي نور', todayAppointments: 18, completedAppointments: 10, waitingPatients: 8, avgWaitTime: 40, status: 'open', openingHours: '10:00 - 15:00' },
  { id: '6', name: 'Dermatology Clinic', nameAr: 'عيادة الجلدية', department: 'Dermatology', departmentAr: 'الجلدية', location: 'Floor 3, Room 312', locationAr: 'الطابق 3، غرفة 312', doctor: 'Dr. Noor Ali', doctorAr: 'د. نور علي', todayAppointments: 15, completedAppointments: 15, waitingPatients: 0, avgWaitTime: 0, status: 'closed', openingHours: '09:00 - 13:00' },
  { id: '7', name: 'Diabetes Clinic', nameAr: 'عيادة السكري', department: 'Internal Medicine', departmentAr: 'الباطنية', location: 'Floor 2, Room 215', locationAr: 'الطابق 2، غرفة 215', doctor: 'Dr. Samer Jubouri', doctorAr: 'د. سامر الجبوري', todayAppointments: 28, completedAppointments: 20, waitingPatients: 8, avgWaitTime: 15, status: 'full', openingHours: '08:00 - 14:00' },
  { id: '8', name: 'Prenatal Clinic', nameAr: 'عيادة متابعة الحمل', department: 'Maternity', departmentAr: 'النسائية', location: 'Floor 5, Room 503', locationAr: 'الطابق 5، غرفة 503', doctor: 'Dr. Layla Rashid', doctorAr: 'د. ليلى رشيد', todayAppointments: 16, completedAppointments: 8, waitingPatients: 8, avgWaitTime: 45, status: 'open', openingHours: '09:00 - 13:00' },
];

export function Clinics() {
  const { isRtl } = useRTL();
  const [clinics] = useState(MOCK_CLINICS);

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
              {isRtl ? 'العيادات الخارجية' : 'Outpatient Clinics'}
            </h1>
            <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
              {isRtl ? 'إدارة العيادات الخارجية وجداول المواعيد' : 'Manage outpatient clinics and appointment schedules'}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { label: 'إجمالي المواعيد', labelEn: 'Total Appointments', value: 174, color: 'bg-blue-500' },
            { label: 'مكتملة', labelEn: 'Completed', value: 120, color: 'bg-green-500' },
            { label: 'بانتظار', labelEn: 'Waiting', value: 54, color: 'bg-yellow-500' },
            { label: 'متوسط الانتظار', labelEn: 'Avg Wait (min)', value: '29', color: 'bg-red-500' },
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

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {clinics.map(clinic => (
            <Card key={clinic.id}>
              <CardHeader
                title={isRtl ? clinic.nameAr : clinic.name}
                action={
                  <Badge variant={
                    clinic.status === 'open' ? 'success' :
                    clinic.status === 'closed' ? 'danger' :
                    clinic.status === 'full' ? 'warning' : 'info'
                  }>
                    {isRtl ? (
                      clinic.status === 'open' ? 'مفتوح' :
                      clinic.status === 'closed' ? 'مغلق' :
                      clinic.status === 'full' ? 'ممتلئ' : 'استراحة'
                    ) : clinic.status}
                  </Badge>
                }
              />
              <CardBody>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-neutral-500">{isRtl ? 'الطبيب' : 'Doctor'}:</span>
                    <span className="text-neutral-700 dark:text-neutral-300">{isRtl ? clinic.doctorAr : clinic.doctor}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">{isRtl ? 'الموقع' : 'Location'}:</span>
                    <span className="text-neutral-700 dark:text-neutral-300">{isRtl ? clinic.locationAr : clinic.location}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-neutral-500">{isRtl ? 'ساعات العمل' : 'Hours'}:</span>
                    <span className="text-neutral-700 dark:text-neutral-300">{clinic.openingHours}</span>
                  </div>
                  <div className="border-t border-neutral-100 dark:border-neutral-800 pt-2 mt-2">
                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div>
                        <p className="text-lg font-bold text-blue-600 dark:text-blue-400">{clinic.todayAppointments}</p>
                        <p className="text-xs text-neutral-400">{isRtl ? 'إجمالي' : 'Total'}</p>
                      </div>
                      <div>
                        <p className="text-lg font-bold text-green-600 dark:text-green-400">{clinic.completedAppointments}</p>
                        <p className="text-xs text-neutral-400">{isRtl ? 'مكتمل' : 'Done'}</p>
                      </div>
                      <div>
                        <p className="text-lg font-bold text-yellow-600 dark:text-yellow-400">{clinic.waitingPatients}</p>
                        <p className="text-xs text-neutral-400">{isRtl ? 'انتظار' : 'Queue'}</p>
                      </div>
                    </div>
                  </div>
                  {clinic.avgWaitTime > 0 && (
                    <div className="flex items-center gap-2 text-xs text-neutral-400">
                      <span>{isRtl ? 'متوسط وقت الانتظار:' : 'Avg wait time:'}</span>
                      <span className="font-medium text-neutral-600 dark:text-neutral-300">{clinic.avgWaitTime} {isRtl ? 'دقيقة' : 'min'}</span>
                    </div>
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
