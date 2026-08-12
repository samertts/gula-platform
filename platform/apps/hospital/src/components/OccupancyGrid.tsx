import { useRTL } from '@gula/ui-platform';

interface BedCell {
  id: string;
  bedNumber: string;
  status: 'available' | 'occupied' | 'reserved' | 'maintenance' | 'cleaning';
  patientName?: string;
  patientNameAr?: string;
}

interface WardOccupancy {
  ward: string;
  wardAr: string;
  department: string;
  beds: BedCell[];
}

const MOCK_OCCUPANCY: WardOccupancy[] = [
  {
    ward: 'ER-1', wardAr: 'الطوارئ - 1', department: 'ER',
    beds: [
      { id: 'b1', bedNumber: 'ER-101', status: 'occupied', patientNameAr: 'أحمد خالد' },
      { id: 'b2', bedNumber: 'ER-102', status: 'occupied', patientNameAr: 'محمود علي' },
      { id: 'b3', bedNumber: 'ER-103', status: 'occupied', patientNameAr: 'سامي نوري' },
      { id: 'b4', bedNumber: 'ER-104', status: 'occupied', patientNameAr: 'نور صالح' },
      { id: 'b5', bedNumber: 'ER-105', status: 'available' },
      { id: 'b6', bedNumber: 'ER-106', status: 'occupied', patientNameAr: 'علي حسن' },
      { id: 'b7', bedNumber: 'ER-107', status: 'maintenance' },
      { id: 'b8', bedNumber: 'ER-108', status: 'available' },
      { id: 'b9', bedNumber: 'ER-109', status: 'occupied', patientNameAr: 'فاطمة أحمد' },
      { id: 'b10', bedNumber: 'ER-110', status: 'cleaning' },
    ],
  },
  {
    ward: 'ICU-1', wardAr: 'العناية المركزة - 1', department: 'ICU',
    beds: [
      { id: 'b11', bedNumber: 'ICU-301', status: 'occupied', patientNameAr: 'حسن نوري' },
      { id: 'b12', bedNumber: 'ICU-302', status: 'occupied', patientNameAr: 'سارة جاسم' },
      { id: 'b13', bedNumber: 'ICU-303', status: 'occupied', patientNameAr: 'كريم عباس' },
      { id: 'b14', bedNumber: 'ICU-304', status: 'occupied', patientNameAr: 'ليلى حسين' },
      { id: 'b15', bedNumber: 'ICU-305', status: 'available' },
      { id: 'b16', bedNumber: 'ICU-306', status: 'occupied', patientNameAr: 'محمد رضا' },
      { id: 'b17', bedNumber: 'ICU-307', status: 'occupied', patientNameAr: 'أمل كريم' },
      { id: 'b18', bedNumber: 'ICU-308', status: 'occupied', patientNameAr: 'ياسر قاسم' },
    ],
  },
  {
    ward: 'SUR-1', wardAr: 'الجراحة - 1', department: 'Surgery',
    beds: [
      { id: 'b19', bedNumber: 'SUR-401', status: 'occupied', patientNameAr: 'عمر ياسين' },
      { id: 'b20', bedNumber: 'SUR-402', status: 'occupied', patientNameAr: 'نادية شاكر' },
      { id: 'b21', bedNumber: 'SUR-403', status: 'available' },
      { id: 'b22', bedNumber: 'SUR-404', status: 'occupied', patientNameAr: 'جاسم محمد' },
      { id: 'b23', bedNumber: 'SUR-405', status: 'reserved' },
      { id: 'b24', bedNumber: 'SUR-406', status: 'available' },
    ],
  },
  {
    ward: 'IM-2', wardAr: 'الباطنية - 2', department: 'Internal Medicine',
    beds: [
      { id: 'b25', bedNumber: 'IM-201', status: 'occupied', patientNameAr: 'ناجي خليل' },
      { id: 'b26', bedNumber: 'IM-202', status: 'occupied', patientNameAr: 'هدى كاظم' },
      { id: 'b27', bedNumber: 'IM-203', status: 'available' },
      { id: 'b28', bedNumber: 'IM-204', status: 'occupied', patientNameAr: 'عبد الله سعيد' },
      { id: 'b29', bedNumber: 'IM-205', status: 'maintenance' },
      { id: 'b30', bedNumber: 'IM-206', status: 'occupied', patientNameAr: 'مريم جابر' },
    ],
  },
  {
    ward: 'PED-3', wardAr: 'الأطفال - 3', department: 'Pediatrics',
    beds: [
      { id: 'b31', bedNumber: 'PED-301', status: 'occupied', patientNameAr: 'نور علي' },
      { id: 'b32', bedNumber: 'PED-302', status: 'occupied', patientNameAr: 'طفل رضيع' },
      { id: 'b33', bedNumber: 'PED-303', status: 'available' },
      { id: 'b34', bedNumber: 'PED-304', status: 'available' },
    ],
  },
  {
    ward: 'MAT-2', wardAr: 'النسائية - 2', department: 'Maternity',
    beds: [
      { id: 'b35', bedNumber: 'MAT-201', status: 'occupied', patientNameAr: 'سارة جاسم' },
      { id: 'b36', bedNumber: 'MAT-202', status: 'occupied', patientNameAr: 'زينب نور' },
      { id: 'b37', bedNumber: 'MAT-203', status: 'available' },
      { id: 'b38', bedNumber: 'MAT-204', status: 'occupied', patientNameAr: 'حنين كريم' },
    ],
  },
];

