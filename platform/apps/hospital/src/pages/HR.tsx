import { useState } from 'react';
import {
  Card, CardHeader, CardBody, Badge, Select, Input, LayoutContent, useRTL,
} from '@gula/ui-platform';
import { StaffSchedule } from '../components/StaffSchedule';

interface StaffRecord {
  id: string;
  name: string;
  nameAr: string;
  role: string;
  roleAr: string;
  department: string;
  departmentAr: string;
  status: 'active' | 'on_leave' | 'suspended' | 'terminated';
  shift: string;
  shiftAr: string;
  phone: string;
  email: string;
  joiningDate: string;
}

const MOCK_STAFF: StaffRecord[] = [
  { id: '1', name: 'Dr. Ahmed Samarrai', nameAr: 'د. أحمد السامرائي', role: 'Consultant', roleAr: 'استشاري', department: 'Emergency', departmentAr: 'الطوارئ', status: 'active', shift: 'morning', shiftAr: 'صباحي', phone: '07701112233', email: 'ahmed.s@hospital.gula', joiningDate: '2020-03-15' },
  { id: '2', name: 'Nurse Fatima Noor', nameAr: 'م. فاطمة نور', role: 'Head Nurse', roleAr: 'رئيسة تمريض', department: 'ICU', departmentAr: 'العناية المركزة', status: 'active', shift: 'rotating', shiftAr: 'متناوب', phone: '07702223344', email: 'fatima.n@hospital.gula', joiningDate: '2019-06-01' },
  { id: '3', name: 'Dr. Khalid Ani', nameAr: 'د. خالد العاني', role: 'Surgeon', roleAr: 'جراح', department: 'Surgery', departmentAr: 'الجراحة', status: 'on_leave', shift: 'morning', shiftAr: 'صباحي', phone: '07703334455', email: 'khalid.a@hospital.gula', joiningDate: '2021-01-10' },
  { id: '4', name: 'Dr. Maryam Kadhim', nameAr: 'د. مريم الكاظمي', role: 'Pediatrician', roleAr: 'طبيبة أطفال', department: 'Pediatrics', departmentAr: 'طب الأطفال', status: 'active', shift: 'evening', shiftAr: 'مسائي', phone: '07704445566', email: 'maryam.k@hospital.gula', joiningDate: '2022-09-20' },
  { id: '5', name: 'Nurse Hassan Ali', nameAr: 'م. حسن علي', role: 'Nurse', roleAr: 'ممرض', department: 'Emergency', departmentAr: 'الطوارئ', status: 'active', shift: 'night', shiftAr: 'ليلي', phone: '07705556677', email: 'hassan.a@hospital.gula', joiningDate: '2023-04-05' },
  { id: '6', name: 'Tech. Sami Noor', nameAr: 'ف. سامي نور', role: 'Lab Technician', roleAr: 'فني مختبر', department: 'Laboratory', departmentAr: 'المختبر', status: 'active', shift: 'morning', shiftAr: 'صباحي', phone: '07706667788', email: 'sami.n@hospital.gula', joiningDate: '2021-11-15' },
  { id: '7', name: 'Dr. Layla Rashid', nameAr: 'د. ليلى رشيد', role: 'Gynecologist', roleAr: 'طبيبة نسائية', department: 'Maternity', departmentAr: 'النسائية', status: 'active', shift: 'morning', shiftAr: 'صباحي', phone: '07707778899', email: 'layla.r@hospital.gula', joiningDate: '2020-08-01' },
  { id: '8', name: 'Admin Qasim Yousif', nameAr: 'أ. قاسم يوسف', role: 'Admin Officer', roleAr: 'مسؤول إداري', department: 'Administration', departmentAr: 'الإدارة', status: 'active', shift: 'morning', shiftAr: 'صباحي', phone: '07708889900', email: 'qasim.y@hospital.gula', joiningDate: '2018-05-20' },
  { id: '9', name: 'Nurse Zainab Ali', nameAr: 'م. زينب علي', role: 'Nurse', roleAr: 'ممرضة', department: 'Surgery', departmentAr: 'الجراحة', status: 'on_leave', shift: 'morning', shiftAr: 'صباحي', phone: '07709990011', email: 'zainab.a@hospital.gula', joiningDate: '2022-02-14' },
  { id: '10', name: 'Dr. Hamed Najjar', nameAr: 'د. حامد النجار', role: 'Cardiologist', roleAr: 'طبيب قلب', department: 'Cardiology', departmentAr: 'القلب', status: 'active', shift: 'rotating', shiftAr: 'متناوب', phone: '07701002003', email: 'hamed.n@hospital.gula', joiningDate: '2019-10-01' },
];

