import { useState, useEffect } from 'react';
import { cn } from '@gula/ui-platform';
import { apiRequest } from '@/services/api';
import type { AuditEntry } from '@/utils/types';

export function AuditLog() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ action: '', entityType: '', dateFrom: '', dateTo: '' });
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const perPage = 25;

  useEffect(() => {
    loadAuditLog();
  }, [page]);

  async function loadAuditLog() {
    setLoading(true);
    try {
      const query = new URLSearchParams({ page: String(page), per_page: String(perPage) });
      if (filter.action) query.set('action', filter.action);
      if (filter.entityType) query.set('entity_type', filter.entityType);
      if (filter.dateFrom) query.set('date_from', filter.dateFrom);
      if (filter.dateTo) query.set('date_to', filter.dateTo);

      const data = await apiRequest<{ data: AuditEntry[]; total: number }>(`/audit-log?${query.toString()}`);
      setEntries(data.data);
      setTotal(data.total);
    } catch { /* ignore */ }
    setLoading(false);
  }

  const totalPages = Math.ceil(total / perPage);

  const actionArabic = (action: string) => {
    const actions: Record<string, string> = {
      create: 'إنشاء', update: 'تحديث', delete: 'حذف', read: 'قراءة',
      login: 'دخول', logout: 'خروج', verify: 'تحقق', reject: 'رفض',
      approve: 'اعتماد', print: 'طباعة', export: 'تصدير', import: 'استيراد',
    };
    return actions[action] || action;
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">سجل التدقيق</h1>
      <p className="text-sm text-neutral-500 -mt-5">سجل جميع العمليات والإجراءات في النظام</p>

      <div className="flex flex-wrap gap-3">
        <input type="text" value={filter.action} onChange={e => setFilter(f => ({ ...f, action: e.target.value }))} placeholder="الإجراء" className="px-4 py-2.5 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" />
        <input type="text" value={filter.entityType} onChange={e => setFilter(f => ({ ...f, entityType: e.target.value }))} placeholder="نوع الكيان" className="px-4 py-2.5 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" />
        <input type="date" value={filter.dateFrom} onChange={e => setFilter(f => ({ ...f, dateFrom: e.target.value }))} className="px-4 py-2.5 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" />
        <input type="date" value={filter.dateTo} onChange={e => setFilter(f => ({ ...f, dateTo: e.target.value }))} className="px-4 py-2.5 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" />
        <button type="button" onClick={() => { setPage(1); loadAuditLog(); }} className="px-4 py-2.5 bg-primary-500 text-white rounded-xl font-bold text-xs hover:bg-primary-600">بحث</button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-neutral-400">جاري التحميل...</div>
      ) : entries.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-neutral-800 rounded-2xl border-2 border-dashed border-neutral-300">
          <p className="text-neutral-500">لا توجد إدخالات في سجل التدقيق</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-right">
              <thead>
                <tr className="border-b border-neutral-100 dark:border-neutral-700">
                  <th className="px-5 py-4 text-[10px] font-black text-neutral-400 uppercase tracking-wider">التاريخ</th>
                  <th className="px-5 py-4 text-[10px] font-black text-neutral-400 uppercase tracking-wider">المستخدم</th>
                  <th className="px-5 py-4 text-[10px] font-black text-neutral-400 uppercase tracking-wider">الإجراء</th>
                  <th className="px-5 py-4 text-[10px] font-black text-neutral-400 uppercase tracking-wider">الكيان</th>
                  <th className="px-5 py-4 text-[10px] font-black text-neutral-400 uppercase tracking-wider">التفاصيل</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100 dark:divide-neutral-700">
                {entries.map(entry => (
                  <tr key={entry.id} className="hover:bg-neutral-50 dark:hover:bg-neutral-700/30 transition-colors">
                    <td className="px-5 py-4 text-xs text-neutral-500 whitespace-nowrap" dir="ltr">
                      {new Date(entry.timestamp).toLocaleString('ar-IQ')}
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-sm font-bold text-neutral-900 dark:text-neutral-100">{entry.userName}</span>
                    </td>
                    <td className="px-5 py-4">
                      <span className={cn(
                        'px-2 py-0.5 rounded text-[9px] font-bold',
                        entry.action === 'create' ? 'bg-success-50 text-success-600' :
                        entry.action === 'delete' ? 'bg-danger-50 text-danger-600' :
                        entry.action === 'update' ? 'bg-warning-50 text-warning-600' :
                        'bg-neutral-100 text-neutral-600',
                      )}>
                        {actionArabic(entry.action)}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-xs font-medium text-neutral-600 dark:text-neutral-400">
                        {entry.entityType}
                      </span>
                      <span className="text-xs text-neutral-400 font-mono mr-1">#{entry.entityId.slice(0, 8)}</span>
                    </td>
                    <td className="px-5 py-4 text-xs text-neutral-500 max-w-[200px] truncate">
                      {entry.details ? JSON.stringify(entry.details).slice(0, 60) : '---'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between px-5 py-4 border-t border-neutral-100 dark:border-neutral-700">
              <span className="text-xs text-neutral-500">
                الصفحة {page} من {totalPages} ({total} إجمالي)
              </span>
              <div className="flex gap-2">
                <button type="button" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1} className="px-3 py-1.5 bg-neutral-100 dark:bg-neutral-700 rounded-xl text-xs font-bold disabled:opacity-50 hover:bg-neutral-200">السابق</button>
                <button type="button" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages} className="px-3 py-1.5 bg-primary-500 text-white rounded-xl text-xs font-bold disabled:opacity-50 hover:bg-primary-600">التالي</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
