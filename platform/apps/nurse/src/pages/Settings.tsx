import { Card, Button, Select } from '@gula/ui-platform';
import { useNurse } from '../contexts/NurseContext';

export default function Settings() {
  const { user, logout } = useNurse();

  return (
    <div className="space-y-6 p-6 max-w-2xl mx-auto" dir="rtl">
      <h1 className="text-2xl font-bold">الإعدادات</h1>

      <Card title="الملف الشخصي">
        <div className="space-y-3">
          <p><strong>الاسم:</strong> {user?.name || 'ممرض/ة'}</p>
          <p><strong>البريد الإلكتروني:</strong> {user?.email || 'nurse@gula.iq'}</p>
          <p><strong>الدور:</strong> ممرض/ة</p>
        </div>
      </Card>

      <Card title="التفضيلات">
        <div className="space-y-4">
          <Select label="اللغة" value="ar" options={[{ value: 'ar', label: 'العربية' }, { value: 'en', label: 'English' }]} />
          <Select label="الوضع" value="light" options={[{ value: 'light', label: 'فاتح' }, { value: 'dark', label: 'داكن' }, { value: 'system', label: 'تلقائي' }]} />
          <Select label="الإشعارات" value="all" options={[{ value: 'all', label: 'جميع الإشعارات' }, { value: 'important', label: 'المهم فقط' }, { value: 'none', label: 'بدون إشعارات' }]} />
        </div>
      </Card>

      <Card title="حول التطبيق">
        <p className="text-sm text-gray-500">GULA National Health Platform</p>
        <p className="text-sm text-gray-500">Nurse App v2.1.0</p>
      </Card>

      <Button variant="danger" onClick={logout}>تسجيل الخروج</Button>
    </div>
  );
}
