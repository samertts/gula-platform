import { useState, useEffect } from 'react';
import { cn } from '@gula/ui-platform';
import { useWorklist } from '@/contexts/WorklistContext';
import { samplesService } from '@/services/samples';
import { WorklistItem } from '@/components/WorklistItem';
import { BarcodeScanner } from '@/components/BarcodeScanner';
import type { Sample, Priority } from '@/utils/types';

export function Worklist() {
  const { filteredSamples, setSamples, filterStatus, setFilterStatus, filterPriority, setFilterPriority, searchQuery, setSearchQuery } = useWorklist();
  const [loading, setLoading] = useState(true);
  const [showScanner, setShowScanner] = useState(false);
  const [selectedSample, setSelectedSample] = useState<Sample | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');

  useEffect(() => {
    loadSamples();
  }, []);

  async function loadSamples() {
    setLoading(true);
    try {
      const result = await samplesService.list({ perPage: 50 });
      setSamples(result.data);
    } catch { /* ignore */ }
    setLoading(false);
  }

  const statuses = ['ordered', 'registered', 'collected', 'received', 'accepted', 'processing', 'analyzing', 'analyzed', 'verified'];
  const priorities: Priority[] = ['routine', 'urgent', 'stat'];

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">قائمة العمل</h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">جميع العينات والطلبات</p>
        </div>
        <button
          type="button"
          onClick={() => setShowScanner(!showScanner)}
          className={cn(
            'px-4 py-2.5 rounded-xl font-bold text-sm transition-all flex items-center gap-2',
            showScanner
              ? 'bg-danger-50 text-danger-600 dark:bg-danger-900/30 dark:text-danger-400'
              : 'bg-primary-50 text-primary-600 dark:bg-primary-900/30 dark:text-primary-400',
          )}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
            <circle cx="12" cy="13" r="3" />
          </svg>
          {showScanner ? 'إخفاء الماسح' : 'مسح باركود'}
        </button>
      </div>

      {showScanner && (
        <BarcodeScanner
          onScan={(barcode) => {
            setSearchQuery(barcode);
            setShowScanner(false);
          }}
        />
      )}

      <div className="space-y-3">
        <div className="flex flex-wrap gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="بحث برقم العينة أو اسم المريض..."
            className="flex-1 min-w-[200px] px-4 py-2.5 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm focus:border-primary-500 focus:outline-none dark:text-neutral-100"
          />
          <select
            value={filterPriority.join(',')}
            onChange={e => setFilterPriority(e.target.value ? e.target.value.split(',') as Priority[] : [])}
            className="px-4 py-2.5 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm focus:border-primary-500 focus:outline-none dark:text-neutral-100"
          >
            <option value="">كل الأولويات</option>
            <option value="stat">STAT</option>
            <option value="urgent">عاجل</option>
            <option value="routine">روتين</option>
          </select>
          <div className="flex gap-1">
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className={cn('p-2.5 rounded-xl border-2 transition-colors', viewMode === 'list' ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30' : 'border-neutral-200 dark:border-neutral-700')}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="8" y1="6" x2="21" y2="6" /><line x1="8" y1="12" x2="21" y2="12" /><line x1="8" y1="18" x2="21" y2="18" /><line x1="3" y1="6" x2="3.01" y2="6" /><line x1="3" y1="12" x2="3.01" y2="12" /><line x1="3" y1="18" x2="3.01" y2="18" /></svg>
            </button>
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              className={cn('p-2.5 rounded-xl border-2 transition-colors', viewMode === 'grid' ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30' : 'border-neutral-200 dark:border-neutral-700')}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /></svg>
            </button>
          </div>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {statuses.map(status => (
            <button
              key={status}
              type="button"
              onClick={() => setFilterStatus(filterStatus.includes(status) ? filterStatus.filter(s => s !== status) : [...filterStatus, status])}
              className={cn(
                'px-2.5 py-1 rounded-lg text-[10px] font-bold transition-colors',
                filterStatus.includes(status)
                  ? 'bg-primary-500 text-white'
                  : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-600',
              )}
            >
              {statusLabel(status)}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-neutral-400">جاري التحميل...</span>
          </div>
        </div>
      ) : filteredSamples.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 bg-neutral-100 dark:bg-neutral-700 rounded-2xl flex items-center justify-center text-neutral-400">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2" /><line x1="3" y1="9" x2="21" y2="9" /><line x1="9" y1="21" x2="9" y2="9" /></svg>
          </div>
          <p className="text-sm text-neutral-500 dark:text-neutral-400">لا توجد عينات مطابقة</p>
        </div>
      ) : viewMode === 'list' ? (
        <div className="space-y-3">
          {filteredSamples.map(sample => (
            <WorklistItem
              key={sample.id}
              sample={sample}
              onSelect={setSelectedSample}
              selected={selectedSample?.id === sample.id}
            />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSamples.map(sample => (
            <WorklistItem
              key={sample.id}
              sample={sample}
              onSelect={setSelectedSample}
              selected={selectedSample?.id === sample.id}
              compact
            />
          ))}
        </div>
      )}
    </div>
  );
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    ordered: 'مطلوب', registered: 'مسجل', collected: 'مجموع',
    received: 'مستلم', accepted: 'مقبول', processing: 'معالجة',
    analyzing: 'تحليل', analyzed: 'تم التحليل', verified: 'تم التحقق',
    validated: 'معتمد', released: 'منشور',
  };
  return labels[status] || status;
}
