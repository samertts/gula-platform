import { useState, useEffect, useCallback } from 'react';
import { cn } from '@gula/ui-platform';
import { samplesService } from '@/services/samples';
import { BarcodeScanner } from '@/components/BarcodeScanner';
import { useLab } from '@/contexts/LabContext';
import type { Sample } from '@/utils/types';

export function Receiving() {
  const { user } = useLab();
  const [pendingSamples, setPendingSamples] = useState<Sample[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSample, setSelectedSample] = useState<Sample | null>(null);
  const [action, setAction] = useState<'accept' | 'reject' | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [notes, setNotes] = useState('');
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const loadPending = useCallback(async () => {
    setLoading(true);
    try {
      const result = await samplesService.list({ status: 'collected', perPage: 50 });
      setPendingSamples(result.data);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { loadPending(); }, [loadPending]);

  const handleScan = async (barcode: string) => {
    try {
      const sample = await samplesService.getByBarcode(barcode);
      setSelectedSample(sample);
      setMessage(null);
    } catch {
      setMessage({ type: 'error', text: 'لم يتم العثور على عينة بهذا الباركود' });
    }
  };

  const handleReceive = async () => {
    if (!selectedSample || !action) return;
    setProcessing(true);
    try {
      if (action === 'accept') {
        await samplesService.acceptSample(selectedSample.id, {
          acceptedBy: user?.name || 'unknown',
          notes,
        });
      } else {
        await samplesService.rejectSample(selectedSample.id, {
          rejectedBy: user?.name || 'unknown',
          reason: rejectReason,
          notes,
        });
      }
      setMessage({ type: 'success', text: `تم ${action === 'accept' ? 'قبول' : 'رفض'} العينة ${selectedSample.sampleId}` });
      setPendingSamples(prev => prev.filter(s => s.id !== selectedSample.id));
      setSelectedSample(null);
      setAction(null);
      setRejectReason('');
      setNotes('');
    } catch (e) {
      setMessage({ type: 'error', text: (e as Error).message || 'فشل العملية' });
    }
    setProcessing(false);
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">استلام العينات</h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">قبول أو رفض العينات الواردة</p>
        </div>
      </div>

      {message && (
        <div className={cn(
          'px-5 py-4 rounded-2xl text-sm font-medium',
          message.type === 'success' ? 'bg-success-50 text-success-700 dark:bg-success-900/30 dark:text-success-400 border border-success-200' : 'bg-danger-50 text-danger-700 dark:bg-danger-900/30 dark:text-danger-400 border border-danger-200',
        )}>{message.text}</div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <BarcodeScanner onScan={handleScan} placeholder="امسح باركود العينة للاستلام" />

          <div className="space-y-2">
            <h3 className="text-sm font-bold text-neutral-700 dark:text-neutral-300">عينات بانتظار الاستلام ({pendingSamples.length})</h3>
            {loading ? (
              <div className="text-center py-8 text-neutral-400">جاري التحميل...</div>
            ) : pendingSamples.length === 0 ? (
              <div className="text-center py-8 text-neutral-400">لا توجد عينات بانتظار الاستلام</div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {pendingSamples.map(sample => (
                  <button
                    key={sample.id}
                    type="button"
                    onClick={() => setSelectedSample(sample)}
                    className={cn(
                      'w-full text-right p-4 rounded-xl border-2 transition-all bg-white dark:bg-neutral-800',
                      selectedSample?.id === sample.id ? 'border-primary-500 shadow-sm' : 'border-neutral-200 dark:border-neutral-700 hover:border-neutral-300',
                    )}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-xs font-bold text-neutral-500">{sample.sampleId}</span>
                      <span className={cn(
                        'px-1.5 py-0.5 rounded text-[9px] font-bold',
                        sample.priority === 'stat' ? 'bg-danger-50 text-danger-600' :
                        sample.priority === 'urgent' ? 'bg-warning-50 text-warning-600' :
                        'bg-neutral-100 text-neutral-600',
                      )}>
                        {sample.priority === 'stat' ? 'STAT' : sample.priority === 'urgent' ? 'عاجل' : 'روتين'}
                      </span>
                    </div>
                    <p className="text-sm font-bold text-neutral-900 dark:text-neutral-100">{sample.patientName}</p>
                    <p className="text-xs text-neutral-500">{sample.tests.join(' • ')}</p>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {selectedSample && (
          <div className="space-y-4">
            <div className="bg-white dark:bg-neutral-800 rounded-2xl border-2 border-neutral-200 dark:border-neutral-700 p-6 shadow-sm">
              <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-100 mb-4">تفاصيل العينة</h3>

              <div className="space-y-3">
                <div className="flex justify-between py-2 border-b border-neutral-100 dark:border-neutral-700">
                  <span className="text-sm text-neutral-500">رقم العينة</span>
                  <span className="text-sm font-bold font-mono">{selectedSample.sampleId}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-neutral-100 dark:border-neutral-700">
                  <span className="text-sm text-neutral-500">المريض</span>
                  <span className="text-sm font-bold">{selectedSample.patientName}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-neutral-100 dark:border-neutral-700">
                  <span className="text-sm text-neutral-500">نوع العينة</span>
                  <span className="text-sm font-bold">{selectedSample.specimenType}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-neutral-100 dark:border-neutral-700">
                  <span className="text-sm text-neutral-500">الفحوصات</span>
                  <span className="text-sm font-bold">{selectedSample.tests.join(' • ')}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-neutral-100 dark:border-neutral-700">
                  <span className="text-sm text-neutral-500">تاريخ الجمع</span>
                  <span className="text-sm">{selectedSample.collectedAt ? new Date(selectedSample.collectedAt).toLocaleString('ar-IQ') : '---'}</span>
                </div>
              </div>

              {!action && (
                <div className="flex gap-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setAction('accept')}
                    className="flex-1 py-3 bg-success-500 text-white rounded-xl font-bold text-sm hover:bg-success-600 transition-colors"
                  >
                    قبول العينة
                  </button>
                  <button
                    type="button"
                    onClick={() => setAction('reject')}
                    className="flex-1 py-3 bg-danger-500 text-white rounded-xl font-bold text-sm hover:bg-danger-600 transition-colors"
                  >
                    رفض العينة
                  </button>
                </div>
              )}

              {action === 'reject' && (
                <div className="mt-4 space-y-3">
                  <select
                    value={rejectReason}
                    onChange={e => setRejectReason(e.target.value)}
                    className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm focus:border-danger-500 focus:outline-none dark:text-neutral-100"
                  >
                    <option value="">اختر سبب الرفض</option>
                    <option value="clotted">الدم متجلط</option>
                    <option value="hemolyzed">الدم محطم</option>
                    <option value="insufficient">حجم غير كاف</option>
                    <option value="wrong_container">حاوية خاطئة</option>
                    <option value="unlabeled">غير موسوم</option>
                    <option value="damaged">تالفة</option>
                    <option value="expired">منتهية الصلاحية</option>
                    <option value="other">سبب آخر</option>
                  </select>
                  <textarea
                    value={notes}
                    onChange={e => setNotes(e.target.value)}
                    placeholder="ملاحظات إضافية..."
                    rows={2}
                    className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm focus:border-neutral-400 focus:outline-none resize-none dark:text-neutral-100"
                  />
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={handleReceive}
                      disabled={processing || !rejectReason}
                      className="flex-1 py-3 bg-danger-500 text-white rounded-xl font-bold text-sm hover:bg-danger-600 transition-colors disabled:opacity-50"
                    >
                      {processing ? 'جاري...' : 'تأكيد الرفض'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setAction(null)}
                      className="px-4 py-3 bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-300 rounded-xl font-bold text-sm"
                    >
                      إلغاء
                    </button>
                  </div>
                </div>
              )}

              {action === 'accept' && (
                <div className="mt-4 space-y-3">
                  <textarea
                    value={notes}
                    onChange={e => setNotes(e.target.value)}
                    placeholder="ملاحظات (اختياري)..."
                    rows={2}
                    className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm focus:border-neutral-400 focus:outline-none resize-none dark:text-neutral-100"
                  />
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={handleReceive}
                      disabled={processing}
                      className="flex-1 py-3 bg-success-500 text-white rounded-xl font-bold text-sm hover:bg-success-600 transition-colors disabled:opacity-50"
                    >
                      {processing ? 'جاري...' : 'تأكيد القبول'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setAction(null)}
                      className="px-4 py-3 bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-300 rounded-xl font-bold text-sm"
                    >
                      إلغاء
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