const STATUS_STYLES: Record<string, { bg: string; dot: string; label: string; labelAr: string }> = {
  available: { bg: 'bg-green-100 dark:bg-green-900/20 border-green-300 dark:border-green-700', dot: 'bg-green-500', label: 'Available', labelAr: 'متاح' },
  occupied: { bg: 'bg-red-100 dark:bg-red-900/20 border-red-300 dark:border-red-700', dot: 'bg-red-500', label: 'Occupied', labelAr: 'مشغول' },
  reserved: { bg: 'bg-yellow-100 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-700', dot: 'bg-yellow-500', label: 'Reserved', labelAr: 'محجوز' },
  maintenance: { bg: 'bg-neutral-100 dark:bg-neutral-800 border-neutral-300 dark:border-neutral-600', dot: 'bg-neutral-500', label: 'Maintenance', labelAr: 'صيانة' },
  cleaning: { bg: 'bg-blue-100 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700', dot: 'bg-blue-500', label: 'Cleaning', labelAr: 'تنظيف' },
};

interface OccupancyGridProps {
  departmentFilter?: string;
}

export function OccupancyGrid({ departmentFilter = 'all' }: OccupancyGridProps) {
  const { isRtl } = useRTL();

  const filtered = departmentFilter === 'all'
    ? MOCK_OCCUPANCY
    : MOCK_OCCUPANCY.filter(w => w.department === departmentFilter);

  return (
    <div className="space-y-6">
      {filtered.map(ward => (
        <div key={ward.ward}>
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-sm font-bold text-neutral-900 dark:text-neutral-50">{isRtl ? ward.wardAr : ward.ward}</h3>
              <p className="text-xs text-neutral-400">
                {ward.beds.filter(b => b.status === 'occupied').length}/{ward.beds.length} {isRtl ? 'مشغول' : 'occupied'}
              </p>
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2">
            {ward.beds.map(bed => {
              const style = STATUS_STYLES[bed.status];
              return (
                <div
                  key={bed.id}
                  className={`relative p-2 rounded-lg border ${style.bg} transition-colors cursor-pointer hover:opacity-80`}
                >
                  <div className="flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full ${style.dot}`} />
                    <span className="text-xs font-bold text-neutral-700 dark:text-neutral-300">{bed.bedNumber}</span>
                  </div>
                  {bed.patientNameAr && (
                    <p className="text-xs text-neutral-600 dark:text-neutral-400 mt-1 truncate">{bed.patientNameAr}</p>
                  )}
                  {bed.status === 'available' && (
                    <p className="text-xs text-green-600 dark:text-green-400 mt-0.5">
                      {isRtl ? style.labelAr : style.label}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}

      <div className="flex flex-wrap items-center gap-4 text-xs text-neutral-500 pt-2 border-t border-neutral-100 dark:border-neutral-800">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-green-500" />
          {isRtl ? 'متاح' : 'Available'}
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
          {isRtl ? 'مشغول' : 'Occupied'}
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-yellow-500" />
          {isRtl ? 'محجوز' : 'Reserved'}
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-neutral-500" />
          {isRtl ? 'صيانة' : 'Maintenance'}
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
          {isRtl ? 'تنظيف' : 'Cleaning'}
        </div>
      </div>
    </div>
  );
}
