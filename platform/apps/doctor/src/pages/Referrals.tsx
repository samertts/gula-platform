import { useState } from 'react';
import { Card, CardHeader, CardBody, Button, Badge, Input, LayoutContent } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';

interface Referral {
  id: string;
  patientName: string;
  patientNameAr: string;
  fromSpecialty: string;
  fromSpecialtyAr: string;
  toSpecialty: string;
  toSpecialtyAr: string;
  toDoctor: string;
  reason: string;
  reasonAr: string;
  priority: 'routine' | 'urgent' | 'emergency';
  status: 'pending' | 'accepted' | 'completed' | 'rejected';
  createdAt: string;
}

const MOCK_REFERRALS: Referral[] = [
  { id: 'ref1', patientName: 'Ahmed Ali', patientNameAr: 'أحمد علي', fromSpecialty: 'Internal Medicine', fromSpecialtyAr: 'طب باطني', toSpecialty: 'Cardiology', toSpecialtyAr: 'قلب', toDoctor: 'Dr. Mahmoud', reason: 'Chest pain evaluation', reasonAr: 'تقييم ألم الصدر', priority: 'urgent', status: 'accepted', createdAt: '2024-12-14' },
  { id: 'ref2', patientName: 'Sara Mohammed', patientNameAr: 'سارة محمد', fromSpecialty: 'Family Medicine', fromSpecialtyAr: 'طب أسرة', toSpecialty: 'Endocrinology', toSpecialtyAr: 'غدد صماء', toDoctor: 'Dr. Huda', reason: 'Uncontrolled diabetes', reasonAr: 'سكري غير منضبط', priority: 'routine', status: 'pending', createdAt: '2024-12-15' },
];

const specialties = [
  { value: 'cardiology', label: 'Cardiology', labelAr: 'قلب' },
  { value: 'endocrinology', label: 'Endocrinology', labelAr: 'غدد صماء' },
  { value: 'neurology', label: 'Neurology', labelAr: 'أعصاب' },
  { value: 'orthopedics', label: 'Orthopedics', labelAr: 'عظام' },
  { value: 'pediatrics', label: 'Pediatrics', labelAr: 'اطفال' },
  { value: 'psychiatry', label: 'Psychiatry', labelAr: 'نفسي' },
  { value: 'surgery', label: 'Surgery', labelAr: 'جراحة' },
  { value: 'urology', label: 'Urology', labelAr: 'مسالك بولية' },
  { value: 'ophthalmology', label: 'Ophthalmology', labelAr: 'عيون' },
  { value: 'ent', label: 'ENT', labelAr: 'أنف وأذن وحنجرة' },
];

