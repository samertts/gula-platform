import { useState, useEffect } from 'react';
import { cn } from '@gula/ui-platform';
import { analyzersService } from '@/services/analyzers';
import { InstrumentCard } from '@/components/InstrumentCard';
import type { Analyzer } from '@/utils/types';

export function AnalyzerIntegration() {
  const [analyzers, setAnalyzers] = useState<Analyzer[]>([]);
  const [loading, setLoading] = useState(true);
  const [showRegister, setShowRegister] = useState(false);
  const [form, setForm] = useState({
    name: '', model: '', serialNumber: '', manufacturer: '',
    connectionType: 'astm' as const, ipAddress: '', port: 0, location: '',
  });

  useEffect(() => { loadAnalyzers(); }, []);

  async function loadAnalyzers() {
    setLoading(true);
    try { const data = await analyzersService.list(); setAnalyzers(data); } catch { /* ignore */ }
    setLoading(false);
  }

  const handleRegister = async () => {
    try {
      await analyzersService.register(form);
      setShowRegister(false);
      loadAnalyzers();
    } catch { /* ignore */ }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">ربط الأجهزة</h1>
          <p className="text-sm text-neutral-500 mt-1">إدارة وتكوين أجهزة التحليل المتصلة</p>
        </div>
        <button type="button" onClick={() => setShowRegister(true)} className="px-4 py-2.5 bg-primary-500 text-white rounded-xl font-bold text-sm hover:bg-primary-600">تسجيل جهاز جديد</button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-neutral-400">جاري التحميل...</div>
      ) : analyzers.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-neutral-800 rounded-2xl border-2 border-dashed border-neutral-300">
          <p className="text-neutral-500">لا توجد أجهزة مسجلة. أضف جهازاً جديداً.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {analyzers.map(analyzer => (
            <InstrumentCard key={analyzer.id} analyzer={analyzer} />
          ))}
        </div>
      )}

      {showRegister && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm">
          <div className="bg-white dark:bg-neutral-800 rounded-3xl p-8 w-full max-w-lg shadow-2xl border border-neutral-200 dark:border-neutral-700 space-y-5">
            <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">تسجيل جهاز جديد</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2 col-span-2"><label className="text-xs font-bold text-neutral-600">اسم الجهاز</label><input type="text" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" /></div>
              <div className="space-y-2"><label className="text-xs font-bold text-neutral-600">الطراز</label><input type="text" value={form.model} onChange={e => setForm(f => ({ ...f, model: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" /></div>
              <div className="space-y-2"><label className="text-xs font-bold text-neutral-600">الرقم التسلسلي</label><input type="text" value={form.serialNumber} onChange={e => setForm(f => ({ ...f, serialNumber: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" /></div>
              <div className="space-y-2"><label className="text-xs font-bold text-neutral-600">الشركة المصنعة</label><input type="text" value={form.manufacturer} onChange={e => setForm(f => ({ ...f, manufacturer: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" /></div>
              <div className="space-y-2"><label className="text-xs font-bold text-neutral-600">نوع الاتصال</label><select value={form.connectionType} onChange={e => setForm(f => ({ ...f, connectionType: e.target.value as any }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm">
                <option value="astm">ASTM</option><option value="hl7">HL7</option><option value="serial">Serial</option><option value="tcpip">TCP/IP</option><option value="file">ملف</option><option value="manual">يدوي</option>
              </select></div>
              <div className="space-y-2"><label className="text-xs font-bold text-neutral-600">الموقع</label><input type="text" value={form.location} onChange={e => setForm(f => ({ ...f, location: e.target.value }))} className="w-full px-4 py-3 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm" /></div>
            </div>
            <div className="flex gap-3 pt-2">
              <button type="button" onClick={handleRegister} className="flex-1 py-3 bg-primary-500 text-white rounded-xl font-bold text-sm hover:bg-primary-600">تسجيل</button>
              <button type="button" onClick={() => setShowRegister(false)} className="px-6 py-3 bg-neutral-100 dark:bg-neutral-700 text-neutral-600 rounded-xl font-bold text-sm">إلغاء</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
