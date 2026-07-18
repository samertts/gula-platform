import { useState } from 'react';
import {
  Card, CardHeader, CardBody, Badge, Button, Modal, LayoutContent, useRTL,
} from '@gula/ui-platform';
import { DischargeChecklist } from '../components/DischargeChecklist';

interface DischargePatient {
  id: string;
  patientName: string;
  patientNameAr: string;
  department: string;
  departmentAr: string;
  ward: string;
  wardAr: string;
  admissionDate: string;
  diagnosis: string;
  diagnosisAr: string;
  doctor: string;
  doctorAr: string;
  dischargeStatus: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  bedNumber: string;
  lengthOfStay: number;
}

const MOCK_DISCHARGES: DischargePatient[] = [
  { id: '1', patientName: 'Ahmed Khalid', patientNameAr: 'أحمد خالد', department: 'Internal Medicine', departmentAr: 'الباطنية', ward: 'IM-2', wardAr: 'الباطنية - 2', admissionDate: '2026-07-12', diagnosis: 'Pneumonia', diagnosisAr: 'التهاب رئوي', doctor: 'Dr. Samer', doctorAr: 'د. سامر', dischargeStatus: 'pending', bedNumber: 'B-201', lengthOfStay: 4 },
  { id: '2', patientName: 'Fatima Ali', patientNameAr: 'فاطمة علي', department: 'Pediatrics', departmentAr: 'طب الأطفال', ward: 'PED-1', wardAr: 'الأطفال - 1', admissionDate: '2026-07-10', diagnosis: 'Gastroenteritis', diagnosisAr: 'التهاب معوي', doctor: 'Dr. Maryam', doctorAr: 'د. مريم', dischargeStatus: 'in_progress', bedNumber: 'A-105', lengthOfStay: 6 },
  { id: '3', patientName: 'Hassan Abbas', patientNameAr: 'حسن عباس', department: 'Surgery', departmentAr: 'الجراحة', ward: 'SUR-2', wardAr: 'الجراحة - 2', admissionDate: '2026-07-08', diagnosis: 'Cholecystectomy', diagnosisAr: 'استئصال المرارة', doctor: 'Dr. Khalid', doctorAr: 'د. خالد', dischargeStatus: 'pending', bedNumber: 'D-405', lengthOfStay: 8 },
  { id: '4', patientName: 'Noor Jassim', patientNameAr: 'نور جاسم', department: 'Maternity', departmentAr: 'النسائية', ward: 'MAT-1', wardAr: 'النسائية - 1', admissionDate: '2026-07-14', diagnosis: 'Normal Delivery', diagnosisAr: 'ولادة طبيعية', doctor: 'Dr. Layla', doctorAr: 'د. ليلى', dischargeStatus: 'pending', bedNumber: 'E-502', lengthOfStay: 2 },
];

export function Discharge() {
  const { isRtl } = useRTL();
  const [patients] = useState(MOCK_DISCHARGES);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const selected = patients.find(p => p.id === selectedId);

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
            {isRtl ? 'إدارة التخريج' : 'Discharge Management'}
          </h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            {isRtl ? 'إجراءات تخريج المرضى' : 'Patient discharge workflow'}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { label: 'بانتظار التخريج', labelEn: 'Pending', value: patients.filter(p => p.dischargeStatus === 'pending').length, color: 'bg-yellow-500' },
            { label: 'قيد الإجراء', labelEn: 'In Progress', value: patients.filter(p => p.dischargeStatus === 'in_progress').length, color: 'bg-blue-500' },
            { label: 'مكتمل اليوم', labelEn: 'Completed Today', value: 5, color: 'bg-green-500' },
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
          <CardHeader title={isRtl ? 'مرضى التخريج' : 'Discharge List'} />
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-neutral-200 dark:border-neutral-700">
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'المريض' : 'Patient'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'القسم' : 'Dept.'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'التشخيص' : 'Diagnosis'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'تاريخ الدخول' : 'Admitted'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'المدة' : 'LOS'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الحالة' : 'Status'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الإجراءات' : 'Actions'}</th>
                  </tr>
                </thead>
                <tbody>
                  {patients.map(p => (
                    <tr key={p.id} className="border-b border-neutral-100 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800/50">
                      <td className="p-3">
                        <p className="font-medium text-neutral-900 dark:text-neutral-50">{isRtl ? p.patientNameAr : p.patientName}</p>
                        <p className="text-xs text-neutral-400">{isRtl ? p.doctorAr : p.doctor}</p>
                      </td>
                      <td className="p-3 text-neutral-700 dark:text-neutral-300">{isRtl ? p.departmentAr : p.department}</td>
                      <td className="p-3 text-neutral-700 dark:text-neutral-300">{isRtl ? p.diagnosisAr : p.diagnosis}</td>
                      <td className="p-3 text-sm text-neutral-500">{p.admissionDate}</td>
                      <td className="p-3">
                        <Badge variant="info">{p.lengthOfStay} {isRtl ? 'أيام' : 'days'}</Badge>
                      </td>
                      <td className="p-3">
                        <Badge variant={
                          p.dischargeStatus === 'pending' ? 'warning' :
                          p.dischargeStatus === 'in_progress' ? 'primary' : 'success'
                        }>
                          {isRtl ? (
                            p.dischargeStatus === 'pending' ? 'بانتظار' :
                            p.dischargeStatus === 'in_progress' ? 'قيد الإجراء' : 'مكتمل'
                          ) : p.dischargeStatus}
                        </Badge>
                      </td>
                      <td className="p-3">
                        <Button size="sm" onClick={() => setSelectedId(p.id)}>
                          {isRtl ? 'إجراء التخريج' : 'Process'}
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      </div>

      <Modal
        isOpen={!!selectedId}
        onClose={() => setSelectedId(null)}
        title={isRtl ? `إجراءات تخريج - ${selected?.patientNameAr}` : `Discharge - ${selected?.patientName}`}
        size="lg"
      >
        {selected && <DischargeChecklist patient={selected} onComplete={() => setSelectedId(null)} />}
      </Modal>
    </LayoutContent>
  );
}
