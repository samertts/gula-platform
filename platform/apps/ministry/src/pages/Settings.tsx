import { Card, Button, Select, useRTL } from '@gula/ui-platform';

export function Settings() {
  const { isRtl, toggleDirection } = useRTL();

  return (
    <div className="space-y-6 p-6 max-w-2xl mx-auto" dir="rtl">
      <h1 className="text-2xl font-bold text-white">الإعدادات</h1>

      <Card title="التفضيلات">
        <div className="space-y-4">
          <Select label="اللغة" value="ar" options={[{ value: 'ar', label: 'العربية' }, { value: 'en', label: 'English' }]} />
          <Select label="الوضع" value="dark" options={[{ value: 'light', label: 'فاتح' }, { value: 'dark', label: 'داكن' }, { value: 'system', label: 'تلقائي' }]} />
          <Button variant="secondary" onClick={toggleDirection}>{isRtl ? '→ English Layout' : '← تخطيط عربي'}</Button>
        </div>
      </Card>

      <Card title="الإشعارات">
        <div className="space-y-3">
          <label className="flex items-center gap-3"><input type="checkbox" defaultChecked /><span>إنذارات الطوارئ</span></label>
          <label className="flex items-center gap-3"><input type="checkbox" defaultChecked /><span>تقارير دورية</span></label>
          <label className="flex items-center gap-3"><input type="checkbox" defaultChecked /><span>تنبيهات التفشي الوبائي</span></label>
        </div>
      </Card>

      <Card title="حول">
        <p className="text-sm text-slate-400">GULA National Health Platform</p>
        <p className="text-sm text-slate-400">وزارة الصحة العراقية</p>
        <p className="text-sm text-slate-400">Ministry Dashboard v2.1.0</p>
      </Card>

      <Button variant="danger" onClick={() => {
        sessionStorage.removeItem('gula_ministry_demo_mode');
        void fetch('https://api.gula.health/api/v1/auth/logout', {
          method: 'POST',
          credentials: 'include',
        }).finally(() => window.location.assign('/login'));
      }}>
        تسجيل الخروج
      </Button>
    </div>
  );
}
