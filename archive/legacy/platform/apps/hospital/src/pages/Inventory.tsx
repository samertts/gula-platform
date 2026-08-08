import { useState } from 'react';
import {
  Card, CardHeader, CardBody, Badge, Select, Input, LayoutContent, useRTL,
} from '@gula/ui-platform';

interface InventoryItem {
  id: string;
  name: string;
  nameAr: string;
  category: string;
  categoryAr: string;
  quantity: number;
  minQuantity: number;
  maxQuantity: number;
  unit: string;
  unitAr: string;
  location: string;
  locationAr: string;
  expiryDate: string | null;
  supplier: string;
  supplierAr: string;
  unitCost: number;
  status: 'in_stock' | 'low_stock' | 'out_of_stock' | 'expired' | 'ordered';
}

const MOCK_INVENTORY: InventoryItem[] = [
  { id: '1', name: 'Amoxicillin 500mg', nameAr: 'أموكسيسيلين 500 ملغ', category: 'Antibiotics', categoryAr: 'مضادات حيوية', quantity: 2500, minQuantity: 500, maxQuantity: 5000, unit: 'tab', unitAr: 'قرص', location: 'Pharmacy A', locationAr: 'صيدلية A', expiryDate: '2027-08-15', supplier: 'Iraqi Pharma', supplierAr: 'الصيدلانية العراقية', unitCost: 0.15, status: 'in_stock' },
  { id: '2', name: 'Paracetamol 500mg', nameAr: 'باراسيتامول 500 ملغ', category: 'Analgesics', categoryAr: 'مسكنات', quantity: 5000, minQuantity: 1000, maxQuantity: 10000, unit: 'tab', unitAr: 'قرص', location: 'Pharmacy B', locationAr: 'صيدلية B', expiryDate: '2028-01-20', supplier: 'Universal Pharma', supplierAr: 'يونيفرسال فارما', unitCost: 0.05, status: 'in_stock' },
  { id: '3', name: 'Insulin Glargine', nameAr: 'أنسولين غلارجين', category: 'Hormones', categoryAr: 'هرمونات', quantity: 120, minQuantity: 100, maxQuantity: 400, unit: 'vial', unitAr: 'قنينة', location: 'Fridge A', locationAr: 'الثلاجة A', expiryDate: '2027-03-10', supplier: 'Sanofi Iraq', supplierAr: 'سانوفي العراق', unitCost: 12.50, status: 'low_stock' },
  { id: '4', name: 'Surgical Gloves (Sterile)', nameAr: 'قفازات جراحية (معقمة)', category: 'Supplies', categoryAr: 'مستلزمات', quantity: 3500, minQuantity: 500, maxQuantity: 5000, unit: 'pair', unitAr: 'زوج', location: 'Store 1', locationAr: 'مخزن 1', expiryDate: null, supplier: 'MedTech Supplies', supplierAr: 'مستلزمات ميدتيك', unitCost: 0.30, status: 'in_stock' },
  { id: '5', name: 'Normal Saline 500ml', nameAr: 'محلول ملحي 500 مل', category: 'IV Fluids', categoryAr: 'محاليل وريدية', quantity: 800, minQuantity: 200, maxQuantity: 1000, unit: 'bag', unitAr: 'كيس', location: 'Store 2', locationAr: 'مخزن 2', expiryDate: '2027-11-30', supplier: 'Gulf Medical', supplierAr: 'خليج ميديكال', unitCost: 0.80, status: 'in_stock' },
  { id: '6', name: 'Blood Collection Tubes', nameAr: 'أنابيب جمع الدم', category: 'Lab Supplies', categoryAr: 'مستلزمات مختبر', quantity: 50, minQuantity: 200, maxQuantity: 1000, unit: 'box', unitAr: 'علبة', location: 'Lab Store', locationAr: 'مخزن المختبر', expiryDate: '2028-06-01', supplier: 'LabTech Iraq', supplierAr: 'لاب تك العراق', unitCost: 5.00, status: 'out_of_stock' },
  { id: '7', name: 'Morphine 10mg/ml', nameAr: 'مورفين 10 ملغ/مل', category: 'Narcotics', categoryAr: 'مخدرات', quantity: 200, minQuantity: 50, maxQuantity: 300, unit: 'amp', unitAr: 'أمبولة', location: 'Narcotic Cabinet', locationAr: 'خزانة المخدرات', expiryDate: '2027-05-15', supplier: 'Narcotics Control', supplierAr: 'مكافحة المخدرات', unitCost: 2.50, status: 'in_stock' },
  { id: '8', name: 'Bandage Gauze', nameAr: 'شاش طبي', category: 'Supplies', categoryAr: 'مستلزمات', quantity: 2000, minQuantity: 300, maxQuantity: 3000, unit: 'roll', unitAr: 'لفة', location: 'Store 1', locationAr: 'مخزن 1', expiryDate: null, supplier: 'MedTech Supplies', supplierAr: 'مستلزمات ميدتيك', unitCost: 0.40, status: 'in_stock' },
  { id: '9', name: 'Atropine 1mg', nameAr: 'أتروبين 1 ملغ', category: 'Emergency', categoryAr: 'طوارئ', quantity: 100, minQuantity: 80, maxQuantity: 200, unit: 'amp', unitAr: 'أمبولة', location: 'Crash Cart', locationAr: 'عربة الطوارئ', expiryDate: '2027-09-01', supplier: 'Iraqi Pharma', supplierAr: 'الصيدلانية العراقية', unitCost: 1.00, status: 'low_stock' },
  { id: '10', name: 'Syringe 5ml', nameAr: 'حقنة 5 مل', category: 'Supplies', categoryAr: 'مستلزمات', quantity: 10000, minQuantity: 2000, maxQuantity: 15000, unit: 'piece', unitAr: 'قطعة', location: 'Store 3', locationAr: 'مخزن 3', expiryDate: null, supplier: 'Universal Pharma', supplierAr: 'يونيفرسال فارما', unitCost: 0.10, status: 'in_stock' },
];

