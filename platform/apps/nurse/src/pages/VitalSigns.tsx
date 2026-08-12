import { useState, useEffect } from 'react';
import { cn } from '@gula/ui-platform';
import { useNurse } from '@/contexts/NurseContext';
import { vitalsService } from '@/services/vitals';
import { patientsService } from '@/services/patients';
import { VitalSignsChart } from '@/components/VitalSignsChart';
import type { VitalSigns, Patient } from '@/utils/types';

interface VitalForm {
  patientId: string;
  temperature: string;
  heartRate: string;
  respiratoryRate: string;
  bloodPressureSystolic: string;
  bloodPressureDiastolic: string;
  oxygenSaturation: string;
  bloodGlucose: string;
  painScore: string;
  consciousness: string;
  notes: string;
}

const emptyForm: VitalForm = {
  patientId: '',
  temperature: '',
  heartRate: '',
  respiratoryRate: '',
  bloodPressureSystolic: '',
  bloodPressureDiastolic: '',
  oxygenSaturation: '',
  bloodGlucose: '',
  painScore: '',
  consciousness: 'alert',
  notes: '',
};

const consciousnessOptions = [
  { value: 'alert', label: 'يقظ' },
  { value: 'confused', label: 'مشوش' },
  { value: 'voice', label: 'يستجيب للصوت' },
  { value: 'pain', label: 'يستجيب للألم' },
  { value: 'unresponsive', label: 'غير مستجيب' },
];

