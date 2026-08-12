import { useState } from 'react';
import {
  Card, CardHeader, CardBody, Badge, Button, Select, LayoutContent, useRTL,
} from '@gula/ui-platform';

interface MaintenanceRecord {
  id: string;
  assetName: string;
  assetNameAr: string;
  type: 'preventive' | 'corrective' | 'emergency' | 'inspection';
  typeAr: string;
  description: string;
  descriptionAr: string;
  department: string;
  departmentAr: string;
  assignedTo: string;
  assignedToAr: string;
  scheduledDate: string;
  completionDate: string | null;
  cost: number;
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'critical';
}

const MOCK_MAINTENANCE: MaintenanceRecord[] = [
  { id: '1', assetName: 'CT Scanner', assetNameAr: 'الماسح المقطعي', type: 'preventive', typeAr: 'صيانة دورية', description: '6-month preventive maintenance and calibration', descriptionAr: 'صيانة دورية نصف سنوية ومعايرة', department: 'Radiology', departmentAr: 'الأشعة', assignedTo: 'Siemens maintenance team', assignedToAr: 'فريق صيانة سيمنز', scheduledDate: '2026-07-20', completionDate: null, cost: 3500, status: 'scheduled', priority: 'high' },
  { id: '2', assetName: 'X-Ray Machine', assetNameAr: 'جهاز أشعة سينية', type: 'corrective', typeAr: 'صيانة تصحيحية', description: 'Image distortion issue - tube replacement', descriptionAr: 'مشكلة تشويه الصورة - استبدال الأنبوب', department: 'Emergency', departmentAr: 'الطوارئ', assignedTo: 'Internal maintenance engineer', assignedToAr: 'مهندس الصيانة الداخلي', scheduledDate: '2026-07-16', completionDate: null, cost: 2500, status: 'in_progress', priority: 'critical' },
  { id: '3', assetName: 'Ventilator Set', assetNameAr: 'أجهزة التنفس', type: 'preventive', typeAr: 'صيانة دورية', description: 'Monthly ventilator check and sensor calibration', descriptionAr: 'فحص شهري لأجهزة التنفس ومعايرة الحساسات', department: 'ICU', departmentAr: 'العناية المركزة', assignedTo: 'Medical maintenance team', assignedToAr: 'فريق الصيانة الطبية', scheduledDate: '2026-07-18', completionDate: null, cost: 800, status: 'scheduled', priority: 'medium' },
  { id: '4', assetName: 'MRI Machine', assetNameAr: 'جهاز الرنين المغناطيسي', type: 'inspection', typeAr: 'تفتيش', description: 'Quarterly safety inspection and coolant check', descriptionAr: 'تفتيش سلامة ربع سنوي وفحص المبرد', department: 'Radiology', departmentAr: 'الأشعة', assignedTo: 'Philips maintenance team', assignedToAr: 'فريق صيانة فيليبس', scheduledDate: '2026-07-25', completionDate: null, cost: 1500, status: 'scheduled', priority: 'medium' },
  { id: '5', assetName: 'Dialysis Machine', assetNameAr: 'جهاز غسيل الكلى', type: 'emergency', typeAr: 'صيانة طارئة', description: 'Flow rate alarm - pump failure', descriptionAr: 'إنذار معدل التدفق - عطل في المضخة', department: 'Nephrology', departmentAr: 'الكلى', assignedTo: 'Internal maintenance engineer', assignedToAr: 'مهندس الصيانة الداخلي', scheduledDate: '2026-07-15', completionDate: '2026-07-15', cost: 1200, status: 'completed', priority: 'critical' },
  { id: '6', assetName: 'Anesthesia Machine', assetNameAr: 'جهاز التخدير', type: 'preventive', typeAr: 'صيانة دورية', description: 'Annual preventive maintenance and safety check', descriptionAr: 'صيانة دورية سنوية وفحص سلامة', department: 'Surgery', departmentAr: 'الجراحة', assignedTo: 'GE maintenance team', assignedToAr: 'فريق صيانة GE', scheduledDate: '2026-08-01', completionDate: null, cost: 2000, status: 'scheduled', priority: 'high' },
  { id: '7', assetName: 'Defibrillator', assetNameAr: 'مزيل الرجفان', type: 'inspection', typeAr: 'تفتيش', description: 'Battery test and charge verification', descriptionAr: 'اختبار البطارية والتحقق من الشحن', department: 'Emergency', departmentAr: 'الطوارئ', assignedTo: 'Medical maintenance team', assignedToAr: 'فريق الصيانة الطبية', scheduledDate: '2026-07-19', completionDate: null, cost: 300, status: 'scheduled', priority: 'medium' },
  { id: '8', assetName: 'Ultrasound', assetNameAr: 'جهاز الموجات فوق الصوتية', type: 'corrective', typeAr: 'صيانة تصحيحية', description: 'Probe cable replacement', descriptionAr: 'استبدال كابل المسبار', department: 'Gynecology', departmentAr: 'النسائية', assignedTo: 'Samsung maintenance team', assignedToAr: 'فريق صيانة سامسونج', scheduledDate: '2026-07-17', completionDate: '2026-07-17', cost: 1800, status: 'completed', priority: 'high' },
];

