import { useState, useEffect } from 'react';
import { Card, Button, Modal, Input, Select, LoadingSpinner, EmptyState, Badge } from '@gula/ui-platform';
import { useNurse } from '../contexts/NurseContext';
import { CarePlanCard } from '../components/CarePlanCard';

interface Plan {
  id: string;
  patientName: string;
  patientId: string;
  ward: string;
  diagnosis: string;
  goals: string[];
  interventions: string[];
  startDate: string;
  endDate: string;
  status: 'active' | 'completed' | 'review' | 'cancelled';
  priority: 'low' | 'medium' | 'high';
}

const MOCK_PLANS: Plan[] = [
  { id: '1', patientName: 'أحمد علي', patientId: 'P-001', ward: 'icu', diagnosis: 'قصور قلب', goals: ['تحسين النتاج القلبي', 'تقليل الوذمة'], interventions: ['مراقبة العلامات الحيوية كل ساعة', 'إعطاء مدرات البول'], startDate: '2026-07-10', endDate: '2026-07-20', status: 'active', priority: 'high' },
  { id: '2', patientName: 'مريم خالد', patientId: 'P-002', ward: 'general', diagnosis: 'التهاب رئوي', goals: ['تحسين التنفس', 'خفض الحرارة'], interventions: ['علاج تنفسي', 'مراقبة تشبع الأكسجين'], startDate: '2026-07-12', endDate: '2026-07-18', status: 'active', priority: 'medium' },
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
