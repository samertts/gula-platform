import { useState } from 'react';
import {
  Card, CardHeader, CardBody, Input, Button, Select, LayoutContent, useRTL,
} from '@gula/ui-platform';
import { useAuth } from '../contexts/AuthContext';

export function Settings() {
  const { isRtl, toggleDirection } = useRTL();
  const { user } = useAuth();
  const [language, setLanguage] = useState<'ar' | 'en'>(isRtl ? 'ar' : 'en');
  const [notifications, setNotifications] = useState({
    admissions: true,
    discharges: true,
    bedAlerts: true,
    maintenanceAlerts: true,
    financialReports: false,
    hrAlerts: true,
  });

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
            {isRtl ? 'الإعدادات' : 'Settings'}
          </h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            {isRtl ? 'إعدادات نظام إدارة المستشفى' : 'Hospital management system settings'}
          </p>
        </div>

        <Card>
          <CardHeader title={isRtl ? 'الملف الشخصي' : 'Profile'} />
          <CardBody>
            <div className="flex items-center gap-4 mb-4">
              <div className="w-16 h-16 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-600 dark:text-primary-400 text-xl font-bold">
                {user?.nameAr?.charAt(0) || 'م'}
              </div>
              <div>
                <p className="font-bold text-lg text-neutral-900 dark:text-neutral-50">{user?.nameAr || user?.name}</p>
                <p className="text-sm text-neutral-500">{user?.titleAr || user?.title}</p>
                <p className="text-xs text-neutral-400">{user?.departmentAr || user?.department}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs text-neutral-500">{isRtl ? 'البريد الإلكتروني' : 'Email'}</p>
                <p className="text-sm font-medium text-neutral-700 dark:text-neutral-300">{user?.email}</p>
              </div>
              <div>
                <p className="text-xs text-neutral-500">{isRtl ? 'الصلاحيات' : 'Role'}</p>
                <p className="text-sm font-medium text-neutral-700 dark:text-neutral-300">{user?.role}</p>
              </div>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title={isRtl ? 'التفضيلات' : 'Preferences'} />
          <CardBody>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-neutral-700 dark:text-neutral-300">{isRtl ? 'اللغة' : 'Language'}</p>
                  <p className="text-xs text-neutral-500">{isRtl ? 'لغة الواجهة' : 'Interface language'}</p>
                </div>
                <Select
                  value={language}
                  onChange={(v) => {
                    setLanguage(v as 'ar' | 'en');
                    if ((v === 'ar') !== isRtl) toggleDirection();
                  }}
                  options={[
                    { value: 'ar', label: 'العربية' },
                    { value: 'en', label: 'English' },
                  ]}
                  className="w-32"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-neutral-700 dark:text-neutral-300">{isRtl ? 'السمات' : 'Theme'}</p>
                  <p className="text-xs text-neutral-500">{isRtl ? 'وضع العرض' : 'Display mode'}</p>
                </div>
                <Button variant="outline" size="sm">
                  {isRtl ? 'فاتح / داكن' : 'Light / Dark'}
                </Button>
              </div>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title={isRtl ? 'الإشعارات' : 'Notifications'} />
          <CardBody>
            <div className="space-y-3">
              {[
                { key: 'admissions', labelAr: 'الاستقبالات الجديدة', labelEn: 'New Admissions' },
                { key: 'discharges', labelAr: 'التخريج', labelEn: 'Discharges' },
                { key: 'bedAlerts', labelAr: 'تنبيهات الأسرة', labelEn: 'Bed Alerts' },
                { key: 'maintenanceAlerts', labelAr: 'تنبيهات الصيانة', labelEn: 'Maintenance Alerts' },
                { key: 'financialReports', labelAr: 'التقارير المالية', labelEn: 'Financial Reports' },
                { key: 'hrAlerts', labelAr: 'تنبيهات الموظفين', labelEn: 'HR Alerts' },
              ].map(item => (
                <div key={item.key} className="flex items-center justify-between">
                  <span className="text-sm text-neutral-700 dark:text-neutral-300">
                    {isRtl ? item.labelAr : item.labelEn}
                  </span>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={(notifications as any)[item.key]}
                      onChange={() => setNotifications(prev => ({ ...prev, [item.key]: !(prev as any)[item.key] }))}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-neutral-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-neutral-700 peer-checked:after:translate-x-full peer-checked:after:rtl:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-neutral-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-neutral-600 peer-checked:bg-primary-600" />
                  </label>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title={isRtl ? 'حول النظام' : 'About'} />
          <CardBody>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-neutral-500">{isRtl ? 'النظام' : 'System'}</span>
                <span className="text-neutral-700 dark:text-neutral-300">GULA Hospital</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-500">{isRtl ? 'الإصدار' : 'Version'}</span>
                <span className="text-neutral-700 dark:text-neutral-300">2.1.0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-500">{isRtl ? 'المنصة' : 'Platform'}</span>
                <span className="text-neutral-700 dark:text-neutral-300">GULA Health Platform</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-500">{isRtl ? 'المرحلة' : 'Phase'}</span>
                <span className="text-neutral-700 dark:text-neutral-300">PI-003 Phase 7 (Hospital Administration)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-500">{isRtl ? 'المستشفى' : 'Hospital'}</span>
                <span className="text-neutral-700 dark:text-neutral-300">{isRtl ? 'مستشفى GULA الوطني' : 'GULA National Hospital'}</span>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>
    </LayoutContent>
  );
}
