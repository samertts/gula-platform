import { useState, useEffect } from 'react';
import { cn } from '@gula/ui-platform';
import { resultsService } from '@/services/results';
import type { AutoverificationRule } from '@/utils/types';

export function Autoverification() {
  const [rules, setRules] = useState<AutoverificationRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [editingRule, setEditingRule] = useState<AutoverificationRule | null>(null);
  const [form, setForm] = useState({
    name: '', testName: '', conditions: [{ field: 'value' as const, operator: 'between' as const, value: '' }],
    action: 'auto_verify' as const, priority: 1,
  });

  useEffect(() => {
    loadRules();
  }, []);

  async function loadRules() {
    setLoading(true);
    try {
      const data = await resultsService.getAutoverificationRules();
      setRules(data);
    } catch { /* ignore */ }
    setLoading(false);
  }

  const handleToggle = async (rule: AutoverificationRule) => {
    try {
      await resultsService.updateAutoverificationRule(rule.id, { isActive: !rule.isActive });
      loadRules();
    } catch { /* ignore */ }
  };

  const handleSave = async () => {
    try {
      if (editingRule) {
        await resultsService.updateAutoverificationRule(editingRule.id, form);
      } else {
        await resultsService.createAutoverificationRule(form);
      }
      setShowNew(false);
      setEditingRule(null);
      loadRules();
    } catch { /* ignore */ }
  };

  const actionLabel = (action: string) => ({ auto_verify: 'تحقق تلقائي', flag_review: 'علم للمراجعة', reject: 'رفض' }[action] || action);

  return (
    <div className="p-6 space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">التحقق الآلي</h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">قواعد التحقق التلقائي من النتائج</p>
        </div>
        <button type="button" onClick={() => { setShowNew(true); setEditingRule(null); }} className="px-4 py-2.5 bg-primary-500 text-white rounded-xl font-bold text-sm hover:bg-primary-600">إضافة قاعدة</button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-neutral-400">جاري التحميل...</div>
      ) : rules.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-neutral-800 rounded-2xl border-2 border-dashed border-neutral-300">
          <p className="text-neutral-500">لا توجد قواعد تحقق آلي. أضف قاعدة جديدة.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {rules.map(rule => (
            <div key={rule.id} className={cn(
              'bg-white dark:bg-neutral-800 rounded-2xl border-2 p-5 transition-all',
              rule.isActive ? 'border-neutral-200 dark:border-neutral-700' : 'border-neutral-100 dark:border-neutral-800 opacity-60',
            )}>
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-bold text-neutral-900 dark:text-neutral-100">{rule.name}</span>
                    <span className={cn(
                      'px-2 py-0.5 rounded text-[9px] font-bold',
                      rule.action === 'auto_verify' ? 'bg-success-50 text-success-600' :
                      rule.action === 'flag_review' ? 'bg-warning-50 text-warning-600' :
                      'bg-danger-50 text-danger-600',
                    )}>
                      {actionLabel(rule.action)}
                    </span>
                    <span className="text-[10px] text-neutral-400">الأولوية: {rule.priority}</span>
                  </div>
                  <p className="text-xs text-neutral-500">الفحص: {rule.testName}</p>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {rule.conditions.map((c, i) => (
                      <span key={i} className="px-2 py-0.5 bg-neutral-100 dark:bg-neutral-700 rounded text-[9px] font-medium">
                        {c.field} {c.operator} {Array.isArray(c.value) ? c.value.join(', ') : c.value}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" checked={rule.isActive} onChange={() => handleToggle(rule)} className="sr-only peer" />
                    <div className="w-10 h-5 bg-neutral-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-200 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary-500" />
                  </label>
                  <button type="button" onClick={() => { setEditingRule(rule); setForm({ name: rule.name, testName: rule.testName, conditions: rule.conditions, action: rule.action, priority: rule.priority }); setShowNew(true); }} className="p-2 text-neutral-400 hover:text-primary-500 rounded-xl hover:bg-primary-50 transition-colors">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" /></svg>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showNew && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm">
          <div className="bg-white dark:bg-neutral-800 rounded-3xl p-8 w-full max-w-lg shadow-2xl border border-neutral-200 dark:border-neutral-700 space-y-5">
            <h3 className="text-lg font-bold">{editingRule ? 'تعديل قاعدة' : 'إضافة قاعدة جديدة'}</h3>

            <div className="space-y-2">
              <label className="text-xs font-bold text-neutral-600 dark:text-neutral-400">اسم القاعدة</label>
              <input type="text" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-neutral-600 dark:text-neutral-400">اسم الفحص</label>
              <input type="text" value={form.testName} onChange={e => setForm(f => ({ ...f, testName: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs font-bold text-neutral-600 dark:text-neutral-400">الإجراء</label>
                <select value={form.action} onChange={e => setForm(f => ({ ...f, action: e.target.value as any }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm">
                  <option value="auto_verify">تحقق تلقائي</option>
                  <option value="flag_review">علم للمراجعة</option>
                  <option value="reject">رفض</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-neutral-600 dark:text-neutral-400">الأولوية</label>
                <input type="number" value={form.priority} onChange={e => setForm(f => ({ ...f, priority: Number(e.target.value) }))} min={1} max={100} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" />
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button type="button" onClick={handleSave} className="flex-1 py-3 bg-primary-500 text-white rounded-xl font-bold text-sm hover:bg-primary-600">حفظ</button>
              <button type="button" onClick={() => setShowNew(false)} className="px-6 py-3 bg-neutral-100 dark:bg-neutral-700 text-neutral-600 rounded-xl font-bold text-sm">إلغاء</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
