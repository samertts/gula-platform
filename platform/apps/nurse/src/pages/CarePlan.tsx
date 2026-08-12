import { useEffect, useState } from 'react';
import { Card, Button, Modal, Input, Select, LoadingSpinner, EmptyState } from '@gula/ui-platform';
import { useNurse } from '../contexts/NurseContext';
import { CarePlanCard } from '../components/CarePlanCard';
import type { CarePlan as Plan } from '@/utils/types';

const MOCK_PLANS: Plan[] = [
  {
    id: '1',
    patientName: 'أحمد علي',
    patientId: 'P-001',
    bed: 'ICU-01',
    diagnosis: 'قصور قلب',
    goals: [
      { id: 'g1', description: 'تحسين النتاج القلبي', targetDate: '2026-07-20', status: 'pending' },
      { id: 'g2', description: 'تقليل الوذمة', targetDate: '2026-07-20', status: 'pending' },
    ],
    interventions: [
      { id: 'i1', description: 'مراقبة العلامات الحيوية كل ساعة', frequency: 'كل ساعة', status: 'active' },
      { id: 'i2', description: 'إعطاء مدرات البول', frequency: 'حسب الوصفة', status: 'active' },
    ],
    startDate: '2026-07-10',
    reviewDate: '2026-07-20',
    status: 'active',
    createdBy: 'nurse-demo',
  },
  {
    id: '2',
    patientName: 'مريم خالد',
    patientId: 'P-002',
    bed: 'Ward-12',
    diagnosis: 'التهاب رئوي',
    goals: [
      { id: 'g3', description: 'تحسين التنفس', targetDate: '2026-07-18', status: 'pending' },
      { id: 'g4', description: 'خفض الحرارة', targetDate: '2026-07-18', status: 'pending' },
    ],
    interventions: [
      { id: 'i3', description: 'علاج تنفسي', frequency: 'مرتان يومياً', status: 'active' },
      { id: 'i4', description: 'مراقبة تشبع الأكسجين', frequency: 'كل 4 ساعات', status: 'active' },
    ],
    startDate: '2026-07-12',
    reviewDate: '2026-07-18',
    status: 'active',
    createdBy: 'nurse-demo',
  },
];

export default function CarePlan() {
  const { selectedWard } = useNurse();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    setTimeout(() => { setPlans(MOCK_PLANS); setLoading(false); }, 500);
  }, [selectedWard]);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">خطط الرعاية التمريضية</h1>
          <p className="text-gray-500">إدارة وتحديث خطط الرعاية للمرضى</p>
        </div>
        <Button variant="primary" onClick={() => setShowModal(true)}>إضافة خطة جديدة</Button>
      </div>

      {plans.length === 0 ? (
        <EmptyState title="لا توجد خطط رعاية" description="لم يتم إنشاء أي خطط رعاية بعد" />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {plans.map(plan => <CarePlanCard key={plan.id} plan={plan} />)}
        </div>
      )}

      <Modal open={showModal} onClose={() => setShowModal(false)} title="إضافة خطة رعاية جديدة" size="lg">
        <div className="space-y-4">
          <Input label="المريض" placeholder="اختر المريض" />
          <Input label="التشخيص" placeholder="التشخيص الطبي" />
          <Select label="الأولوية" options={[{ value: 'low', label: 'منخفضة' }, { value: 'medium', label: 'متوسطة' }, { value: 'high', label: 'عالية' }]} />
          <div className="flex justify-left gap-2 pt-4">
            <Button variant="primary">حفظ الخطة</Button>
            <Button variant="ghost" onClick={() => setShowModal(false)}>إلغاء</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
