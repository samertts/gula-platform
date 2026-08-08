import { useState } from 'react';
import {
  Card, CardHeader, CardBody, Button, Badge, Input, Select, Modal, LayoutContent, useRTL,
} from '@gula/ui-platform';
import { AdmissionForm } from '../components/AdmissionForm';

interface AdmissionItem {
  id: string;
  patientName: string;
  patientNameAr: string;
  gender: 'male' | 'female';
  age: number;
  phone: string;
  admissionDate: string;
  department: string;
  departmentAr: string;
  ward: string;
  wardAr: string;
  diagnosis: string;
  diagnosisAr: string;
  status: 'pending' | 'active' | 'transferred' | 'discharged';
  bedNumber: string | null;
  doctor: string;
}

const MOCK_ADMISSIONS: AdmissionItem[] = [
  { id: '1', patientName: 'Ahmed Khalid', patientNameAr: 'أحمد خالد', gender: 'male', age: 45, phone: '07701234567', admissionDate: '2026-07-16 09:30', department: 'ER', departmentAr: 'الطوارئ', ward: 'ER-1', wardAr: 'الطوارئ - 1', diagnosis: 'Chest Pain', diagnosisAr: 'ألم صدر', status: 'active', bedNumber: 'A-101', doctor: 'د. سامر' },
  { id: '2', patientName: 'Sara Jassim', patientNameAr: 'سارة جاسم', gender: 'female', age: 32, phone: '07707654321', admissionDate: '2026-07-16 08:15', department: 'Maternity', departmentAr: 'النسائية', ward: 'MAT-2', wardAr: 'النسائية - 2', diagnosis: 'Pregnancy', diagnosisAr: 'متابعة حمل', status: 'active', bedNumber: 'B-205', doctor: 'د. ليلى' },
  { id: '3', patientName: 'Hassan Noori', patientNameAr: 'حسن نوري', gender: 'male', age: 60, phone: '07701112233', admissionDate: '2026-07-15 22:45', department: 'ICU', departmentAr: 'العناية المركزة', ward: 'ICU-1', wardAr: 'العناية - 1', diagnosis: 'Stroke', diagnosisAr: 'جلطة دماغية', status: 'active', bedNumber: 'C-301', doctor: 'د. أحمد' },
  { id: '4', patientName: 'Noor Ali', patientNameAr: 'نور علي', gender: 'female', age: 28, phone: '07704445566', admissionDate: '2026-07-16 11:00', department: 'Pediatrics', departmentAr: 'طب الأطفال', ward: 'PED-3', wardAr: 'الأطفال - 3', diagnosis: 'Bronchitis', diagnosisAr: 'التهاب شعبي', status: 'pending', bedNumber: null, doctor: 'د. مريم' },
  { id: '5', patientName: 'Omar Yasin', patientNameAr: 'عمر ياسين', gender: 'male', age: 55, phone: '07707778899', admissionDate: '2026-07-15 14:20', department: 'Surgery', departmentAr: 'الجراحة', ward: 'SUR-1', wardAr: 'الجراحة - 1', diagnosis: 'Appendicitis', diagnosisAr: 'التهاب الزائدة', status: 'active', bedNumber: 'D-401', doctor: 'د. خالد' },
  { id: '6', patientName: 'Layla Abbas', patientNameAr: 'ليلى عباس', gender: 'female', age: 70, phone: '07703334455', admissionDate: '2026-07-14 19:30', department: 'Internal Medicine', departmentAr: 'الباطنية', ward: 'IM-2', wardAr: 'الباطنية - 2', diagnosis: 'Diabetes', diagnosisAr: 'سكري', status: 'discharged', bedNumber: null, doctor: 'د. سامر' },
];

const STATUS_COLORS: Record<string, 'warning' | 'success' | 'info' | 'danger'> = {
  pending: 'warning',
  active: 'success',
  transferred: 'info',
  discharged: 'danger',
};

