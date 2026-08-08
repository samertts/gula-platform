import { useState, useEffect } from 'react';
import { cn } from '@gula/ui-platform';
import { useNurse } from '@/contexts/NurseContext';
import { patientsService } from '@/services/patients';
import type { Admission } from '@/utils/types';

interface AdmissionForm {
  patientName: string;
  mrn: string;
  ward: string;
  bed: string;
  diagnosis: string;
  referringPhysician: string;
  admissionType: 'emergency' | 'elective' | 'transfer';
  notes: string;
}

const emptyForm: AdmissionForm = {
  patientName: '',
  mrn: '',
  ward: '',
  bed: '',
  diagnosis: '',
  referringPhysician: '',
  admissionType: 'emergency',
  notes: '',
};

const wards = [
  { value: 'emergency', label: 'الطوارئ' },
  { value: 'icu', label: 'العناية المركزة' },
  { value: 'nicu', label: 'عناية الأطفال حديثي الولادة' },
  { value: 'cardiology', label: 'القلب' },
  { value: 'pediatrics', label: 'الأطفال' },
  { value: 'maternity', label: 'الولادة' },
  { value: 'surgery', label: 'الجراحة' },
  { value: 'orthopedics', label: 'العظام' },
  { value: 'neurology', label: 'الأعصاب' },
  { value: 'general', label: 'الداخلي العام' },
];

export function Admissions() {
  const { user } = useNurse();
  const [admissions, setAdmissions] = useState<Admission[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<AdmissionForm>(emptyForm);
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadAdmissions();
  }, [user?.ward]);

  const loadAdmissions = async () => {
    setLoading(true);
    try {
      const list = await patientsService.getAdmissions(user?.ward);
      setAdmissions(list);
    } catch {
      setError('فشل تحميل قائمة القبول');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.patientName || !form.ward || !form.bed) {
      setError('يرجى ملء الحقول المطلوبة');
      return;
    }
    setSaving(true);
    setError('');
    try {
      await patientsService.admitPatient({
        patientName: form.patientName,
        mrn: form.mrn,
        ward: form.ward,
        bed: form.bed,
        diagnosis: form.diagnosis,
        referringPhysician: form.referringPhysician,
        admissionType: form.admissionType,
        notes: form.notes,
        admissionDate: new Date().toISOString(),
      });
      setSuccess(`تم قبول المريض ${form.patientName} بنجاح`);
      setForm(emptyForm);
      setShowForm(false);
      loadAdmissions();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل قبول المريض');
    } finally {
      setSaving(false);
    }
  };

  const filteredAdmissions = admissions.filter(a =>
    !search || a.patientName.includes(search) || a.mrn.includes(search)
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-black text-neutral-900 dark:text-neutral-100">قبول المرضى</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className={cn(
            'px-4 py-2 rounded-xl font-bold text-xs transition-colors',
            showForm
              ? 'bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-400'
              : 'bg-primary-500 text-white hover:bg-primary-600',
          )}
        >
          {showForm ? 'إلغاء' : 'قبول مريض جديد'}
        </button>
      </div>

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

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 p-6 space-y-4">
          <h2 className="font-bold text-neutral-900 dark:text-neutral-100">نموذج قبول مريض</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-1.5">اسم المريض *</label>
              <input type="text" value={form.patientName} onChange={e => setForm(f => ({ ...f, patientName: e.target.value }))} placeholder="الاسم الكامل" className="w-full px-3 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-1.5">رقم الملف الطبي (MRN)</label>
              <input type="text" value={form.mrn} onChange={e => setForm(f => ({ ...f, mrn: e.target.value }))} placeholder="123456" className="w-full px-3 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-1.5">الجناح *</label>
              <select value={form.ward} onChange={e => setForm(f => ({ ...f, ward: e.target.value }))} className="w-full px-3 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 focus:border-primary-500 focus:outline-none">
                <option value="">اختر الجناح</option>
                {wards.map(w => <option key={w.value} value={w.value}>{w.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-1.5">رقم السرير *</label>
              <input type="text" value={form.bed} onChange={e => setForm(f => ({ ...f, bed: e.target.value }))} placeholder="A101" className="w-full px-3 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-1.5">التشخيص</label>
              <input type="text" value={form.diagnosis} onChange={e => setForm(f => ({ ...f, diagnosis: e.target.value }))} placeholder="التشخيص المبدئي" className="w-full px-3 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-1.5">الطبيب المحول</label>
              <input type="text" value={form.referringPhysician} onChange={e => setForm(f => ({ ...f, referringPhysician: e.target.value }))} placeholder="د. اسم الطبيب" className="w-full px-3 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-1.5">نوع القبول</label>
              <select value={form.admissionType} onChange={e => setForm(f => ({ ...f, admissionType: e.target.value as AdmissionForm['admissionType'] }))} className="w-full px-3 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 focus:border-primary-500 focus:outline-none">
                <option value="emergency">طوارئ</option>
                <option value="elective">مجدول</option>
                <option value="transfer">تحويل</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-1.5">ملاحظات</label>
              <input type="text" value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} placeholder="أي ملاحظات إضافية" className="w-full px-3 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none" />
            </div>
          </div>
          <button type="submit" disabled={saving} className={cn('w-full py-3 bg-primary-500 text-white rounded-2xl font-bold text-sm hover:bg-primary-600 transition-colors disabled:opacity-50')}>
            {saving ? 'جاري الحفظ...' : 'تأكيد القبول'}
          </button>
        </form>
      )}

      <div className="relative">
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="بحث في القبول..."
          className="w-full px-4 py-2.5 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none pr-10"
        />
        <svg className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
        </svg>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : filteredAdmissions.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700">
          <p className="text-4xl mb-3">📋</p>
          <p className="text-sm font-bold text-neutral-500 dark:text-neutral-400">{search ? 'لا توجد نتائج' : 'لا توجد حالات قبول'}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredAdmissions.map(admission => (
            <div key={admission.id} className="bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 p-4">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="font-bold text-neutral-900 dark:text-neutral-100">{admission.patientName}</p>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400">{admission.mrn}</p>
                </div>
                <span className={cn(
                  'text-[10px] px-2 py-0.5 rounded-lg font-bold',
                  admission.admissionType === 'emergency' ? 'bg-danger-100 dark:bg-danger-900/30 text-danger-600' :
                  admission.admissionType === 'elective' ? 'bg-success-100 dark:bg-success-900/30 text-success-600' :
                  'bg-primary-100 dark:bg-primary-900/30 text-primary-600',
                )}>
                  {admission.admissionType === 'emergency' ? 'طوارئ' : admission.admissionType === 'elective' ? 'مجدول' : 'تحويل'}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div><span className="text-neutral-400">الجناح:</span> <span className="font-bold text-neutral-600 dark:text-neutral-300">{admission.ward}</span></div>
                <div><span className="text-neutral-400">السرير:</span> <span className="font-bold text-neutral-600 dark:text-neutral-300">{admission.bed}</span></div>
                <div><span className="text-neutral-400">التاريخ:</span> <span className="font-bold text-neutral-600 dark:text-neutral-300">{new Date(admission.admissionDate).toLocaleDateString('ar-IQ')}</span></div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
