import { Card, CardHeader, CardBody, Badge, useRTL } from '@gula/ui-platform';

interface DepartmentCardProps {
  department: {
    id: string;
    name: string;
    nameAr: string;
    code: string;
    floor: number;
    headOfficer: string;
    headNurse: string;
    totalBeds: number;
    availableBeds: number;
    occupiedBeds: number;
    activePatients: number;
    admissionsToday: number;
    bedOccupancyRate: number;
    totalStaff: number;
    totalDoctors: number;
    totalNurses: number;
    status: 'active' | 'inactive' | 'under_maintenance';
  };
}

export function DepartmentCard({ department }: DepartmentCardProps) {
  const { isRtl } = useRTL();
  const occupancyPct = department.bedOccupancyRate;

  return (
    <Card>
      <CardHeader
        title={
          <div className="flex items-center gap-2">
            <span>{isRtl ? department.nameAr : department.name}</span>
            <Badge variant="info" size="sm">{department.code}</Badge>
          </div>
        }
        action={
          <Badge variant={
            department.status === 'active' ? 'success' :
            department.status === 'inactive' ? 'danger' : 'warning'
          } size="sm">
            {isRtl ? (
              department.status === 'active' ? 'نشط' :
              department.status === 'inactive' ? 'غير نشط' : 'صيانة'
            ) : department.status}
          </Badge>
        }
      />
      <CardBody>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-neutral-500">{isRtl ? 'نسبة الإشغال' : 'Occupancy'}</span>
                <span className="text-xs font-bold text-neutral-700 dark:text-neutral-300">{occupancyPct}%</span>
              </div>
              <div className="h-2 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    occupancyPct > 90 ? 'bg-red-500' :
                    occupancyPct > 75 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${occupancyPct}%` }}
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3 text-center text-sm">
            <div className="bg-neutral-50 dark:bg-neutral-800/50 p-2 rounded-lg">
              <p className="text-lg font-bold text-neutral-900 dark:text-neutral-50">{department.occupiedBeds}</p>
              <p className="text-xs text-neutral-400">{isRtl ? 'مشغول' : 'Occ.'}</p>
            </div>
            <div className="bg-neutral-50 dark:bg-neutral-800/50 p-2 rounded-lg">
              <p className="text-lg font-bold text-green-600">{department.availableBeds}</p>
              <p className="text-xs text-neutral-400">{isRtl ? 'متاح' : 'Avail.'}</p>
            </div>
            <div className="bg-neutral-50 dark:bg-neutral-800/50 p-2 rounded-lg">
              <p className="text-lg font-bold text-blue-600">{department.activePatients}</p>
              <p className="text-xs text-neutral-400">{isRtl ? 'مرضى' : 'Patients'}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs text-neutral-500">
            <div className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-primary-400" />
              {isRtl ? 'الطابق' : 'Floor'}: {department.floor}
            </div>
            <div className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-primary-400" />
              {isRtl ? 'إجمالي الأسرة' : 'Beds'}: {department.totalBeds}
            </div>
            <div className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-primary-400" />
              {isRtl ? 'أطباء' : 'Doctors'}: {department.totalDoctors}
            </div>
            <div className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-primary-400" />
              {isRtl ? 'التمريض' : 'Nurses'}: {department.totalNurses}
            </div>
            <div className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-primary-400" />
              {isRtl ? 'استقبال اليوم' : 'Adm. Today'}: {department.admissionsToday}
            </div>
            <div className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-primary-400" />
              {isRtl ? 'إجمالي الموظفين' : 'Staff'}: {department.totalStaff}
            </div>
          </div>

          <div className="pt-2 border-t border-neutral-100 dark:border-neutral-800">
            <div className="flex items-center justify-between text-xs">
              <div>
                <p className="text-neutral-400">{isRtl ? 'رئيس القسم' : 'Head'}</p>
                <p className="font-medium text-neutral-700 dark:text-neutral-300">{department.headOfficer}</p>
              </div>
              <div className="text-left">
                <p className="text-neutral-400">{isRtl ? 'رئيسة التمريض' : 'Head Nurse'}</p>
                <p className="font-medium text-neutral-700 dark:text-neutral-300">{department.headNurse}</p>
              </div>
            </div>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
