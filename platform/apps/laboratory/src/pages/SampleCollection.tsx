import { useState } from 'react';
import { cn } from '@gula/ui-platform';
import { BarcodeScanner } from '@/components/BarcodeScanner';
import { samplesService } from '@/services/samples';
import { barcodeService } from '@/services/barcode';
import { useWorklist } from '@/contexts/WorklistContext';
import { Card, CardBody, CardHeader } from '@gula/ui-platform';

export function SampleCollection() {
  const { addSample } = useWorklist();
  const [step, setStep] = useState<'scan' | 'register' | 'collect'>('scan');
  const [form, setForm] = useState({
    sampleId: '',
    patientId: '',
    patientName: '',
    specimenType: 'whole_blood',
    tests: [''],
    priority: 'routine' as const,
    container: '',
    volume: 5,
    notes: '',
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const specimenTypes = [
    { value: 'whole_blood', label: 'دم كامل' },
    { value: 'serum', label: 'مصل' },
    { value: 'plasma', label: 'بلازما' },
    { value: 'urine', label: 'بول' },
    { value: 'stool', label: 'براز' },
    { value: 'swab', label: 'مسحة' },
    { value: 'sputum', label: 'بلغم' },
    { value: 'tissue', label: 'نسيج' },
    { value: 'csf', label: 'سائل نخاعي' },
    { value: 'other', label: 'أخرى' },
  ];

  const handleScan = (barcode: string, parsed: any) => {
    if (parsed?.type === 'patient') {
      setForm(f => ({ ...f, patientId: parsed.patientId || '' }));
      setMessage({ type: 'success', text: `تم مسح المريض: ${parsed.patientId}` });
    } else if (parsed?.type === 'sample') {
      setForm(f => ({ ...f, sampleId: parsed.sampleId || '' }));
      setMessage({ type: 'success', text: `تم مسح العينة: ${parsed.sampleId}` });
    } else {
      setForm(f => ({ ...f, patientId: barcode }));
    }
    setStep('register');
  };

  const addTest = () => setForm(f => ({ ...f, tests: [...f.tests, ''] }));
  const removeTest = (i: number) => setForm(f => ({ ...f, tests: f.tests.filter((_, idx) => idx !== i) }));
  const updateTest = (i: number, v: string) => setForm(f => {
    const tests = [...f.tests];
    tests[i] = v;
    return { ...f, tests };
  });

  const handleRegister = async () => {
    if (!form.patientName || !form.patientId || form.tests.filter(t => t.trim()).length === 0) {
      setMessage({ type: 'error', text: 'يرجى إكمال جميع الحقول المطلوبة' });
      return;
    }
    setSaving(true);
    setMessage(null);
    try {
      const sampleId = form.sampleId || `SMP-${Date.now().toString(36).toUpperCase()}`;
      const sample = await samplesService.registerSample({
        sampleId,
        patientId: form.patientId,
        patientName: form.patientName,
        specimenType: form.specimenType,
        tests: form.tests.filter(t => t.trim()),
        priority: form.priority,
        notes: form.notes,
      });
      addSample(sample);
      setMessage({ type: 'success', text: `تم تسجيل العينة ${sample.sampleId} بنجاح` });
      setForm({ sampleId: '', patientId: '', patientName: '', specimenType: 'whole_blood', tests: [''], priority: 'routine', container: '', volume: 5, notes: '' });
      setStep('scan');
    } catch (e) {
      setMessage({ type: 'error', text: (e as Error).message || 'فشل تسجيل العينة' });
    }
    setSaving(false);
  };

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">جمع العينات</h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">تسجيل عينات جديدة للمختبر</p>
        </div>
      </div>

      {message && (
        <div className={cn(
          'px-5 py-4 rounded-2xl text-sm font-medium flex items-center gap-3',
          message.type === 'success' ? 'bg-success-50 text-success-700 dark:bg-success-900/30 dark:text-success-400 border border-success-200 dark:border-success-700' : 'bg-danger-50 text-danger-700 dark:bg-danger-900/30 dark:text-danger-400 border border-danger-200 dark:border-danger-700',
        )}>
          {message.type === 'success' ? (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12" /></svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
          )}
          {message.text}
        </div>
      )}

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <div className={cn(
              'w-8 h-8 rounded-xl flex items-center justify-center text-sm font-black',
              step === 'scan' ? 'bg-primary-500 text-white' : 'bg-success-100 text-success-600 dark:bg-success-900/30 dark:text-success-400',
            )}>1</div>
            <span className="font-bold">مسح أو إدخال بيانات المريض</span>
          </div>
        </CardHeader>
        <CardBody>
          <BarcodeScanner
            onScan={handleScan}
            placeholder="امسح باركود المريض أو أدخل المعرف يدوياً"
          />
          <div className="grid grid-cols-2 gap-4 mt-4">
            <div className="space-y-2">
              <label className="text-xs font-bold text-neutral-600 dark:text-neutral-400">معرف المريض *</label>
              <input type="text" value={form.patientId} onChange={e => setForm(f => ({ ...f, patientId: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm focus:border-primary-500 focus:outline-none dark:text-neutral-100" />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold text-neutral-600 dark:text-neutral-400">اسم المريض *</label>
              <input type="text" value={form.patientName} onChange={e => setForm(f => ({ ...f, patientName: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm focus:border-primary-500 focus:outline-none dark:text-neutral-100" />
            </div>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <div className={cn(
              'w-8 h-8 rounded-xl flex items-center justify-center text-sm font-black',
              step === 'register' ? 'bg-primary-500 text-white' : 'bg-success-100 text-success-600 dark:bg-success-900/30 dark:text-success-400',
            )}>2</div>
            <span className="font-bold">تفاصيل العينة</span>
          </div>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-bold text-neutral-600 dark:text-neutral-400">نوع العينة *</label>
              <select value={form.specimenType} onChange={e => setForm(f => ({ ...f, specimenType: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm focus:border-primary-500 focus:outline-none dark:text-neutral-100">
                {specimenTypes.map(st => <option key={st.value} value={st.value}>{st.label}</option>)}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold text-neutral-600 dark:text-neutral-400">الأولوية *</label>
              <select value={form.priority} onChange={e => setForm(f => ({ ...f, priority: e.target.value as any }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm focus:border-primary-500 focus:outline-none dark:text-neutral-100">
                <option value="routine">روتين</option>
                <option value="urgent">عاجل</option>
                <option value="stat">STAT</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-bold text-neutral-600 dark:text-neutral-400">الحاوية</label>
              <input type="text" value={form.container} onChange={e => setForm(f => ({ ...f, container: e.target.value }))} placeholder="نوع الأنبوب" className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm focus:border-primary-500 focus:outline-none dark:text-neutral-100" />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold text-neutral-600 dark:text-neutral-400">الحجم (مل)</label>
              <input type="number" value={form.volume} onChange={e => setForm(f => ({ ...f, volume: Number(e.target.value) }))} min={1} max={50} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm focus:border-primary-500 focus:outline-none dark:text-neutral-100" />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-neutral-600 dark:text-neutral-400">الفحوصات المطلوبة *</label>
              <button type="button" onClick={addTest} className="text-xs font-bold text-primary-500 hover:text-primary-600">+ إضافة فحص</button>
            </div>
            {form.tests.map((test, i) => (
              <div key={i} className="flex gap-2">
                <input type="text" value={test} onChange={e => updateTest(i, e.target.value)} placeholder={`اسم الفحص ${i + 1}`} className="flex-1 px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm focus:border-primary-500 focus:outline-none dark:text-neutral-100" />
                {form.tests.length > 1 && (
                  <button type="button" onClick={() => removeTest(i)} className="px-3 py-3 text-danger-500 hover:bg-danger-50 dark:hover:bg-danger-900/30 rounded-xl transition-colors">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
                  </button>
                )}
              </div>
            ))}
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-neutral-600 dark:text-neutral-400">ملاحظات</label>
            <textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} rows={2} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm focus:border-primary-500 focus:outline-none resize-none dark:text-neutral-100" />
          </div>

          <button
            type="button"
            onClick={handleRegister}
            disabled={saving}
            className="w-full py-3.5 bg-primary-500 text-white rounded-xl font-bold text-sm hover:bg-primary-600 transition-colors disabled:opacity-50"
          >
            {saving ? (
              <span className="inline-flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                جاري التسجيل...
              </span>
            ) : 'تسجيل العينة'}
          </button>
        </CardBody>
      </Card>
    </div>
  );
}
