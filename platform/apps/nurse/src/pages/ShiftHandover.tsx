import { useEffect, useState } from 'react';
import { Card, Button, Modal, Input, Select, LoadingSpinner, EmptyState, Badge } from '@gula/ui-platform';
import { useNurse } from '../contexts/NurseContext';
import { getShiftArabic } from '../utils/routes';
import { handoversService, type HandoverRecord, type HandoverShift } from '../services/handovers';

interface HandoverForm {
  shift: HandoverShift;
  toNurseId: string;
  date: string;
  notes: string;
}

export default function ShiftHandover() {
  const { user } = useNurse();
  const [handovers, setHandovers] = useState<HandoverRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<HandoverForm>({
    shift: 'morning',
    toNurseId: '',
    date: new Date().toISOString().slice(0, 10),
    notes: '',
  });

  async function loadHandovers(active = true) {
    setLoading(true);
    setError(null);
    try {
      const records = await handoversService.list();
      if (active) setHandovers(records);
    } catch (cause) {
      if (active) setError(cause instanceof Error ? cause.message : 'تعذر تحميل سجل التسليم من الخادم');
    } finally {
      if (active) setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    void loadHandovers(active);
    return () => {
      active = false;
    };
  }, []);

  async function createHandover() {
    if (!user?.id || !form.toNurseId.trim()) {
      setError('أدخل هوية الممرض المستلم قبل الحفظ.');
      return;
    }
    setCreating(true);
    setError(null);
    try {
      const created = await handoversService.create({
        from_nurse_id: String(user.id),
        to_nurse_id: form.toNurseId.trim(),
        handover_type: form.shift,
        shift_date: form.date,
        notes: form.notes.trim() || undefined,
      });
      setHandovers((current) => [created, ...current]);
      setShowModal(false);
      setForm((current) => ({ ...current, toNurseId: '', notes: '' }));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'تعذر إنشاء تسليم الوردية');
    } finally {
      setCreating(false);
    }
  }

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">تسليم الوردية</h1>
          <p className="text-gray-500">سجل حي من نظام التمريض الوطني</p>
        </div>
        <Button variant="primary" onClick={() => setShowModal(true)}>تسليم جديد</Button>
      </div>

      {error && (
        <div className="flex items-center justify-between gap-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700" role="alert">
          <span>{error}</span>
          <Button variant="outline" onClick={() => void loadHandovers(true)}>إعادة المحاولة</Button>
        </div>
      )}

      {handovers.length === 0 && !error ? (
        <EmptyState title="لا يوجد تسليم" description="لم يتم تسجيل أي تسليم وردية بعد" />
      ) : (
        <div className="space-y-4">
          {handovers.map((handover) => (
            <Card key={handover.id}>
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h3 className="text-lg font-semibold">{getShiftArabic(handover.shift)} - {handover.date}</h3>
                  <p className="text-sm text-gray-500">من: {handover.fromNurse} → إلى: {handover.toNurse}</p>
                  <p className="text-sm">المرضى: {handover.patientCount} | حالات حرجة: {handover.criticalCount}</p>
                  {handover.notes && <p className="mt-2 text-sm">{handover.notes}</p>}
                </div>
                <Badge variant={handover.completed ? 'success' : 'warning'}>{handover.completed ? 'مكتمل' : 'قيد الانتظار'}</Badge>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal open={showModal} onClose={() => setShowModal(false)} title="تسليم وردية جديد" size="lg">
        <div className="space-y-4">
          <Select
            label="الوردية"
            value={form.shift}
            onChange={(event) => setForm((current) => ({ ...current, shift: event.target.value as HandoverShift }))}
            options={[{ value: 'morning', label: 'صباحية' }, { value: 'evening', label: 'مسائية' }, { value: 'night', label: 'ليلية' }]}
          />
          <Input label="تاريخ الوردية" type="date" value={form.date} onChange={(event) => setForm((current) => ({ ...current, date: event.target.value }))} />
          <Input label="معرّف الممرض المستلم" placeholder="أدخل المعرّف المعتمد" value={form.toNurseId} onChange={(event) => setForm((current) => ({ ...current, toNurseId: event.target.value }))} />
          <Input label="ملاحظات" placeholder="ملاحظات التسليم" value={form.notes} onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))} />
          <div className="flex justify-left gap-2 pt-4">
            <Button variant="primary" onClick={() => void createHandover()} disabled={creating}>{creating ? 'جارٍ الحفظ…' : 'تأكيد التسليم'}</Button>
            <Button variant="ghost" onClick={() => setShowModal(false)}>إلغاء</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
