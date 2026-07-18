import { useState } from 'react';
import { cn } from '@gula/ui-platform';
import { BarcodeScanner } from '@/components/BarcodeScanner';
import { PrintLabel } from '@/components/PrintLabel';
import { barcodeService } from '@/services/barcode';
import { Card, CardBody, CardHeader } from '@gula/ui-platform';
import type { BarcodeLabel } from '@/utils/types';

export function BarcodePrinting() {
  const [step, setStep] = useState<'input' | 'preview'>('input');
  const [label, setLabel] = useState<BarcodeLabel | null>(null);
  const [form, setForm] = useState({
    sampleId: '', patientName: '', patientId: '',
    specimenType: 'whole_blood', tests: [''], container: '',
  });
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const specimenTypes = [
    { value: 'whole_blood', label: 'دم كامل' }, { value: 'serum', label: 'مصل' },
    { value: 'plasma', label: 'بلازما' }, { value: 'urine', label: 'بول' },
    { value: 'swab', label: 'مسحة' }, { value: 'csf', label: 'سائل نخاعي' },
    { value: 'tissue', label: 'نسيج' }, { value: 'other', label: 'أخرى' },
  ];

  const generateBarcode = () => {
    const id = form.sampleId || `SMP-${Date.now().toString(36).toUpperCase()}`;
    const barcode = id;
    setLabel({
      sampleId: id, patientName: form.patientName, patientId: form.patientId,
      specimenType: form.specimenType, tests: form.tests.filter(t => t.trim()),
      container: form.container, barcode,
    });
    setStep('preview');
  };

  const handlePrint = async (labelToPrint: BarcodeLabel, copies: number) => {
    try {
      const result = await barcodeService.printLabels([labelToPrint], { copies });
      if (result.success) {
        setMessage({ type: 'success', text: `تم إرسال ${copies} نسخة للطباعة` });
      } else {
        setMessage({ type: 'error', text: result.error || 'فشلت الطباعة' });
      }
    } catch (e) {
      setMessage({ type: 'error', text: (e as Error).message });
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">طباعة الباركود</h1>
      <p className="text-sm text-neutral-500 -mt-5">إنشاء وطباعة ملصقات الباركود للعينات</p>

      {message && (
        <div className={cn('px-4 py-3 rounded-2xl text-sm font-medium border', message.type === 'success' ? 'bg-success-50 text-success-700 border-success-200' : 'bg-danger-50 text-danger-700 border-danger-200')}>
          {message.text}
        </div>
      )}

      {step === 'input' ? (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <BarcodeScanner onScan={(barcode, parsed) => {
                if (parsed?.type === 'sample') setForm(f => ({ ...f, sampleId: parsed.sampleId || barcode }));
                else if (parsed?.type === 'patient') setForm(f => ({ ...f, patientId: parsed.patientId || barcode }));
              }} placeholder="امسح العينة أو المريض" />
            </div>
          </CardHeader>
          <CardBody className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2"><label className="text-xs font-bold text-neutral-600">رقم العينة</label><input type="text" value={form.sampleId} onChange={e => setForm(f => ({ ...f, sampleId: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm font-mono" /></div>
              <div className="space-y-2"><label className="text-xs font-bold text-neutral-600">معرف المريض</label><input type="text" value={form.patientId} onChange={e => setForm(f => ({ ...f, patientId: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" /></div>
            </div>
            <div className="space-y-2"><label className="text-xs font-bold text-neutral-600">اسم المريض</label><input type="text" value={form.patientName} onChange={e => setForm(f => ({ ...f, patientName: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" /></div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2"><label className="text-xs font-bold text-neutral-600">نوع العينة</label><select value={form.specimenType} onChange={e => setForm(f => ({ ...f, specimenType: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm">
                {specimenTypes.map(st => <option key={st.value} value={st.value}>{st.label}</option>)}
              </select></div>
              <div className="space-y-2"><label className="text-xs font-bold text-neutral-600">الحاوية</label><input type="text" value={form.container} onChange={e => setForm(f => ({ ...f, container: e.target.value }))} placeholder="نوع الأنبوب" className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" /></div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-neutral-600">الفحوصات</label>
                <button type="button" onClick={() => setForm(f => ({ ...f, tests: [...f.tests, ''] }))} className="text-xs text-primary-500 font-bold">+ إضافة</button>
              </div>
              {form.tests.map((t, i) => (
                <div key={i} className="flex gap-2">
                  <input type="text" value={t} onChange={e => { const tests = [...form.tests]; tests[i] = e.target.value; setForm(f => ({ ...f, tests })); }} className="flex-1 px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" />
                  {form.tests.length > 1 && <button type="button" onClick={() => setForm(f => ({ ...f, tests: f.tests.filter((_, idx) => idx !== i) }))} className="p-3 text-danger-500 hover:bg-danger-50 rounded-xl">✕</button>}
                </div>
              ))}
            </div>
            <button type="button" onClick={generateBarcode} disabled={!form.patientName} className="w-full py-3.5 bg-primary-500 text-white rounded-xl font-bold text-sm hover:bg-primary-600 disabled:opacity-50">
              معاينة الباركود
            </button>
          </CardBody>
        </Card>
      ) : label ? (
        <div className="space-y-4">
          <PrintLabel label={label} onPrint={handlePrint} onClose={() => setStep('input')} />
        </div>
      ) : null}
    </div>
  );
}