function VitalSigns() {
  const { user } = useNurse();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [vitalHistory, setVitalHistory] = useState<VitalSigns[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState('');
  const [form, setForm] = useState<VitalForm>(emptyForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [ewsResult, setEwsResult] = useState<{ grade: string; color: string; action: string } | null>(null);

  useEffect(() => {
    loadPatients();
  }, [user?.ward]);

  useEffect(() => {
    if (selectedPatientId) {
      loadVitalHistory(selectedPatientId);
      setForm(prev => ({ ...prev, patientId: selectedPatientId }));
    }
  }, [selectedPatientId]);

  const loadPatients = async () => {
    try {
      const list = await patientsService.getList(user?.ward);
      setPatients(list);
      if (list.length > 0) {
        setSelectedPatientId(list[0].id);
      }
    } catch (err) {
      setError('فشل تحميل قائمة المرضى');
    } finally {
      setLoading(false);
    }
  };

  const loadVitalHistory = async (patientId: string) => {
    try {
      const history = await vitalsService.getChart(patientId, 24);
      setVitalHistory(history);
    } catch {
      setVitalHistory([]);
    }
  };

  const updateForm = (field: keyof VitalForm, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }));
    const numericFields: (keyof VitalForm)[] = [
      'temperature', 'heartRate', 'respiratoryRate',
      'bloodPressureSystolic', 'bloodPressureDiastolic',
      'oxygenSaturation', 'bloodGlucose', 'painScore',
    ];
    if (numericFields.includes(field)) {
      const partial: Partial<VitalSigns> = {};
      const t = field === 'temperature' ? parseFloat(value) : null;
      if (field === 'temperature' && !isNaN(t ?? NaN)) partial.temperature = t;
      const hr = field === 'heartRate' ? parseInt(value) : null;
      if (field === 'heartRate' && !isNaN(hr ?? NaN)) partial.heartRate = hr;
      const rr = field === 'respiratoryRate' ? parseInt(value) : null;
      if (field === 'respiratoryRate' && !isNaN(rr ?? NaN)) partial.respiratoryRate = rr;
      const sbp = field === 'bloodPressureSystolic' ? parseInt(value) : null;
      if (field === 'bloodPressureSystolic' && !isNaN(sbp ?? NaN)) partial.bloodPressureSystolic = sbp;
      const dbp = field === 'bloodPressureDiastolic' ? parseInt(value) : null;
      if (field === 'bloodPressureDiastolic' && !isNaN(dbp ?? NaN)) partial.bloodPressureDiastolic = dbp;
      const spo2 = field === 'oxygenSaturation' ? parseInt(value) : null;
      if (field === 'oxygenSaturation' && !isNaN(spo2 ?? NaN)) partial.oxygenSaturation = spo2;
      const bg = field === 'bloodGlucose' ? parseFloat(value) : null;
      if (field === 'bloodGlucose' && !isNaN(bg ?? NaN)) partial.bloodGlucose = bg;
      const ps = field === 'painScore' ? parseInt(value) : null;
      if (field === 'painScore' && !isNaN(ps ?? NaN)) partial.painScore = ps;
      if (field === 'consciousness') partial.consciousness = value;

      const fullPartial: Partial<VitalSigns> = {
        temperature: parseFloat(form.temperature) || null,
        heartRate: parseInt(form.heartRate) || null,
        respiratoryRate: parseInt(form.respiratoryRate) || null,
        bloodPressureSystolic: parseInt(form.bloodPressureSystolic) || null,
        bloodPressureDiastolic: parseInt(form.bloodPressureDiastolic) || null,
        oxygenSaturation: parseInt(form.oxygenSaturation) || null,
        bloodGlucose: parseFloat(form.bloodGlucose) || null,
        painScore: parseInt(form.painScore) || null,
        consciousness: form.consciousness,
        ...partial,
      };
      const score = vitalsService.calculateEWS(fullPartial);
      const result = vitalsService.getEWSGrade(score);
      setEwsResult(result);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.patientId) {
      setError('يرجى اختيار مريض');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const data = {
        patientId: form.patientId,
        patientName: patients.find(p => p.id === form.patientId)?.name || '',
        bed: patients.find(p => p.id === form.patientId)?.bed || '',
        temperature: form.temperature ? parseFloat(form.temperature) : null,
        heartRate: form.heartRate ? parseInt(form.heartRate) : null,
        respiratoryRate: form.respiratoryRate ? parseInt(form.respiratoryRate) : null,
        bloodPressureSystolic: form.bloodPressureSystolic ? parseInt(form.bloodPressureSystolic) : null,
        bloodPressureDiastolic: form.bloodPressureDiastolic ? parseInt(form.bloodPressureDiastolic) : null,
        oxygenSaturation: form.oxygenSaturation ? parseInt(form.oxygenSaturation) : null,
        bloodGlucose: form.bloodGlucose ? parseFloat(form.bloodGlucose) : null,
        painScore: form.painScore ? parseInt(form.painScore) : null,
        consciousness: form.consciousness,
        notes: form.notes,
      };
      await vitalsService.record(data);
      setSuccess('تم تسجيل العلامات الحيوية بنجاح');
      setForm(emptyForm);
      setEwsResult(null);
      if (selectedPatientId) loadVitalHistory(selectedPatientId);
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل تسجيل العلامات الحيوية');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-black text-neutral-900 dark:text-neutral-100">العلامات الحيوية</h1>

      <div className="flex gap-2 flex-wrap">
        {patients.map(p => (
          <button
            key={p.id}
            onClick={() => setSelectedPatientId(p.id)}
            className={cn(
              'px-3 py-1.5 text-xs font-bold rounded-xl transition-colors',
              selectedPatientId === p.id
                ? 'bg-primary-500 text-white'
                : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-600',
            )}
          >
            {p.name} - {p.bed}
          </button>
        ))}
      </div>

      {error && (
        <div className="bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 p-3 rounded-2xl">
          <p className="text-xs text-danger-600 dark:text-danger-400 font-bold">{error}</p>
        </div>
      )}

      {success && (
        <div className="bg-success-50 dark:bg-success-900/20 border border-success-200 dark:border-success-800 p-3 rounded-2xl">
          <p className="text-xs text-success-600 dark:text-success-400 font-bold">{success}</p>
        </div>
      )}

      {selectedPatientId && vitalHistory.length > 0 && (
        <div className="bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 p-4">
          <h2 className="font-bold text-sm text-neutral-700 dark:text-neutral-300 mb-4">آخر 24 ساعة</h2>
          <VitalSignsChart data={vitalHistory} />
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 p-6 space-y-5">
        <h2 className="font-bold text-neutral-900 dark:text-neutral-100">تسجيل قراءات جديدة</h2>

        {ewsResult && (
          <div className={cn('p-3 rounded-2xl border', ewsResult.color.includes('danger') ? 'bg-danger-50 dark:bg-danger-900/20 border-danger-200 dark:border-danger-800' : ewsResult.color.includes('warning') ? 'bg-warning-50 dark:bg-warning-900/20 border-warning-200 dark:border-warning-800' : 'bg-success-50 dark:bg-success-900/20 border-success-200 dark:border-success-800')}>
            <p className={cn('text-xs font-bold', ewsResult.color)}>EWS: {ewsResult.grade}</p>
            <p className="text-[10px] text-neutral-500 dark:text-neutral-400 mt-0.5">{ewsResult.action}</p>
          </div>
        )}

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-1.5">درجة الحرارة (°C)</label>
            <input type="number" step="0.1" value={form.temperature} onChange={e => updateForm('temperature', e.target.value)} placeholder="36.6" className="w-full px-3 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none" />
          </div>
          <div>
            <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-1.5">معدل القلب (/د)</label>
            <input type="number" value={form.heartRate} onChange={e => updateForm('heartRate', e.target.value)} placeholder="72" className="w-full px-3 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none" />
          </div>
          <div>
            <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-1.5">التنفس (/د)</label>
            <input type="number" value={form.respiratoryRate} onChange={e => updateForm('respiratoryRate', e.target.value)} placeholder="16" className="w-full px-3 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none" />
          </div>
          <div>
            <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-1.5">ضغط الدم الانقباضي</label>
            <input type="number" value={form.bloodPressureSystolic} onChange={e => updateForm('bloodPressureSystolic', e.target.value)} placeholder="120" className="w-full px-3 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none" />
          </div>
          <div>
            <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-1.5">ضغط الدم الانبساطي</label>
            <input type="number" value={form.bloodPressureDiastolic} onChange={e => updateForm('bloodPressureDiastolic', e.target.value)} placeholder="80" className="w-full px-3 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none" />
          </div>
          <div>
            <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-1.5">تشبع الأكسجين (%)</label>
            <input type="number" value={form.oxygenSaturation} onChange={e => updateForm('oxygenSaturation', e.target.value)} placeholder="98" className="w-full px-3 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none" />
          </div>
          <div>
            <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-1.5">سكر الدم (مجم/دل)</label>
            <input type="number" step="0.1" value={form.bloodGlucose} onChange={e => updateForm('bloodGlucose', e.target.value)} placeholder="100" className="w-full px-3 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none" />
          </div>
          <div>
            <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-1.5">مقياس الألم (0-10)</label>
            <input type="number" min="0" max="10" value={form.painScore} onChange={e => updateForm('painScore', e.target.value)} placeholder="0" className="w-full px-3 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none" />
          </div>
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-1.5">مستوى الوعي</label>
            <select value={form.consciousness} onChange={e => updateForm('consciousness', e.target.value)} className="w-full px-3 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 focus:border-primary-500 focus:outline-none">
              {consciousnessOptions.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-1.5">ملاحظات</label>
            <input type="text" value={form.notes} onChange={e => updateForm('notes', e.target.value)} placeholder="أي ملاحظات إضافية" className="w-full px-3 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none" />
          </div>
        </div>

        <button
          type="submit"
          disabled={saving || !selectedPatientId}
          className={cn(
            'w-full py-3 bg-primary-500 text-white rounded-2xl font-bold text-sm transition-all',
            'hover:bg-primary-600 active:bg-primary-700',
            'disabled:opacity-50 disabled:cursor-not-allowed',
          )}
        >
          {saving ? (
            <span className="inline-flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              جاري الحفظ...
            </span>
          ) : 'حفظ القراءات'}
        </button>
      </form>
    </div>
  );
}

export default VitalSigns;
