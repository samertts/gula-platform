import { useState } from 'react';
import {
  Card, CardHeader, CardBody, Badge, Select, Input, LayoutContent, useRTL,
} from '@gula/ui-platform';
import { AssetCard } from '../components/AssetCard';

const MOCK_ASSETS = [
  { id: '1', name: 'CT Scanner', nameAr: 'الماسح المقطعي', type: 'imaging', typeAr: 'تصوير', model: 'Siemens SOMATOM X.cite', serialNumber: 'SN-2024-001', manufacturer: 'Siemens', departmentAr: 'الأشعة', locationAr: 'الطابق الأرضي - غرفة 3', purchaseCost: 850000, currentValue: 765000, warrantyExpiry: '2029-06-15', status: 'operational' as const, condition: 'excellent' as const, lastMaintenanceDate: '2026-06-01', nextMaintenanceDate: '2026-08-01' },
  { id: '2', name: 'MRI Machine', nameAr: 'جهاز الرنين المغناطيسي', type: 'imaging', typeAr: 'تصوير', model: 'Philips Ingenia 3.0T', serialNumber: 'SN-2023-045', manufacturer: 'Philips', departmentAr: 'الأشعة', locationAr: 'الطابق الأرضي - غرفة 5', purchaseCost: 1200000, currentValue: 1080000, warrantyExpiry: '2028-03-20', status: 'operational' as const, condition: 'good' as const, lastMaintenanceDate: '2026-05-15', nextMaintenanceDate: '2026-07-15' },
  { id: '3', name: 'Ventilator', nameAr: 'جهاز تنفس اصطناعي', type: 'life_support', typeAr: 'دعم حياة', model: 'Hamilton C6', serialNumber: 'SN-2024-078', manufacturer: 'Hamilton Medical', departmentAr: 'العناية المركزة', locationAr: 'العناية المركزة - غرفة 2', purchaseCost: 45000, currentValue: 40500, warrantyExpiry: '2027-11-01', status: 'operational' as const, condition: 'good' as const, lastMaintenanceDate: '2026-06-10', nextMaintenanceDate: '2026-07-10' },
  { id: '4', name: 'X-Ray Machine', nameAr: 'جهاز أشعة سينية', type: 'imaging', typeAr: 'تصوير', model: 'GE Healthcare AMX-400', serialNumber: 'SN-2023-112', manufacturer: 'GE Healthcare', departmentAr: 'الطوارئ', locationAr: 'الطوارئ - غرفة الأشعة', purchaseCost: 180000, currentValue: 144000, warrantyExpiry: '2027-08-15', status: 'under_maintenance' as const, condition: 'fair' as const, lastMaintenanceDate: '2026-07-01', nextMaintenanceDate: '2026-07-20' },
  { id: '5', name: 'Ultrasound', nameAr: 'جهاز الموجات فوق الصوتية', type: 'imaging', typeAr: 'تصوير', model: 'Samsung HS70A', serialNumber: 'SN-2024-034', manufacturer: 'Samsung Medison', departmentAr: 'النسائية', locationAr: 'العيادات الخارجية - غرفة 7', purchaseCost: 95000, currentValue: 85500, warrantyExpiry: '2028-01-10', status: 'operational' as const, condition: 'excellent' as const, lastMaintenanceDate: '2026-06-20', nextMaintenanceDate: '2026-08-20' },
  { id: '6', name: 'Defibrillator', nameAr: 'مزيل الرجفان', type: 'emergency', typeAr: 'طوارئ', model: 'Zoll R Series', serialNumber: 'SN-2024-091', manufacturer: 'Zoll Medical', departmentAr: 'الطوارئ', locationAr: 'الطوارئ - غرفة الإنعاش', purchaseCost: 28000, currentValue: 25200, warrantyExpiry: '2027-12-01', status: 'operational' as const, condition: 'good' as const, lastMaintenanceDate: '2026-06-05', nextMaintenanceDate: '2026-09-05' },
  { id: '7', name: 'Dialysis Machine', nameAr: 'جهاز غسيل الكلى', type: 'dialysis', typeAr: 'غسيل كلوي', model: 'Fresenius 5008S', serialNumber: 'SN-2023-156', manufacturer: 'Fresenius', departmentAr: 'الكلى', locationAr: 'وحدة غسيل الكلى - غرفة 1', purchaseCost: 65000, currentValue: 52000, warrantyExpiry: '2027-05-20', status: 'operational' as const, condition: 'good' as const, lastMaintenanceDate: '2026-06-15', nextMaintenanceDate: '2026-08-15' },
  { id: '8', name: 'Anesthesia Machine', nameAr: 'جهاز التخدير', type: 'surgical', typeAr: 'جراحي', model: 'GE Avance CS2', serialNumber: 'SN-2024-023', manufacturer: 'GE Healthcare', departmentAr: 'الجراحة', locationAr: 'غرفة العمليات - 3', purchaseCost: 75000, currentValue: 67500, warrantyExpiry: '2028-02-28', status: 'operational' as const, condition: 'excellent' as const, lastMaintenanceDate: '2026-06-25', nextMaintenanceDate: '2026-09-25' },
  { id: '9', name: 'ECG Machine', nameAr: 'جهاز تخطيط القلب', type: 'diagnostic', typeAr: 'تشخيصي', model: 'Schiller Cardiovit AT-2', serialNumber: 'SN-2024-067', manufacturer: 'Schiller', departmentAr: 'القلب', locationAr: 'عيادة القلب - غرفة 2', purchaseCost: 12000, currentValue: 10800, warrantyExpiry: '2027-10-15', status: 'operational' as const, condition: 'good' as const, lastMaintenanceDate: '2026-05-30', nextMaintenanceDate: '2026-08-30' },
  { id: '10', name: 'Incubator', nameAr: 'حاضنة أطفال', type: 'neonatal', typeAr: 'حديثي الولادة', model: 'Drager Isolette 8000', serialNumber: 'SN-2024-112', manufacturer: 'Drager', departmentAr: 'حديثي الولادة', locationAr: 'وحدة الخداج - غرفة 1', purchaseCost: 55000, currentValue: 49500, warrantyExpiry: '2028-04-01', status: 'decommissioned' as const, condition: 'poor' as const, lastMaintenanceDate: '2026-04-01', nextMaintenanceDate: null },
];

