import { Card, CardHeader, CardBody, Badge, useRTL } from '@gula/ui-platform';

interface AssetCardProps {
  asset: {
    id: string;
    name: string;
    nameAr: string;
    type: string;
    typeAr: string;
    model: string;
    serialNumber: string;
    manufacturer: string;
    departmentAr: string;
    locationAr: string;
    purchaseCost: number;
    currentValue: number;
    warrantyExpiry: string;
    status: 'operational' | 'under_maintenance' | 'repair' | 'decommissioned' | 'reserve';
    condition: 'excellent' | 'good' | 'fair' | 'poor';
    lastMaintenanceDate: string | null;
    nextMaintenanceDate: string | null;
  };
}

const STATUS_STYLES: Record<string, { badge: 'success' | 'warning' | 'danger' | 'info' | 'primary'; label: string; labelAr: string }> = {
  operational: { badge: 'success', label: 'Operational', labelAr: 'قيد التشغيل' },
  under_maintenance: { badge: 'warning', label: 'Under Maintenance', labelAr: 'قيد الصيانة' },
  repair: { badge: 'danger', label: 'Repair', labelAr: 'إصلاح' },
  decommissioned: { badge: 'danger', label: 'Decommissioned', labelAr: 'مستبعد' },
  reserve: { badge: 'info', label: 'Reserve', labelAr: 'احتياطي' },
};

const CONDITION_COLORS: Record<string, string> = {
  excellent: 'text-green-600 dark:text-green-400',
  good: 'text-blue-600 dark:text-blue-400',
  fair: 'text-yellow-600 dark:text-yellow-400',
  poor: 'text-red-600 dark:text-red-400',
};

export function AssetCard({ asset }: AssetCardProps) {
  const { isRtl } = useRTL();
  const status = STATUS_STYLES[asset.status];
  const depreciation = asset.purchaseCost > 0
    ? Math.round((1 - asset.currentValue / asset.purchaseCost) * 100)
    : 0;

  return (
    <Card>
      <CardHeader
        title={
          <div>
            <p className="font-bold text-neutral-900 dark:text-neutral-50">{isRtl ? asset.nameAr : asset.name}</p>
            <p className="text-xs text-neutral-400">{asset.model} | {asset.serialNumber}</p>
          </div>
        }
        action={<Badge variant={status.badge}>{isRtl ? status.labelAr : status.label}</Badge>}
      />
      <CardBody>
        <div className="space-y-2 text-sm">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <p className="text-xs text-neutral-400">{isRtl ? 'النوع' : 'Type'}</p>
              <p className="font-medium text-neutral-700 dark:text-neutral-300">{isRtl ? asset.typeAr : asset.type}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-400">{isRtl ? 'الشركة المصنعة' : 'Manufacturer'}</p>
              <p className="font-medium text-neutral-700 dark:text-neutral-300">{asset.manufacturer}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-400">{isRtl ? 'القسم' : 'Dept.'}</p>
              <p className="font-medium text-neutral-700 dark:text-neutral-300">{isRtl ? asset.departmentAr : asset.departmentAr}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-400">{isRtl ? 'الموقع' : 'Location'}</p>
              <p className="font-medium text-neutral-700 dark:text-neutral-300">{isRtl ? asset.locationAr : asset.locationAr}</p>
            </div>
          </div>

          <div className="border-t border-neutral-100 dark:border-neutral-800 pt-2 grid grid-cols-2 gap-2">
            <div>
              <p className="text-xs text-neutral-400">{isRtl ? 'تكلفة الشراء' : 'Purchase Cost'}</p>
              <p className="font-medium text-neutral-700 dark:text-neutral-300">${asset.purchaseCost.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-400">{isRtl ? 'القيمة الحالية' : 'Current Value'}</p>
              <p className="font-medium text-neutral-700 dark:text-neutral-300">${asset.currentValue.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs text-neutral-400">{isRtl ? 'الاستهلاك' : 'Depreciation'}</p>
              <p className="font-medium text-neutral-500">{depreciation}%</p>
            </div>
            <div>
              <p className="text-xs text-neutral-400">{isRtl ? 'الضمان حتى' : 'Warranty Until'}</p>
              <p className="font-medium text-neutral-700 dark:text-neutral-300">{asset.warrantyExpiry}</p>
            </div>
          </div>

          <div className="flex items-center justify-between pt-1">
            <span className={`text-xs font-medium ${CONDITION_COLORS[asset.condition]}`}>
              {isRtl ? (
                asset.condition === 'excellent' ? 'ممتاز' : asset.condition === 'good' ? 'جيد' : asset.condition === 'fair' ? 'متوسط' : 'سيء'
              ) : asset.condition}
            </span>
            {asset.nextMaintenanceDate && (
              <span className="text-xs text-neutral-400">
                {isRtl ? `الصيانة القادمة: ${asset.nextMaintenanceDate}` : `Next maint.: ${asset.nextMaintenanceDate}`}
              </span>
            )}
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
