import { useState, useEffect } from 'react';
import { cn } from '@gula/ui-platform';
import { qualityControlService } from '@/services/qualityControl';
import { QCChart } from '@/components/QCChart';
import type { QCData, QCStatus } from '@/utils/types';

export function QualityControl() {
  const [qcData, setQcData] = useState<QCData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTest, setSelectedTest] = useState<string>('all');
  const [activeTab, setActiveTab] = useState<'iqc' | 'eqa'>('iqc');
  const [showRecord, setShowRecord] = useState(false);
  const [recordForm, setRecordForm] = useState({
    testName: '', level: 'L1', value: 0, deviceId: '', performedBy: '',
  });

  useEffect(() => {
    loadQC();
  }, []);

  async function loadQC() {
    setLoading(true);
    try {
      const data = await qualityControlService.list();
      setQcData(data);
    } catch { /* ignore */ }
    setLoading(false);
  }

  const testNames = [...new Set(qcData.map(q => q.testName))];
  const filteredQC = selectedTest === 'all' ? qcData : qcData.filter(q => q.testName === selectedTest);

  const handleRecord = async () => {
    try {
      await qualityControlService.record(recordForm);
      setShowRecord(false);
      setRecordForm({ testName: '', level: 'L1', value: 0, deviceId: '', performedBy: '' });
      loadQC();
    } catch { /* ignore */ }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">مراقبة الجودة</h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">IQC و EQA - مخططات Levey-Jennings</p>
        </div>
        <button
          type="button"
          onClick={() => setShowRecord(true)}
          className="px-4 py-2.5 bg-primary-500 text-white rounded-xl font-bold text-sm hover:bg-primary-600 transition-colors"
        >
          تسجيل QC جديد
        </button>
      </div>

      <div className="flex gap-2">
        {['iqc', 'eqa'].map(tab => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab as any)}
            className={cn(
              'px-4 py-2 rounded-xl text-xs font-bold transition-all',
              activeTab === tab ? 'bg-primary-500 text-white shadow-sm' : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200',
            )}
          >
            {tab === 'iqc' ? 'IQC - مراقبة داخلية' : 'EQA - تقييم خارجي'}
          </button>
        ))}
      </div>

      {activeTab === 'iqc' && (
        <>
          <div className="flex gap-2 flex-wrap">
            <button
              type="button"
              onClick={() => setSelectedTest('all')}
              className={cn('px-3 py-1.5 rounded-lg text-[10px] font-bold transition-colors', selectedTest === 'all' ? 'bg-primary-500 text-white' : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-600')}
            >
              الكل
            </button>
            {testNames.map(name => (
              <button
                key={name}
                type="button"
                onClick={() => setSelectedTest(name)}
                className={cn('px-3 py-1.5 rounded-lg text-[10px] font-bold transition-colors', selectedTest === name ? 'bg-primary-500 text-white' : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-600')}
              >
                {name}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="text-center py-12 text-neutral-400">جاري التحميل...</div>
          ) : filteredQC.length === 0 ? (
            <div className="text-center py-12 bg-white dark:bg-neutral-800 rounded-2xl border-2 border-dashed border-neutral-300 dark:border-neutral-600">
              <p className="text-neutral-500">لا توجد بيانات QC متاحة</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {filteredQC.map(qc => (
                <div key={qc.id} className="bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 p-6 shadow-sm">
                  <QCChart data={qc} />
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {activeTab === 'eqa' && (
        <EQAView />
      )}

      {showRecord && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm">
          <div className="bg-white dark:bg-neutral-800 rounded-3xl p-8 w-full max-w-lg shadow-2xl border border-neutral-200 dark:border-neutral-700 space-y-5">
            <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">تسجيل QC جديد</h3>

            <div className="space-y-2">
              <label className="text-xs font-bold text-neutral-600 dark:text-neutral-400">اسم الفحص</label>
              <input type="text" value={recordForm.testName} onChange={e => setRecordForm(f => ({ ...f, testName: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs font-bold text-neutral-600 dark:text-neutral-400">المستوى</label>
                <select value={recordForm.level} onChange={e => setRecordForm(f => ({ ...f, level: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm">
                  <option value="L1">L1</option>
                  <option value="L2">L2</option>
                  <option value="L3">L3</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-neutral-600 dark:text-neutral-400">القيمة</label>
                <input type="number" step="0.01" value={recordForm.value} onChange={e => setRecordForm(f => ({ ...f, value: Number(e.target.value) }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" />
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button type="button" onClick={handleRecord} className="flex-1 py-3 bg-primary-500 text-white rounded-xl font-bold text-sm hover:bg-primary-600">تسجيل</button>
              <button type="button" onClick={() => setShowRecord(false)} className="px-6 py-3 bg-neutral-100 dark:bg-neutral-700 text-neutral-600 rounded-xl font-bold text-sm">إلغاء</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function EQAView() {
  const [eqaData, setEqaData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    qualityControlService.getEQA().then(data => setEqaData(data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center py-8 text-neutral-400">جاري التحميل...</div>;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {eqaData.map(eqa => (
          <div key={eqa.id} className={cn(
            'p-5 rounded-2xl border-2 bg-white dark:bg-neutral-800',
            eqa.acceptable ? 'border-success-200 dark:border-success-700' : 'border-danger-200 dark:border-danger-700',
          )}>
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-bold">{eqa.analyte}</span>
              <span className={cn('px-2 py-0.5 rounded text-[9px] font-bold', eqa.acceptable ? 'bg-success-50 text-success-600' : 'bg-danger-50 text-danger-600')}>
                {eqa.acceptable ? 'مقبول' : 'غير مقبول'}
              </span>
            </div>
            <div className="space-y-1 text-xs text-neutral-500">
              <p>البرنامج: {eqa.scheme}</p>
              <p>القيمة المخصصة: {eqa.assignedValue}</p>
              <p>قيمة المختبر: {eqa.labValue}</p>
              <p>Z-Score: <span className={cn('font-bold', Math.abs(eqa.zScore) > 2 ? 'text-danger-500' : 'text-success-500')}>{eqa.zScore.toFixed(2)}</span></p>
            </div>
          </div>
        ))}
      </div>
      {eqaData.length === 0 && (
        <div className="text-center py-12 text-neutral-400">لا توجد بيانات EQA</div>
      )}
    </div>
  );
}