export function Assets() {
  const { isRtl } = useRTL();
  const [assets] = useState(MOCK_ASSETS);
  const [deptFilter, setDeptFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filtered = assets.filter(a => {
    if (deptFilter !== 'all' && a.departmentAr !== deptFilter && a.departmentAr !== deptFilter) return false;
    if (statusFilter !== 'all' && a.status !== statusFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return a.nameAr.includes(q) || a.name.toLowerCase().includes(q) || a.serialNumber.toLowerCase().includes(q);
    }
    return true;
  });

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
            {isRtl ? 'الأصول والمعدات الطبية' : 'Medical Assets & Equipment'}
          </h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            {isRtl ? 'تتبع وإدارة الأصول الطبية' : 'Track and manage medical equipment assets'}
          </p>
        </div>

        <Card>
          <CardHeader
            title={isRtl ? 'المعدات الطبية' : 'Medical Equipment'}
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
                  options={[
                    { value: 'all', label: isRtl ? 'جميع الأقسام' : 'All Depts' },
                    { value: 'الأشعة', label: isRtl ? 'الأشعة' : 'Radiology' },
                    { value: 'العناية المركزة', label: isRtl ? 'العناية المركزة' : 'ICU' },
                    { value: 'الطوارئ', label: isRtl ? 'الطوارئ' : 'ER' },
                    { value: 'الجراحة', label: isRtl ? 'الجراحة' : 'Surgery' },
                  ]}
                  className="w-36"
                />
                <Select
                  value={statusFilter}
                  onChange={v => setStatusFilter(v as string)}
                  options={[
                    { value: 'all', label: isRtl ? 'جميع الحالات' : 'All Status' },
                    { value: 'operational', label: isRtl ? 'قيد التشغيل' : 'Operational' },
                    { value: 'under_maintenance', label: isRtl ? 'قيد الصيانة' : 'Maintenance' },
                    { value: 'decommissioned', label: isRtl ? 'مستبعد' : 'Decommissioned' },
                  ]}
                  className="w-36"
                />
              </div>
            }
          />
          <CardBody>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {filtered.map(asset => (
                <AssetCard key={asset.id} asset={asset} />
              ))}
            </div>
            {filtered.length === 0 && (
              <div className="text-center py-12 text-neutral-400">
                {isRtl ? 'لا توجد نتائج' : 'No results found'}
              </div>
            )}
          </CardBody>
        </Card>
      </div>
    </LayoutContent>
  );
}
