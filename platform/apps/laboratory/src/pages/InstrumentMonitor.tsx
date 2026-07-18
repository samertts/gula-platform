import { useState, useEffect } from 'react';
import { cn } from '@gula/ui-platform';
import { analyzersService } from '@/services/analyzers';
import { InstrumentCard } from '@/components/InstrumentCard';
import type { Analyzer } from '@/utils/types';

export function InstrumentMonitor() {
  const [analyzers, setAnalyzers] = useState<Analyzer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalyzers();
    const interval = setInterval(loadAnalyzers, 15000);
    return () => clearInterval(interval);
  }, []);

  async function loadAnalyzers() {
    try { const data = await analyzersService.list(); setAnalyzers(data); } catch { /* ignore */ }
    setLoading(false);
  }

  const online = analyzers.filter(a => a.status === 'online').length;
  const offline = analyzers.filter(a => a.status === 'offline' || a.status === 'error').length;

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">مراقبة الأجهزة</h1>
          <p className="text-sm text-neutral-500 mt-1">مراقبة لحظية لأجهزة التحليل</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-success-500" />
            <span className="text-xs font-bold text-success-600">{online} متصل</span>
          </div>
          <div className="flex items-center gap-2">
            <div className={cn('w-2 h-2 rounded-full', offline > 0 ? 'bg-danger-500 animate-pulse' : 'bg-neutral-400')} />
            <span className={cn('text-xs font-bold', offline > 0 ? 'text-danger-600' : 'text-neutral-500')}>{offline} غير متصل</span>
          </div>
          <span className="text-[10px] text-neutral-400">تحديث تلقائي كل 15 ثانية</span>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12 text-neutral-400">جاري التحميل...</div>
      ) : analyzers.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-neutral-800 rounded-2xl border-2 border-dashed border-neutral-300">
          <p className="text-neutral-500">لا توجد أجهزة للمراقبة</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {analyzers.map(analyzer => (
            <InstrumentCard key={analyzer.id} analyzer={analyzer} />
          ))}
        </div>
      )}
    </div>
  );
}