export function Admissions() {
  const { isRtl } = useRTL();
  const [admissions] = useState(MOCK_ADMISSIONS);
  const [showForm, setShowForm] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filtered = admissions.filter(a => {
    if (statusFilter !== 'all' && a.status !== statusFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return a.patientNameAr.includes(q) || a.patientName.toLowerCase().includes(q) || a.phone.includes(q);
    }
    return true;
  });

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
              {isRtl ? 'إدارة الاستقبال' : 'Admissions Management'}
            </h1>
            <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
              {isRtl ? 'إدارة مرضى الاستقبال والتنويم' : 'Manage patient admissions and hospitalization'}
            </p>
          </div>
          <Button onClick={() => setShowForm(true)}>
            {isRtl ? 'تسجيل استقبال جديد' : 'New Admission'}
          </Button>
        </div>

        <Card>
          <CardHeader
            title={isRtl ? 'قائمة الاستقبالات' : 'Admissions List'}
            action={
              <div className="flex items-center gap-3">
                <Input
                  placeholder={isRtl ? 'بحث...' : 'Search...'}
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="w-48"
                />
                <Select
                  value={statusFilter}
                  onChange={v => setStatusFilter(v as string)}
                  options={[
                    { value: 'all', label: isRtl ? 'الكل' : 'All' },
                    { value: 'pending', label: isRtl ? 'بانتظار السرير' : 'Pending' },
                    { value: 'active', label: isRtl ? 'نشط' : 'Active' },
                    { value: 'transferred', label: isRtl ? 'محول' : 'Transferred' },
                    { value: 'discharged', label: isRtl ? 'مخرج' : 'Discharged' },
                  ]}
                  className="w-36"
                />
              </div>
            }
          />
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-neutral-200 dark:border-neutral-700">
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'المريض' : 'Patient'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'القسم' : 'Department'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'التشخيص' : 'Diagnosis'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'السرير' : 'Bed'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'تاريخ الاستقبال' : 'Admitted'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الحالة' : 'Status'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'إجراءات' : 'Actions'}</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(adm => (
                    <tr key={adm.id} className="border-b border-neutral-100 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800/50">
                      <td className="p-3">
                        <div>
                          <p className="font-medium text-neutral-900 dark:text-neutral-50">{isRtl ? adm.patientNameAr : adm.patientName}</p>
                          <p className="text-xs text-neutral-400">{adm.gender === 'male' ? (isRtl ? 'ذكر' : 'Male') : (isRtl ? 'أنثى' : 'Female')}, {adm.age} {isRtl ? 'سنة' : 'yrs'}</p>
                        </div>
                      </td>
                      <td className="p-3">
                        <p className="text-neutral-700 dark:text-neutral-300">{isRtl ? adm.departmentAr : adm.department}</p>
                        <p className="text-xs text-neutral-400">{isRtl ? adm.wardAr : adm.ward}</p>
                      </td>
                      <td className="p-3 text-neutral-700 dark:text-neutral-300">
                        {isRtl ? adm.diagnosisAr : adm.diagnosis}
                      </td>
                      <td className="p-3">
                        {adm.bedNumber ? (
                          <Badge variant="info">{adm.bedNumber}</Badge>
                        ) : (
                          <span className="text-xs text-yellow-600">{isRtl ? 'غير محدد' : 'Unassigned'}</span>
                        )}
                      </td>
                      <td className="p-3 text-sm text-neutral-500">{adm.admissionDate}</td>
                      <td className="p-3">
                        <Badge variant={STATUS_COLORS[adm.status]}>
                          {isRtl ? (
                            adm.status === 'active' ? 'نشط' : adm.status === 'pending' ? 'بانتظار' : adm.status === 'transferred' ? 'محول' : 'مخرج'
                          ) : adm.status}
                        </Badge>
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <Button variant="ghost" size="sm">{isRtl ? 'عرض' : 'View'}</Button>
                          {adm.status === 'active' && (
                            <Button variant="outline" size="sm">{isRtl ? 'تحويل' : 'Transfer'}</Button>
                          )}
                        </div>
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
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        title={isRtl ? 'تسجيل استقبال جديد' : 'New Admission'}
        size="lg"
      >
        <AdmissionForm onClose={() => setShowForm(false)} />
      </Modal>
    </LayoutContent>
  );
}
