import { useState, useEffect } from 'react';
import { cn } from '@gula/ui-platform';
import { resultsService } from '@/services/results';
import { ValidationWorkflow } from '@/components/ValidationWorkflow';
import { CriticalValueFlag } from '@/components/CriticalValueFlag';
import { useLab } from '@/contexts/LabContext';
import type { TestResult } from '@/utils/types';

export function ResultValidation() {
  const { user } = useLab();
  const [results, setResults] = useState<TestResult[]>([]);
  const [criticalAlerts, setCriticalAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedResult, setSelectedResult] = useState<TestResult | null>(null);

  useEffect(() => {
    loadResults();
    loadCriticalAlerts();
  }, []);

  async function loadResults() {
    setLoading(true);
    try {
      const data = await resultsService.list({ perPage: 100 });
      setResults(data.data);
    } catch { /* ignore */ }
    setLoading(false);
  }

  async function loadCriticalAlerts() {
    try {
      const alerts = await resultsService.getCriticalAlerts({ acknowledged: false });
      setCriticalAlerts(alerts);
    } catch { /* ignore */ }
  }

  const handleValidate = async (ids: string[], action: 'approve' | 'reject', notes?: string) => {
    await resultsService.batchValidate(ids, {
      verifiedBy: user?.name || 'unknown',
      action,
    });
    loadResults();
  };

  const handleAcknowledgeCritical = async (id: string) => {
    await resultsService.acknowledgeCriticalAlert(id);
    loadCriticalAlerts();
  };

  const handleReviewSingle = (result: TestResult) => {
    setSelectedResult(result);
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">التحقق من النتائج</h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">مراجعة واعتماد نتائج الفحوصات</p>
        </div>
      </div>

      {criticalAlerts.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-danger-600 dark:text-danger-400">
            تنبيهات القيم الحرجة ({criticalAlerts.length})
          </h3>
          {criticalAlerts.map(alert => (
            <CriticalValueFlag
              key={alert.id}
              testName={alert.testName}
              value={alert.value}
              flag="critical_high"
              patientName={alert.patientName}
              sampleId={alert.resultId}
              onAcknowledge={() => handleAcknowledgeCritical(alert.id)}
            />
          ))}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-neutral-400">جاري التحميل...</div>
      ) : (
        <ValidationWorkflow
          results={results}
          onValidate={handleValidate}
          onReviewSingle={handleReviewSingle}
        />
      )}

      {selectedResult && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm">
          <div className="bg-white dark:bg-neutral-800 rounded-3xl p-8 w-full max-w-2xl shadow-2xl border border-neutral-200 dark:border-neutral-700 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">تفاصيل النتيجة</h3>
              <button type="button" onClick={() => setSelectedResult(null)} className="p-2 text-neutral-400 hover:text-neutral-600 rounded-xl hover:bg-neutral-100">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div><span className="text-xs text-neutral-500">الفحص</span><p className="font-bold">{selectedResult.testName}</p></div>
                <div><span className="text-xs text-neutral-500">الفئة</span><p className="font-bold">{selectedResult.category}</p></div>
                <div><span className="text-xs text-neutral-500">القيمة</span><p className="font-bold text-lg">{selectedResult.value} {selectedResult.unit}</p></div>
                <div><span className="text-xs text-neutral-500">النطاق المرجعي</span><p className="font-bold">{selectedResult.referenceRange}</p></div>
                <div><span className="text-xs text-neutral-500">الجهاز</span><p className="font-bold">{selectedResult.instrument || '---'}</p></div>
                <div><span className="text-xs text-neutral-500">الطريقة</span><p className="font-bold">{selectedResult.method || '---'}</p></div>
              </div>
              {selectedResult.notes && (
                <div className="p-4 bg-neutral-50 dark:bg-neutral-700/50 rounded-xl text-sm">{selectedResult.notes}</div>
              )}
            </div>

            <div className="flex gap-3">
              <button type="button" onClick={() => { handleValidate([selectedResult.id], 'approve'); setSelectedResult(null); }} className="flex-1 py-3 bg-success-500 text-white rounded-xl font-bold text-sm hover:bg-success-600">اعتماد</button>
              <button type="button" onClick={() => { handleValidate([selectedResult.id], 'reject'); setSelectedResult(null); }} className="flex-1 py-3 bg-danger-500 text-white rounded-xl font-bold text-sm hover:bg-danger-600">رفض</button>
              <button type="button" onClick={() => setSelectedResult(null)} className="px-6 py-3 bg-neutral-100 dark:bg-neutral-700 text-neutral-600 rounded-xl font-bold text-sm">إغلاق</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
