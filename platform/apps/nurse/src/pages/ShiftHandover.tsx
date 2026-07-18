import { useState, useEffect } from 'react';
import { Card, Button, Modal, Input, Select, LoadingSpinner, EmptyState, Badge } from '@gula/ui-platform';
import { useNurse } from '../contexts/NurseContext';
import { ShiftSummary } from '../components/ShiftSummary';
import { getShiftArabic } from '../utils/routes';

interface Handover {
  id: string;
  shift: 'morning' | 'evening' | 'night';
  date: string;
  fromNurse: string;
  toNurse: string;
  patientCount: number;
  criticalCount: number;
  notes: string;
  completed: boolean;
}

const MOCK_HANDOVERS: Handover[] = [
  { id: '1', shift: 'morning', date: '2026-07-16', fromNurse: 'نور الرفاعي', toNurse: 'سارة الجبوري', patientCount: 12, criticalCount: 2, notes: 'مريضان في العناية المركزة بحاجة مراقبة مستمرة', completed: true },
  { id: '2', shift: 'evening', date: '2026-07-15', fromNurse: 'سارة الجبوري', toNurse: 'نور الرفاعي', patientCount: 15, criticalCount: 3, notes: 'تم إعطاء جميع الأدوية المقررة', completed: true },
];

export default function ShiftHandover() {
  const [handovers, setHandovers] = useState<Handover[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    setTimeout(() => { setHandovers(MOCK_HANDOVERS); setLoading(false); }, 500);
  }, []);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">تسليم الوردية</h1>
          <p className="text-gray-500">تسليم واستلام المناوبات التمريضية</p>
        </div>
        <Button variant="primary" onClick={() => setShowModal(true)}>تسليم جديد</Button>
      </div>

      {handovers.length === 0 ? (
        <EmptyState title="لا يوجد تسليم" description="لم يتم تسجيل أي تسليم وردية بعد" />
      ) : (
        <div className="space-y-4">
          {handovers.map(h => (
            <Card key={h.id}>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold">{getShiftArabic(h.shift)} - {h.date}</h3>
                  <p className="text-sm text-gray-500">من: {h.fromNurse} → إلى: {h.toNurse}</p>
                  <p className="text-sm">المرضى: {h.patientCount} | حالات حرجة: {h.criticalCount}</p>
                  <p className="text-sm mt-2">{h.notes}</p>
                </div>
                <Badge variant={h.completed ? 'success' : 'warning'}>{h.completed ? 'مكتمل' : 'قيد الانتظار'}</Badge>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal open={showModal} onClose={() => setShowModal(false)} title="تسليم وردية جديد" size="lg">
        <div className="space-y-4">
          <Select label="الوردية" options={[{ value: 'morning', label: 'صباحية' }, { value: 'evening', label: 'مسائية' }, { value: 'night', label: 'ليلية' }]} />
          <Input label="تسليم إلى" placeholder="اسم الممرض/ة المستلم" />
          <Input label="عدد المرضى" type="number" />
          <Input label="عدد الحالات الحرجة" type="number" />
          <Input label="ملاحظات" placeholder="ملاحظات التسليم" />
          <div className="flex justify-left gap-2 pt-4">
            <Button variant="primary">تأكيد التسليم</Button>
            <Button variant="ghost" onClick={() => setShowModal(false)}>إلغاء</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