export function Maintenance() {
  const { isRtl } = useRTL();
  const [records] = useState(MOCK_MAINTENANCE);
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterPriority, setFilterPriority] = useState('all');

  const filtered = records.filter(r => {
    if (filterStatus !== 'all' && r.status !== filterStatus) return false;
    if (filterPriority !== 'all' && r.priority !== filterPriority) return false;
    return true;
  });

  const statusColors: Record<string, 'primary' | 'warning' | 'success' | 'danger'> = {
    scheduled: 'primary',
    in_progress: 'warning',
    completed: 'success',
    cancelled: 'danger',
  };

  const priorityColors: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    low: 'success',
    medium: 'info',
    high: 'warning',
    critical: 'danger',
  };

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
            {isRtl ? 'إدارة الصيانة' : 'Maintenance Management'}
          </h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            {isRtl ? 'جدولة ومتابعة صيانة المعدات الطبية' : 'Schedule and track medical equipment maintenance'}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { label: 'صيانة مجدولة', labelEn: 'Scheduled', value: records.filter(r => r.status === 'scheduled').length, color: 'bg-blue-500' },
            { label: 'قيد التنفيذ', labelEn: 'In Progress', value: records.filter(r => r.status === 'in_progress').length, color: 'bg-yellow-500' },
            { label: 'مكتملة', labelEn: 'Completed', value: records.filter(r => r.status === 'completed').length, color: 'bg-green-500' },
            { label: 'حرجة', labelEn: 'Critical', value: records.filter(r => r.priority === 'critical' && r.status !== 'completed').length, color: 'bg-red-500' },
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
          <CardHeader
            title={isRtl ? 'جدول الصيانة' : 'Maintenance Schedule'}
            action={
              <div className="flex items-center gap-3">
                <Select
                  value={filterStatus}
                  onChange={e => setFilterStatus(e.target.value)}
                  options={[
                    { value: 'all', label: isRtl ? 'جميع الحالات' : 'All' },
                    { value: 'scheduled', label: isRtl ? 'مجدول' : 'Scheduled' },
                    { value: 'in_progress', label: isRtl ? 'قيد التنفيذ' : 'In Progress' },
                    { value: 'completed', label: isRtl ? 'مكتمل' : 'Completed' },
                    { value: 'cancelled', label: isRtl ? 'ملغي' : 'Cancelled' },
                  ]}
                  className="w-36"
                />
                <Select
                  value={filterPriority}
                  onChange={e => setFilterPriority(e.target.value)}
                  options={[
                    { value: 'all', label: isRtl ? 'جميع الأولويات' : 'All Priority' },
                    { value: 'critical', label: isRtl ? 'حرج' : 'Critical' },
                    { value: 'high', label: isRtl ? 'عالٍ' : 'High' },
                    { value: 'medium', label: isRtl ? 'متوسط' : 'Medium' },
                    { value: 'low', label: isRtl ? 'منخفض' : 'Low' },
                  ]}
                  className="w-36"
                />
                <Button>{isRtl ? 'إضافة صيانة' : 'Add Record'}</Button>
              </div>
            }
          />
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-neutral-200 dark:border-neutral-700">
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الجهاز' : 'Equipment'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'النوع' : 'Type'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'القسم' : 'Dept.'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'التاريخ المجدول' : 'Scheduled'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'التكلفة' : 'Cost'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الأولوية' : 'Priority'}</th>
                    <th className="text-right p-3 font-medium text-neutral-500">{isRtl ? 'الحالة' : 'Status'}</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(r => (
                    <tr key={r.id} className="border-b border-neutral-100 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800/50">
                      <td className="p-3">
                        <p className="font-medium text-neutral-900 dark:text-neutral-50">{isRtl ? r.assetNameAr : r.assetName}</p>
                        <p className="text-xs text-neutral-400">{isRtl ? r.descriptionAr : r.description}</p>
                      </td>
                      <td className="p-3">
                        <Badge>{isRtl ? r.typeAr : r.type}</Badge>
                      </td>
                      <td className="p-3 text-neutral-700 dark:text-neutral-300">{isRtl ? r.departmentAr : r.department}</td>
                      <td className="p-3 text-sm text-neutral-500">{r.scheduledDate}</td>
                      <td className="p-3 text-sm font-medium">${r.cost.toLocaleString()}</td>
                      <td className="p-3">
                        <Badge variant={priorityColors[r.priority]}>
                          {isRtl ? (
                            r.priority === 'critical' ? 'حرج' : r.priority === 'high' ? 'عالٍ' : r.priority === 'medium' ? 'متوسط' : 'منخفض'
                          ) : r.priority}
                        </Badge>
                      </td>
                      <td className="p-3">
                        <Badge variant={statusColors[r.status]}>
                          {isRtl ? (
                            r.status === 'scheduled' ? 'مجدول' : r.status === 'in_progress' ? 'قيد التنفيذ' : r.status === 'completed' ? 'مكتمل' : 'ملغي'
                          ) : r.status}
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