export function Referrals() {
  const { isRtl } = useRTL();
  const [referrals, setReferrals] = useState<Referral[]>(MOCK_REFERRALS);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    patientName: '',
    patientNameAr: '',
    toSpecialty: '',
    toDoctor: '',
    reason: '',
    reasonAr: '',
    priority: 'routine' as 'routine' | 'urgent' | 'emergency',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const ref: Referral = {
      id: `ref-${Date.now()}`,
      patientName: form.patientName,
      patientNameAr: form.patientNameAr,
      fromSpecialty: 'Internal Medicine',
      fromSpecialtyAr: 'طب باطني',
      toSpecialty: specialties.find(s => s.value === form.toSpecialty)?.label || form.toSpecialty,
      toSpecialtyAr: specialties.find(s => s.value === form.toSpecialty)?.labelAr || form.toSpecialty,
      toDoctor: form.toDoctor,
      reason: form.reason,
      reasonAr: form.reasonAr,
      priority: form.priority,
      status: 'pending',
      createdAt: new Date().toISOString().split('T')[0],
    };
    setReferrals(prev => [ref, ...prev]);
    setShowForm(false);
    setForm({ patientName: '', patientNameAr: '', toSpecialty: '', toDoctor: '', reason: '', reasonAr: '', priority: 'routine' });
  };

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
            {isRtl ? 'التحويلات الطبية' : 'Referrals'}
          </h1>
          <Button variant="primary" onClick={() => setShowForm(true)}>
            {isRtl ? 'تحويل جديد' : 'New Referral'}
          </Button>
        </div>

        {showForm && (
          <Card>
            <CardHeader title={isRtl ? 'تحويل مريض' : 'Refer Patient'} />
            <CardBody>
              <form onSubmit={handleSubmit} className="space-y-4">
                <Input label={isRtl ? 'اسم المريض (عربي)' : 'Patient Name (Arabic)'} value={form.patientNameAr} onChange={e => setForm(p => ({ ...p, patientNameAr: e.target.value }))} required />
                <Input label={isRtl ? 'اسم المريض (إنجليزي)' : 'Patient Name (English)'} value={form.patientName} onChange={e => setForm(p => ({ ...p, patientName: e.target.value }))} />
                <div>
                  <label className="block text-sm font-medium mb-1">{isRtl ? 'التخصص المحول إليه' : 'Specialty'}</label>
                  <select value={form.toSpecialty} onChange={e => setForm(p => ({ ...p, toSpecialty: e.target.value }))} className="w-full rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-3 py-2 text-sm" required>
                    <option value="">{isRtl ? 'اختر التخصص' : 'Select specialty'}</option>
                    {specialties.map(s => <option key={s.value} value={s.value}>{isRtl ? s.labelAr : s.label}</option>)}
                  </select>
                </div>
                <Input label={isRtl ? 'اسم الطبيب المحول إليه' : 'Referral Doctor'} value={form.toDoctor} onChange={e => setForm(p => ({ ...p, toDoctor: e.target.value }))} />
                <div>
                  <label className="block text-sm font-medium mb-1">{isRtl ? 'الأولوية' : 'Priority'}</label>
                  <select value={form.priority} onChange={e => setForm(p => ({ ...p, priority: e.target.value as any }))} className="w-full rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-3 py-2 text-sm">
                    <option value="routine">{isRtl ? 'روتيني' : 'Routine'}</option>
                    <option value="urgent">{isRtl ? 'عاجل' : 'Urgent'}</option>
                    <option value="emergency">{isRtl ? 'طوارئ' : 'Emergency'}</option>
                  </select>
                </div>
                <Input label={isRtl ? 'سبب التحويل (عربي)' : 'Reason (Arabic)'} value={form.reasonAr} onChange={e => setForm(p => ({ ...p, reasonAr: e.target.value }))} required />
                <Input label={isRtl ? 'سبب التحويل (إنجليزي)' : 'Reason (English)'} value={form.reason} onChange={e => setForm(p => ({ ...p, reason: e.target.value }))} />
                <div className="flex gap-3">
                  <Button type="submit" variant="primary">{isRtl ? 'إرسال التحويل' : 'Submit Referral'}</Button>
                  <Button type="button" variant="ghost" onClick={() => setShowForm(false)}>{isRtl ? 'إلغاء' : 'Cancel'}</Button>
                </div>
              </form>
            </CardBody>
          </Card>
        )}

        <div className="space-y-3">
          {referrals.map(ref => {
            const priorityColors: Record<string, 'danger' | 'warning' | 'info'> = { emergency: 'danger', urgent: 'warning', routine: 'info' };
            const statusColors: Record<string, 'success' | 'default' | 'warning' | 'danger'> = { accepted: 'success', completed: 'success', pending: 'warning', rejected: 'danger' };
            return (
              <Card key={ref.id} padding="md">
                <CardBody>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-sm">{isRtl ? ref.patientNameAr : ref.patientName}</span>
                        <Badge variant={priorityColors[ref.priority]} size="xs">{isRtl ? (ref.priority === 'emergency' ? 'طوارئ' : ref.priority === 'urgent' ? 'عاجل' : 'روتيني') : ref.priority}</Badge>
                      </div>
                      <p className="text-xs text-neutral-500">{isRtl ? `من: ${ref.fromSpecialtyAr}` : `From: ${ref.fromSpecialty}`}</p>
                      <p className="text-xs text-neutral-500">{isRtl ? `إلى: ${ref.toSpecialtyAr} - ${ref.toDoctor}` : `To: ${ref.toSpecialty} - ${ref.toDoctor}`}</p>
                      <p className="text-xs text-neutral-400 mt-1">{isRtl ? ref.reasonAr : ref.reason}</p>
                    </div>
                    <Badge variant={statusColors[ref.status]}>{isRtl ? (ref.status === 'pending' ? 'قيد الانتظار' : ref.status === 'accepted' ? 'مقبول' : ref.status === 'completed' ? 'مكتمل' : 'مرفوض') : ref.status}</Badge>
                  </div>
                </CardBody>
              </Card>
            );
          })}
        </div>
      </div>
    </LayoutContent>
  );
}