const DEPARTMENTS = ['الكل', 'الطوارئ', 'الباطنية', 'الجراحة', 'الأطفال', 'العناية المركزة', 'النسائية', 'المختبر', 'الإدارة', 'القلب'];

export function HR() {
  const { isRtl } = useRTL();
  const [staff] = useState(MOCK_STAFF);
  const [deptFilter, setDeptFilter] = useState('الكل');
  const [searchQuery, setSearchQuery] = useState('');

  const filtered = staff.filter(s => {
    if (deptFilter !== 'الكل' && s.departmentAr !== deptFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return s.nameAr.includes(q) || s.name.toLowerCase().includes(q);
    }
    return true;
  });

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
            {isRtl ? 'الموارد البشرية' : 'Human Resources'}
          </h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            {isRtl ? 'إدارة الموظفين والجدولة' : 'Staff management and scheduling'}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { label: 'إجمالي الموظفين', labelEn: 'Total Staff', value: 142, color: 'bg-primary-500' },
            { label: 'نشط', labelEn: 'Active', value: 128, color: 'bg-green-500' },
            { label: 'في إجازة', labelEn: 'On Leave', value: 12, color: 'bg-yellow-500' },
            { label: 'متوقف', labelEn: 'Suspended', value: 2, color: 'bg-red-500' },
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

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card>
              <CardHeader
                title={isRtl ? 'قائمة الموظفين' : 'Staff List'}
                action={
                  <div className="flex items-center gap-3">
                    <Input
                      placeholder={isRtl ? 'بحث...' : 'Search...'}
                      value={searchQuery}
                      onChange={e => setSearchQuery(e.target.value)}
                      className="w-48"
                    />
                    <Select
                      value={deptFilter}
                      onChange={v => setDeptFilter(v as string)}
                      options={DEPARTMENTS.map(d => ({ value: d, label: d }))}
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
                        <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الاسم' : 'Name'}</th>
                        <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'القسم' : 'Department'}</th>
                        <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الوظيفة' : 'Role'}</th>
                        <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الوردية' : 'Shift'}</th>
                        <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الحالة' : 'Status'}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filtered.map(s => (
                        <tr key={s.id} className="border-b border-neutral-100 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800/50">
                          <td className="p-3">
                            <p className="font-medium text-neutral-900 dark:text-neutral-50">{isRtl ? s.nameAr : s.name}</p>
                          </td>
                          <td className="p-3 text-neutral-700 dark:text-neutral-300">{isRtl ? s.departmentAr : s.department}</td>
                          <td className="p-3">
                            <Badge variant="primary">{isRtl ? s.roleAr : s.role}</Badge>
                          </td>
                          <td className="p-3 text-sm text-neutral-500">{isRtl ? s.shiftAr : s.shift}</td>
                          <td className="p-3">
                            <Badge variant={s.status === 'active' ? 'success' : s.status === 'on_leave' ? 'warning' : 'danger'}>
                              {isRtl ? (
                                s.status === 'active' ? 'نشط' : s.status === 'on_leave' ? 'في إجازة' : 'متوقف'
                              ) : s.status}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardBody>
            </Card>
          </div>

          <div>
            <StaffSchedule />
          </div>
        </div>
      </div>
    </LayoutContent>
  );
}
