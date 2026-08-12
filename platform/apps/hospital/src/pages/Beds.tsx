import { useState } from 'react';
import { Card, CardHeader, CardBody, Select, LayoutContent, useRTL } from '@gula/ui-platform';
import { OccupancyGrid } from '../components/OccupancyGrid';

const DEPARTMENTS = [
  { value: 'all', label: { ar: 'جميع الأقسام', en: 'All Departments' } },
  { value: 'er', label: { ar: 'الطوارئ', en: 'Emergency' } },
  { value: 'internal', label: { ar: 'الباطنية', en: 'Internal Medicine' } },
  { value: 'surgery', label: { ar: 'الجراحة', en: 'Surgery' } },
  { value: 'pediatrics', label: { ar: 'طب الأطفال', en: 'Pediatrics' } },
  { value: 'icu', label: { ar: 'العناية المركزة', en: 'ICU' } },
  { value: 'maternity', label: { ar: 'النسائية', en: 'Maternity' } },
  { value: 'orthopedics', label: { ar: 'العظام', en: 'Orthopedics' } },
];

export function Beds() {
  const { isRtl } = useRTL();
  const [selectedDept, setSelectedDept] = useState('all');

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
              {isRtl ? 'إدارة الأسرة' : 'Bed Management'}
            </h1>
            <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
              {isRtl ? 'عرض وإدارة إشغال الأسرة في المستشفى' : 'View and manage hospital bed occupancy'}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { label: 'الأسرة الكلية', labelEn: 'Total Beds', value: 200, color: 'bg-neutral-500' },
            { label: 'متاح', labelEn: 'Available', value: 58, color: 'bg-green-500' },
            { label: 'مشغول', labelEn: 'Occupied', value: 135, color: 'bg-red-500' },
            { label: 'صيانة', labelEn: 'Maintenance', value: 7, color: 'bg-yellow-500' },
          ].map(s => (
            <Card key={s.label} variant="elevated" padding="md">
              <CardBody>
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${s.color}`} />
                  <div>
                    <p className="text-sm text-neutral-500 dark:text-neutral-400">
                      {isRtl ? s.label : s.labelEn}
                    </p>
                    <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">{s.value}</p>
                  </div>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>

        <Card>
          <CardHeader
            title={isRtl ? 'خريطة إشغال الأسرة' : 'Bed Occupancy Map'}
            action={
              <Select
                value={selectedDept}
                onChange={e => setSelectedDept(e.target.value)}
                options={DEPARTMENTS.map(d => ({
                  value: d.value,
                  label: isRtl ? d.label.ar : d.label.en,
                }))}
                className="w-44"
              />
            }
          />
          <CardBody>
            <OccupancyGrid departmentFilter={selectedDept} />
          </CardBody>
        </Card>
      </div>
    </LayoutContent>
  );
}