const CATEGORIES = ['الكل', 'مضادات حيوية', 'مسكنات', 'مستلزمات', 'محاليل وريدية', 'هرمونات', 'طوارئ'];

export function Inventory() {
  const { isRtl } = useRTL();
  const [items] = useState(MOCK_INVENTORY);
  const [catFilter, setCatFilter] = useState('الكل');
  const [searchQuery, setSearchQuery] = useState('');

  const filtered = items.filter(item => {
    if (catFilter !== 'الكل' && item.categoryAr !== catFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return item.nameAr.includes(q) || item.name.toLowerCase().includes(q);
    }
    return true;
  });

  const statusColors: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    in_stock: 'success',
    low_stock: 'warning',
    out_of_stock: 'danger',
    expired: 'danger',
    ordered: 'info',
  };

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
            {isRtl ? 'إدارة المخزون' : 'Inventory Management'}
          </h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            {isRtl ? 'مخزون المستلزمات الطبية والأدوية' : 'Medical supplies and pharmaceutical inventory'}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {[
            { label: 'متوفر', labelEn: 'In Stock', value: items.filter(i => i.status === 'in_stock').length, color: 'bg-green-500' },
            { label: 'مخزون منخفض', labelEn: 'Low Stock', value: items.filter(i => i.status === 'low_stock').length, color: 'bg-yellow-500' },
            { label: 'نفذ', labelEn: 'Out of Stock', value: items.filter(i => i.status === 'out_of_stock').length, color: 'bg-red-500' },
            { label: 'منتهي الصلاحية', labelEn: 'Expired', value: items.filter(i => i.status === 'expired').length, color: 'bg-red-500' },
            { label: 'قيد الطلب', labelEn: 'Ordered', value: items.filter(i => i.status === 'ordered').length, color: 'bg-blue-500' },
          ].map(s => (
            <Card key={s.label} variant="elevated" padding="md">
              <CardBody>
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${s.color}`} />
                  <div>
                    <p className="text-xs text-neutral-500">{isRtl ? s.label : s.labelEn}</p>
                    <p className="text-xl font-bold text-neutral-900 dark:text-neutral-50">{s.value}</p>
                  </div>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>

        <Card>
          <CardHeader
            title={isRtl ? 'المخزون' : 'Inventory'}
            action={
              <div className="flex items-center gap-3">
                <Input
                  placeholder={isRtl ? 'بحث...' : 'Search...'}
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="w-48"
                />
                <Select
                  value={catFilter}
                  onChange={v => setCatFilter(v as string)}
                  options={CATEGORIES.map(c => ({ value: c, label: c }))}
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
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الصنف' : 'Item'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'التصنيف' : 'Category'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الكمية' : 'Qty'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الحد الأدنى' : 'Min'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الموقع' : 'Location'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'تاريخ الصلاحية' : 'Expiry'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الحالة' : 'Status'}</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(item => (
                    <tr key={item.id} className="border-b border-neutral-100 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800/50">
                      <td className="p-3">
                        <p className="font-medium text-neutral-900 dark:text-neutral-50">{isRtl ? item.nameAr : item.name}</p>
                        <p className="text-xs text-neutral-400">{item.unitCost > 0 ? `$${item.unitCost.toFixed(2)}/${item.unitAr}` : ''}</p>
                      </td>
                      <td className="p-3"><Badge>{isRtl ? item.categoryAr : item.category}</Badge></td>
                      <td className="p-3">
                        <span className={`font-medium ${
                          item.quantity <= item.minQuantity ? 'text-red-600 dark:text-red-400' : 'text-neutral-900 dark:text-neutral-50'
                        }`}>
                          {item.quantity}
                        </span>
                      </td>
                      <td className="p-3 text-neutral-500">{item.minQuantity}</td>
                      <td className="p-3 text-neutral-700 dark:text-neutral-300">{isRtl ? item.locationAr : item.location}</td>
                      <td className="p-3 text-sm text-neutral-500">
                        {item.expiryDate || <span className="text-neutral-300">—</span>}
                      </td>
                      <td className="p-3">
                        <Badge variant={statusColors[item.status]}>
                          {isRtl ? (
                            item.status === 'in_stock' ? 'متوفر' : item.status === 'low_stock' ? 'منخفض' : item.status === 'out_of_stock' ? 'نفذ' : item.status === 'expired' ? 'منتهي' : 'قيد الطلب'
                          ) : item.status}
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
    </LayoutContent>
  );
}
