import { useState, useEffect } from 'react';
import { cn } from '@gula/ui-platform';
import { useNurse } from '@/contexts/NurseContext';
import { patientsService } from '@/services/patients';
import type { Patient } from '@/utils/types';

interface ChecklistItem {
  id: string;
  label: string;
  checked: boolean;
}

function DischargeChecklist({ items, onToggle }: { items: ChecklistItem[]; onToggle: (id: string) => void }) {
  const allChecked = items.every(i => i.checked);
  const completed = items.filter(i => i.checked).length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-xs font-bold text-neutral-500 dark:text-neutral-400">قائمة التدقيق</p>
        <span className="text-xs font-bold text-neutral-400">{completed}/{items.length}</span>
      </div>
      <div className="h-1.5 bg-neutral-100 dark:bg-neutral-700 rounded-full overflow-hidden">
        <div className={cn('h-full rounded-full transition-all', allChecked ? 'bg-success-500' : 'bg-primary-500')} style={{ width: `${(completed / items.length) * 100}%` }} />
      </div>
      <div className="space-y-2">
        {items.map(item => (
          <button
            key={item.id}
            type="button"
            onClick={() => onToggle(item.id)}
            className={cn(
              'w-full text-right p-3 rounded-xl border-2 transition-all flex items-center gap-3',
              item.checked
                ? 'border-success-200 dark:border-success-800 bg-success-50 dark:bg-success-900/20'
                : 'border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 hover:border-primary-300',
            )}
          >
            <div className={cn(
              'w-6 h-6 rounded-lg border-2 flex items-center justify-center shrink-0 transition-all',
              item.checked ? 'bg-success-500 border-success-500' : 'border-neutral-300 dark:border-neutral-600',
            )}>
              {item.checked && (
                <svg className="w-3.5 h-3.5 text-white" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" />
                </svg>
              )}
            </div>
            <span className={cn('text-sm font-bold', item.checked ? 'text-success-700 dark:text-success-400 line-through' : 'text-neutral-700 dark:text-neutral-300')}>
              {item.label}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

export function Discharge() {
  const { user } = useNurse();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [dischargeNotes, setDischargeNotes] = useState('');
  const [checklist, setChecklist] = useState<ChecklistItem[]>([
    { id: 'meds', label: 'مراجعة الأدوية مع المريض', checked: false },
    { id: 'summary', label: 'كتابة ملخص الخروج', checked: false },
    { id: 'followup', label: 'تحديد موعد المتابعة', checked: false },
    { id: 'education', label: 'تثقيف المريض', checked: false },
    { id: 'belongings', label: 'تسليم الأغراض الشخصية', checked: false },
    { id: 'records', label: 'تسليم السجلات الطبية', checked: false },
    { id: 'transport', label: 'ترتيب النقل', checked: false },
    { id: 'bed', label: 'تحرير السرير', checked: false },
  ]);

  useEffect(() => {
    loadPatients();
  }, [user?.ward]);

  const loadPatients = async () => {
    try {
      const list = await patientsService.getList(user?.ward);
      setPatients(list);
    } catch {
      setError('فشل تحميل قائمة المرضى');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = (id: string) => {
    setChecklist(prev => prev.map(i => i.id === id ? { ...i, checked: !i.checked } : i));
  };

  const handleDischarge = async () => {
    if (!selectedPatient) return;
    setSaving(true);
    setError('');
    try {
      await patientsService.dischargePatient(selectedPatient.id, {
        dischargeDate: new Date().toISOString(),
        notes: dischargeNotes,
      });
      setSuccess(`تم خروج المريض ${selectedPatient.name} بنجاح`);
      setSelectedPatient(null);
      setDischargeNotes('');
      setChecklist(prev => prev.map(i => ({ ...i, checked: false })));
      loadPatients();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل عملية الخروج');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-black text-neutral-900 dark:text-neutral-100">خروج المرضى</h1>

      {success && (
        <div className="bg-success-50 dark:bg-success-900/20 border border-success-200 dark:border-success-800 p-3 rounded-2xl">
          <p className="text-xs text-success-600 dark:text-success-400 font-bold">{success}</p>
        </div>
      )}

      {error && (
        <div className="bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 p-3 rounded-2xl">
          <p className="text-xs text-danger-600 dark:text-danger-400 font-bold">{error}</p>
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="space-y-3">
          <h2 className="font-bold text-sm text-neutral-700 dark:text-neutral-300">اختر مريضاً للخروج</h2>
          {patients.length === 0 ? (
            <div className="text-center py-12 bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700">
              <p className="text-4xl mb-3">🏥</p>
              <p className="text-sm font-bold text-neutral-500 dark:text-neutral-400">لا يوجد مرضى في هذا الجناح</p>
            </div>
          ) : (
            patients.map(p => (
              <button
                key={p.id}
                onClick={() => { setSelectedPatient(p); setError(''); setSuccess(''); }}
                className={cn(
                  'w-full text-right p-4 rounded-2xl border-2 transition-all',
                  selectedPatient?.id === p.id
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 hover:shadow-md',
                )}
              >
                <div className="flex items-center gap-3">
                  <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-sm', p.gender === 'أنثى' ? 'bg-pink-500' : 'bg-blue-500')}>
                    {p.name.charAt(0)}
                  </div>
                  <div>
                    <p className="font-bold text-neutral-900 dark:text-neutral-100">{p.name}</p>
                    <p className="text-xs text-neutral-500 dark:text-neutral-400">{p.bed} • {p.diagnosis}</p>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>

        {selectedPatient && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 p-4">
              <h3 className="font-bold text-neutral-900 dark:text-neutral-100 mb-1">{selectedPatient.name}</h3>
              <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-4">خروج المريض - يرجى إكمال قائمة التدقيق</p>
              <DischargeChecklist items={checklist} onToggle={handleToggle} />
            </div>

            <div className="bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 p-4">
              <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-2">ملاحظات الخروج</label>
              <textarea
                value={dischargeNotes}
                onChange={e => setDischargeNotes(e.target.value)}
                placeholder="أي ملاحظات إضافية..."
                rows={3}
                className="w-full px-3 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none resize-none"
              />
            </div>

            <button
              onClick={handleDischarge}
              disabled={saving || !checklist.every(i => i.checked)}
              className={cn(
                'w-full py-3 rounded-2xl font-bold text-sm transition-all',
                'bg-danger-500 text-white hover:bg-danger-600',
                'disabled:opacity-50 disabled:cursor-not-allowed',
              )}
            >
              {saving ? (
                <span className="inline-flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  جاري تنفيذ الخروج...
                </span>
              ) : (
                `تأكيد خروج ${selectedPatient.name}`
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
