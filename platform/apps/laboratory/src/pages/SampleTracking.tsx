import { useState, useEffect } from 'react';
import { cn } from '@gula/ui-platform';
import { samplesService } from '@/services/samples';
import { SampleTimeline } from '@/components/SampleTimeline';
import { BarcodeScanner } from '@/components/BarcodeScanner';
import type { Sample } from '@/utils/types';

export function SampleTracking() {
  const [samples, setSamples] = useState<Sample[]>([]);
  const [selectedSample, setSelectedSample] = useState<Sample | null>(null);
  const [timeline, setTimeline] = useState<{ status: string; timestamp: string; by: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    loadSamples();
  }, []);

  async function loadSamples() {
    setLoading(true);
    try {
      const result = await samplesService.list({ perPage: 100 });
      setSamples(result.data);
    } catch { /* ignore */ }
    setLoading(false);
  }

  const handleScan = async (barcode: string) => {
    try {
      const sample = await samplesService.getByBarcode(barcode);
      setSelectedSample(sample);
      const tl = await samplesService.getTimeline(sample.id);
      setTimeline(tl as any);
    } catch { /* ignore */ }
  };

  const selectSample = async (sample: Sample) => {
    setSelectedSample(sample);
    try {
      const tl = await samplesService.getTimeline(sample.id);
      setTimeline(tl as any);
    } catch { /* ignore */ }
  };

  const filteredSamples = samples.filter(s =>
    s.sampleId.toLowerCase().includes(filter.toLowerCase()) ||
    s.patientName.includes(filter) ||
    s.barcode.toLowerCase().includes(filter.toLowerCase())
  );

  const statusColor = (status: string) => {
    if (['verified', 'validated', 'released'].includes(status)) return 'bg-success-100 text-success-700 dark:bg-success-900/30 dark:text-success-400';
    if (['rejected', 'disposed'].includes(status)) return 'bg-danger-100 text-danger-700 dark:bg-danger-900/30 dark:text-danger-400';
    if (['processing', 'analyzing'].includes(status)) return 'bg-warning-100 text-warning-700 dark:bg-warning-900/30 dark:text-warning-400';
    if (['ordered', 'registered', 'collected'].includes(status)) return 'bg-info-100 text-info-700 dark:bg-info-900/30 dark:text-info-400';
    return 'bg-neutral-100 text-neutral-600 dark:bg-neutral-700 dark:text-neutral-400';
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">تتبع العينات</h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">تتبع حالة العينات عبر سير العمل</p>
        </div>
      </div>

      <BarcodeScanner onScan={handleScan} placeholder="امسح باركود العينة للتتبع" />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-3">
          <input
            type="text"
            value={filter}
            onChange={e => setFilter(e.target.value)}
            placeholder="بحث برقم العينة أو اسم المريض..."
            className="w-full px-4 py-2.5 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm focus:border-primary-500 focus:outline-none dark:text-neutral-100"
          />

          {loading ? (
            <div className="text-center py-8 text-neutral-400">جاري التحميل...</div>
          ) : filteredSamples.length === 0 ? (
            <div className="text-center py-8 text-neutral-400">لا توجد عينات</div>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {filteredSamples.map(sample => (
                <button
                  key={sample.id}
                  type="button"
                  onClick={() => selectSample(sample)}
                  className={cn(
                    'w-full text-right p-4 rounded-xl border-2 transition-all bg-white dark:bg-neutral-800',
                    selectedSample?.id === sample.id
                      ? 'border-primary-500 shadow-md bg-primary-50/30 dark:bg-primary-900/10'
                      : 'border-neutral-200 dark:border-neutral-700 hover:border-neutral-300',
                  )}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-xs font-bold">{sample.sampleId}</span>
                    <span className={cn('px-2 py-0.5 rounded text-[9px] font-bold', statusColor(sample.status))}>
                      {sample.status}
                    </span>
                  </div>
                  <p className="text-sm font-bold text-neutral-900 dark:text-neutral-100">{sample.patientName}</p>
                  <div className="flex items-center gap-2 text-xs text-neutral-500 mt-1">
                    <span>{sample.tests.length} فحص</span>
                    <span>•</span>
                    <span>{new Date(sample.createdAt).toLocaleDateString('ar-IQ')}</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        <div>
          {selectedSample ? (
            <div className="bg-white dark:bg-neutral-800 rounded-2xl border-2 border-neutral-200 dark:border-neutral-700 p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">
                  {selectedSample.sampleId}
                </h3>
                <span className={cn('px-3 py-1 rounded-full text-xs font-bold', statusColor(selectedSample.status))}>
                  {selectedSample.status}
                </span>
              </div>

              <div className="space-y-2 mb-6 pb-6 border-b border-neutral-100 dark:border-neutral-700">
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-500">المريض</span>
                  <span className="font-bold">{selectedSample.patientName}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-500">معرف المريض</span>
                  <span className="font-mono">{selectedSample.patientId}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-500">نوع العينة</span>
                  <span>{selectedSample.specimenType}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-500">الفحوصات</span>
                  <span>{selectedSample.tests.join(' • ')}</span>
                </div>
              </div>

              <h4 className="text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-4">الجدول الزمني</h4>
              <SampleTimeline events={timeline} currentStatus={selectedSample.status} />
            </div>
          ) : (
            <div className="bg-white dark:bg-neutral-800 rounded-2xl border-2 border-dashed border-neutral-300 dark:border-neutral-600 p-12 text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-neutral-100 dark:bg-neutral-700 rounded-2xl flex items-center justify-center text-neutral-400">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
              </div>
              <p className="text-sm text-neutral-500 dark:text-neutral-400">اختر عينة من القائمة أو امسح باركود</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
