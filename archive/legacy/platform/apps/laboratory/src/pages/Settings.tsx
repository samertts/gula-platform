import { useState } from 'react';
import { cn } from '@gula/ui-platform';
import { useLab } from '@/contexts/LabContext';
import { Card, CardBody, CardHeader } from '@gula/ui-platform';

export function Settings() {
  const { user, logout } = useLab();
  const [activeTab, setActiveTab] = useState<'general' | 'notifications' | 'security' | 'about'>('general');

  const tabs = [
    { id: 'general' as const, label: 'عام' },
    { id: 'notifications' as const, label: 'الإشعارات' },
    { id: 'security' as const, label: 'الأمان' },
    { id: 'about' as const, label: 'حول' },
  ];

  return (
    <div className="p-6 space-y-6 max-w-6xl">
      <h1 className="text-2xl font-black text-neutral-900 dark:text-neutral-100">الإعدادات</h1>
      <p className="text-sm text-neutral-500 -mt-5">إعدادات التطبيق والمستخدم</p>

      <div className="flex gap-2">
        {tabs.map(tab => (
          <button key={tab.id} type="button" onClick={() => setActiveTab(tab.id)} className={cn('px-4 py-2 rounded-xl text-xs font-bold transition-all', activeTab === tab.id ? 'bg-primary-500 text-white' : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-600')}>
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'general' && (
        <Card>
          <CardHeader><span className="font-bold">الإعدادات العامة</span></CardHeader>
          <CardBody className="space-y-6">
            <div className="flex items-center justify-between">
              <div><p className="font-bold text-neutral-900 dark:text-neutral-100">الوضع المظلم</p><p className="text-xs text-neutral-500">تفعيل المظهر الداكن</p></div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" onChange={() => {
                  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
                  document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
                }} />
                <div className="w-11 h-6 bg-neutral-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-200 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500" />
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div><p className="font-bold text-neutral-900 dark:text-neutral-100">اللغة</p><p className="text-xs text-neutral-500">لغة الواجهة</p></div>
              <select className="px-4 py-2 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl bg-white dark:bg-neutral-800 text-sm">
                <option value="ar">العربية</option>
                <option value="en">English</option>
              </select>
            </div>

            <div className="flex items-center justify-between">
              <div><p className="font-bold text-neutral-900 dark:text-neutral-100">الصوت</p><p className="text-xs text-neutral-500">تشغيل صوت عند مسح الباركود</p></div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" defaultChecked className="sr-only peer" />
                <div className="w-11 h-6 bg-neutral-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-200 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500" />
              </label>
            </div>
          </CardBody>
        </Card>
      )}

      {activeTab === 'notifications' && (
        <Card>
          <CardHeader><span className="font-bold">إعدادات الإشعارات</span></CardHeader>
          <CardBody className="space-y-4">
            {[
              { label: 'القيم الحرجة', desc: 'تنبيه عند ظهور قيمة حرجة' },
              { label: 'نتائج QC', desc: 'إشعار عند فشل مراقبة الجودة' },
              { label: 'مخزون منخفض', desc: 'تنبيه عند انخفاض المخزون' },
              { label: 'حالة الأجهزة', desc: 'إشعار عند تغير حالة جهاز' },
            ].map(item => (
              <div key={item.label} className="flex items-center justify-between">
                <div><p className="font-bold text-sm text-neutral-900 dark:text-neutral-100">{item.label}</p><p className="text-xs text-neutral-500">{item.desc}</p></div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" defaultChecked className="sr-only peer" />
                  <div className="w-11 h-6 bg-neutral-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-200 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500" />
                </label>
              </div>
            ))}
          </CardBody>
        </Card>
      )}

      {activeTab === 'security' && (
        <Card>
          <CardHeader><span className="font-bold">الأمان</span></CardHeader>
          <CardBody className="space-y-4">
            <button type="button" className="w-full p-4 bg-neutral-50 dark:bg-neutral-700/50 rounded-xl text-right">
              <p className="font-bold text-sm text-neutral-900 dark:text-neutral-100">تغيير كلمة المرور</p>
              <p className="text-xs text-neutral-500">آخر تغيير: قبل 30 يوماً</p>
            </button>
            <button type="button" className="w-full p-4 bg-neutral-50 dark:bg-neutral-700/50 rounded-xl text-right">
              <p className="font-bold text-sm text-neutral-900 dark:text-neutral-100">المصادقة الثنائية</p>
              <p className="text-xs text-neutral-500">غير مفعلة</p>
            </button>
            <div className="p-4 bg-neutral-50 dark:bg-neutral-700/50 rounded-xl">
              <p className="font-bold text-sm text-neutral-900 dark:text-neutral-100">جلسات النشطة</p>
              <p className="text-xs text-neutral-500 mt-1">لا توجد جلسات نشطة أخرى</p>
            </div>
          </CardBody>
        </Card>
      )}

      {activeTab === 'about' && (
        <Card>
          <CardHeader><span className="font-bold">حول التطبيق</span></CardHeader>
          <CardBody className="space-y-4">
            <div className="flex items-center justify-center py-6">
              <div className="w-20 h-20 bg-primary-500 rounded-3xl flex items-center justify-center">
                <span className="text-white font-black text-3xl">G</span>
              </div>
            </div>
            <div className="text-center">
              <h3 className="text-lg font-black text-neutral-900 dark:text-neutral-100">GULA مختبر</h3>
              <p className="text-sm text-neutral-500">نظام إدارة معلومات المختبرات</p>
              <p className="text-xs text-neutral-400 mt-1">الإصدار 2.1.0</p>
            </div>
            <div className="pt-4 border-t border-neutral-100 dark:border-neutral-700">
              <button
                type="button"
                onClick={logout}
                className="w-full py-3 bg-danger-50 dark:bg-danger-900/30 text-danger-600 dark:text-danger-400 rounded-xl font-bold text-sm hover:bg-danger-100 dark:hover:bg-danger-900/50 transition-colors"
              >
                تسجيل الخروج
              </button>
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
