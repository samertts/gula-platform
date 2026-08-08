import { useState, useEffect } from 'react';
import { cn } from '@gula/ui-platform';
import { inventoryService } from '@/services/inventory';
import { ReagentLevel } from '@/components/ReagentLevel';
import type { InventoryItem } from '@/utils/types';

export function Inventory() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'reagent' | 'consumable' | 'low'>('all');
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: '', category: 'reagent' as const, quantity: 0, minimumStock: 10, maximumStock: 100, unit: 'ml', supplier: '', location: '', expiryDate: '' });

  useEffect(() => { loadItems(); }, []);

  async function loadItems() {
    setLoading(true);
    try { const data = await inventoryService.list({ perPage: 100 }); setItems(data.data); } catch { /* ignore */ }
    setLoading(false);
  }

  const filteredItems = items.filter(i => {
    if (filter === 'low') return i.quantity <= i.minimumStock;
    if (filter === 'reagent') return i.category === 'reagent';
    if (filter === 'consumable') return i.category === 'consumable';
    return true;
  });

  const handleAdd = async () => {
    try { await inventoryService.create(form); setShowAdd(false); loadItems(); } catch { /* ignore */ }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">المخزون</h1>
          <p className="text-sm text-neutral-500 mt-1">إدارة المواد والكواشف والمستهلكات</p>
        </div>
        <button type="button" onClick={() => setShowAdd(true)} className="px-4 py-2.5 bg-primary-500 text-white rounded-xl font-bold text-sm hover:bg-primary-600">إضافة صنف</button>
      </div>

      <div className="flex gap-2">
        {(['all', 'reagent', 'consumable', 'low'] as const).map(f => (
          <button key={f} type="button" onClick={() => setFilter(f)} className={cn('px-4 py-2 rounded-xl text-xs font-bold transition-all', filter === f ? 'bg-primary-500 text-white' : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-600')}>
            {f === 'all' ? 'الكل' : f === 'reagent' ? 'كواشف' : f === 'consumable' ? 'مستهلكات' : 'مخزون منخفض'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-12 text-neutral-400">جاري التحميل...</div>
      ) : filteredItems.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-neutral-800 rounded-2xl border-2 border-dashed border-neutral-300"><p className="text-neutral-500">لا توجد أصناف</p></div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredItems.map(item => (
            <ReagentLevel
              key={item.id}
              name={item.name}
              current={item.quantity}
              min={item.minimumStock}
              max={item.maximumStock}
              unit={item.unit}
              expiryDate={item.expiryDate}
              lotNumber={item.lotNumber}
            />
          ))}
        </div>
      )}

      {showAdd && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm">
          <div className="bg-white dark:bg-neutral-800 rounded-3xl p-8 w-full max-w-lg shadow-2xl border border-neutral-200 dark:border-neutral-700 space-y-5">
            <h3 className="text-lg font-bold">إضافة صنف جديد</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2 space-y-2"><label className="text-xs font-bold text-neutral-600">الاسم</label><input type="text" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" /></div>
              <div className="space-y-2"><label className="text-xs font-bold text-neutral-600">الفئة</label><select value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value as any }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm"><option value="reagent">كاشف</option><option value="consumable">مستهلك</option><option value="calibrator">معاير</option><option value="control">كونترول</option></select></div>
              <div className="space-y-2"><label className="text-xs font-bold text-neutral-600">الوحدة</label><input type="text" value={form.unit} onChange={e => setForm(f => ({ ...f, unit: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" /></div>
              <div className="space-y-2"><label className="text-xs font-bold text-neutral-600">الكمية</label><input type="number" value={form.quantity} onChange={e => setForm(f => ({ ...f, quantity: Number(e.target.value) }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" /></div>
              <div className="space-y-2"><label className="text-xs font-bold text-neutral-600">الحد الأدنى</label><input type="number" value={form.minimumStock} onChange={e => setForm(f => ({ ...f, minimumStock: Number(e.target.value) }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" /></div>
              <div className="space-y-2"><label className="text-xs font-bold text-neutral-600">الحد الأقصى</label><input type="number" value={form.maximumStock} onChange={e => setForm(f => ({ ...f, maximumStock: Number(e.target.value) }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" /></div>
              <div className="space-y-2"><label className="text-xs font-bold text-neutral-600">الموقع</label><input type="text" value={form.location} onChange={e => setForm(f => ({ ...f, location: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" /></div>
              <div className="space-y-2"><label className="text-xs font-bold text-neutral-600">تاريخ الانتهاء</label><input type="date" value={form.expiryDate} onChange={e => setForm(f => ({ ...f, expiryDate: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" /></div>
            </div>
            <div className="flex gap-3 pt-2">
              <button type="button" onClick={handleAdd} className="flex-1 py-3 bg-primary-500 text-white rounded-xl font-bold text-sm hover:bg-primary-600">إضافة</button>
              <button type="button" onClick={() => setShowAdd(false)} className="px-6 py-3 bg-neutral-100 dark:bg-neutral-700 rounded-xl font-bold text-sm">إلغاء</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
