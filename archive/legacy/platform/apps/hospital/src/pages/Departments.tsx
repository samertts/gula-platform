import { useState } from 'react';
import { Card, CardHeader, CardBody, LayoutContent, useRTL } from '@gula/ui-platform';
import { DepartmentCard } from '../components/DepartmentCard';

const MOCK_DEPARTMENTS = [
  { id: '1', name: 'Emergency', nameAr: 'الطوارئ', code: 'ER', floor: 0, headDoctorAr: 'د. أحمد السامرائي', totalBeds: 30, availableBeds: 4, occupiedBeds: 26, activePatients: 26, admissionsToday: 8, bedOccupancyRate: 86.7, totalStaff: 45, totalDoctors: 12, totalNurses: 25, status: 'active' as const },
  { id: '2', name: 'Internal Medicine', nameAr: 'الباطنية', code: 'IM', floor: 2, headDoctorAr: 'د. سامر الجبوري', totalBeds: 40, availableBeds: 5, occupiedBeds: 35, activePatients: 33, admissionsToday: 6, bedOccupancyRate: 87.5, totalStaff: 38, totalDoctors: 10, totalNurses: 20, status: 'active' as const },
  { id: '3', name: 'Surgery', nameAr: 'الجراحة', code: 'SUR', floor: 3, headDoctorAr: 'د. خالد العاني', totalBeds: 35, availableBeds: 7, occupiedBeds: 28, activePatients: 27, admissionsToday: 4, bedOccupancyRate: 80.0, totalStaff: 35, totalDoctors: 9, totalNurses: 18, status: 'active' as const },
  { id: '4', name: 'Pediatrics', nameAr: 'طب الأطفال', code: 'PED', floor: 4, headDoctorAr: 'د. مريم الكاظمي', totalBeds: 20, availableBeds: 5, occupiedBeds: 15, activePatients: 14, admissionsToday: 3, bedOccupancyRate: 75.0, totalStaff: 28, totalDoctors: 8, totalNurses: 15, status: 'active' as const },
  { id: '5', name: 'Intensive Care Unit', nameAr: 'العناية المركزة', code: 'ICU', floor: 1, headDoctorAr: 'د. علي الحسيني', totalBeds: 15, availableBeds: 1, occupiedBeds: 14, activePatients: 14, admissionsToday: 2, bedOccupancyRate: 93.3, totalStaff: 32, totalDoctors: 8, totalNurses: 18, status: 'active' as const },
  { id: '6', name: 'Maternity', nameAr: 'النسائية والتوليد', code: 'MAT', floor: 5, headDoctorAr: 'د. ليلى رشيد', totalBeds: 25, availableBeds: 7, occupiedBeds: 18, activePatients: 17, admissionsToday: 5, bedOccupancyRate: 72.0, totalStaff: 30, totalDoctors: 8, totalNurses: 16, status: 'active' as const },
  { id: '7', name: 'Orthopedics', nameAr: 'العظام', code: 'ORT', floor: 3, headDoctorAr: 'د. قاسم العبيدي', totalBeds: 20, availableBeds: 4, occupiedBeds: 16, activePatients: 15, admissionsToday: 3, bedOccupancyRate: 80.0, totalStaff: 22, totalDoctors: 6, totalNurses: 12, status: 'active' as const },
  { id: '8', name: 'Psychiatry', nameAr: 'الأمراض النفسية', code: 'PSY', floor: 6, headDoctorAr: 'د. نادية جعفر', totalBeds: 15, availableBeds: 5, occupiedBeds: 10, activePatients: 10, admissionsToday: 1, bedOccupancyRate: 66.7, totalStaff: 18, totalDoctors: 5, totalNurses: 10, status: 'active' as const },
  { id: '9', name: 'Cardiology', nameAr: 'القلب', code: 'CARD', floor: 2, headDoctorAr: 'د. حامد النجار', totalBeds: 20, availableBeds: 3, occupiedBeds: 17, activePatients: 17, admissionsToday: 4, bedOccupancyRate: 85.0, totalStaff: 25, totalDoctors: 7, totalNurses: 13, status: 'active' as const },
  { id: '10', name: 'Nephrology', nameAr: 'الكلى', code: 'NEPH', floor: 4, headDoctorAr: 'د. رياض الصالحي', totalBeds: 15, availableBeds: 2, occupiedBeds: 13, activePatients: 13, admissionsToday: 2, bedOccupancyRate: 86.7, totalStaff: 20, totalDoctors: 5, totalNurses: 11, status: 'active' as const },
];

export function Departments() {
  const { isRtl } = useRTL();
  const [departments] = useState(MOCK_DEPARTMENTS);

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
            {isRtl ? 'إدارة الأقسام' : 'Departments'}
          </h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            {isRtl ? 'مؤشرات أداء الأقسام السريرية' : 'Clinical department performance metrics'}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {departments.map(dept => (
            <DepartmentCard
              key={dept.id}
              department={{
                ...dept,
                headOfficer: dept.headDoctorAr,
                headNurse: 'م. تمريض',
              }}
            />
          ))}
        </div>
      </div>
    </LayoutContent>
  );
}
