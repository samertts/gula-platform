import { useState, useEffect } from 'react';
import {
  Card, CardHeader, CardBody, Badge, LayoutContent, useRTL,
} from '@gula/ui-platform';
import { useAuth } from '../contexts/AuthContext';
import { OccupancyGrid } from '../components/OccupancyGrid';

interface StatCard {
  label: string;
  labelAr: string;
  value: string | number;
  change: number;
  changeLabel: string;
  changeLabelAr: string;
  color: 'primary' | 'success' | 'warning' | 'danger' | 'info';
  icon: string;
}

const MOCK_STATS: StatCard[] = [
  { label: 'الأسرة المشغولة', labelAr: 'الأسرة المشغولة', value: 142, change: 5, changeLabel: 'عن الأمس', changeLabelAr: 'عن الأمس', color: 'danger', icon: '🛏️' },
  { label: 'الأسرة المتاحة', labelAr: 'الأسرة المتاحة', value: 58, change: -3, changeLabel: 'عن الأمس', changeLabelAr: 'عن الأمس', color: 'success', icon: '✅' },
  { label: 'المرضى اليوم', labelAr: 'المرضى اليوم', value: 24, change: 2, changeLabel: 'عن الأمس', changeLabelAr: 'عن الأمس', color: 'primary', icon: '👤' },
  { label: 'التخريج اليوم', labelAr: 'التخريج اليوم', value: 18, change: 4, changeLabel: 'عن الأمس', changeLabelAr: 'عن الأمس', color: 'info', icon: '🚪' },
  { label: 'عمليات اليوم', labelAr: 'عمليات اليوم', value: 7, change: 0, changeLabel: 'عن الأمس', changeLabelAr: 'عن الأمس', color: 'warning', icon: '🔬' },
  { label: 'حالات الطوارئ', labelAr: 'حالات الطوارئ', value: 9, change: -2, changeLabel: 'عن الأمس', changeLabelAr: 'عن الأمس', color: 'danger', icon: '🚨' },
];

const MOCK_DEPARTMENT_STATUS = [
  { name: 'الطوارئ', nameAr: 'الطوارئ', total: 30, occupied: 26, available: 4, admissions: 8, color: 'bg-red-500' },
  { name: 'الباطنية', nameAr: 'الباطنية', total: 40, occupied: 35, available: 5, admissions: 6, color: 'bg-blue-500' },
  { name: 'الجراحة', nameAr: 'الجراحة', total: 35, occupied: 28, available: 7, admissions: 4, color: 'bg-green-500' },
  { name: 'طب الأطفال', nameAr: 'طب الأطفال', total: 20, occupied: 15, available: 5, admissions: 3, color: 'bg-yellow-500' },
  { name: 'العناية المركزة', nameAr: 'العناية المركزة', total: 15, occupied: 14, available: 1, admissions: 2, color: 'bg-purple-500' },
  { name: 'النسائية والتوليد', nameAr: 'النسائية والتوليد', total: 25, occupied: 18, available: 7, admissions: 5, color: 'bg-pink-500' },
  { name: 'العظام', nameAr: 'العظام', total: 20, occupied: 16, available: 4, admissions: 3, color: 'bg-indigo-500' },
  { name: 'الأمراض النفسية', nameAr: 'الأمراض النفسية', total: 15, occupied: 10, available: 5, admissions: 1, color: 'bg-teal-500' },
];

const MOCK_ALERTS = [
  { id: 'a1', type: 'critical' as const, message: 'العناية المركزة: 14 من 15 سريراً مشغولة', time: 'منذ 5 دقائق' },
  { id: 'a2', type: 'warning' as const, message: 'نقص في مخزون المضادات الحيوية - قسم الطوارئ', time: 'منذ 15 دقيقة' },
  { id: 'a3', type: 'info' as const, message: 'جدول صيانة جهاز التصوير المقطعي غداً', time: 'منذ ساعة' },
];

export function Dashboard() {
  const { isRtl } = useRTL();
  const { user } = useAuth();
  const [dateStr, setDateStr] = useState('');

  useEffect(() => {
    setDateStr(new Date().toLocaleDateString(isRtl ? 'ar-IQ' : 'en-US', {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
    }));
  }, [isRtl]);

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
              {isRtl ? `مرحباً، ${user?.nameAr || 'المدير'}` : `Welcome, ${user?.name || 'Admin'}`}
            </h1>
            <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">{dateStr}</p>
          </div>
          <Badge variant="primary" size="lg">
            {isRtl ? 'نسبة الإشغال' : 'Occupancy'}: {Math.round((142 / 200) * 100)}%
          </Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {MOCK_STATS.map(stat => (
            <Card key={stat.label} variant="elevated" padding="md">
              <CardBody>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs text-neutral-500 dark:text-neutral-400">{isRtl ? stat.labelAr : stat.label}</p>
                    <p className="text-2xl font-bold mt-1 text-neutral-900 dark:text-neutral-50">{stat.value}</p>
                  </div>
                  <span className="text-xl">{stat.icon}</span>
                </div>
                <div className="flex items-center gap-1 mt-2">
                  <span className={`text-xs font-medium ${stat.change >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                    {stat.change >= 0 ? '+' : ''}{stat.change}
                  </span>
                  <span className="text-xs text-neutral-400">{isRtl ? stat.changeLabelAr : stat.changeLabel}</span>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card>
              <CardHeader
                title={isRtl ? 'إشغال الأقسام' : 'Department Occupancy'}
                action={
                  <button className="text-sm text-primary-600 dark:text-primary-400 hover:underline">
                    {isRtl ? 'عرض الكل' : 'View All'}
                  </button>
                }
              />
              <CardBody>
                <div className="space-y-3">
                  {MOCK_DEPARTMENT_STATUS.map(dept => {
                    const pct = Math.round((dept.occupied / dept.total) * 100);
                    return (
                      <div key={dept.name} className="flex items-center gap-4">
                        <div className="w-28 shrink-0">
                          <p className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                            {isRtl ? dept.nameAr : dept.name}
                          </p>
                          <p className="text-xs text-neutral-400">{dept.occupied}/{dept.total}</p>
                        </div>
                        <div className="flex-1 h-3 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${dept.color}`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <span className="text-xs font-medium text-neutral-500 w-10 text-left">{pct}%</span>
                        <span className="text-xs text-green-600 dark:text-green-400 w-8 text-left">
                          +{dept.admissions}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </CardBody>
            </Card>
          </div>

          <div className="space-y-4">
            <Card>
              <CardHeader title={isRtl ? 'التنبيهات' : 'Alerts'} />
              <CardBody>
                <div className="space-y-3">
                  {MOCK_ALERTS.map(alert => (
                    <div key={alert.id} className="flex items-start gap-3 p-2 rounded-lg bg-neutral-50 dark:bg-neutral-800/50">
                      <span className={`w-2 h-2 mt-1.5 rounded-full shrink-0 ${
                        alert.type === 'critical' ? 'bg-red-500' :
                        alert.type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
                      }`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-neutral-700 dark:text-neutral-300">{alert.message}</p>
                        <p className="text-xs text-neutral-400 mt-0.5">{alert.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardBody>
            </Card>

            <Card>
              <CardHeader title={isRtl ? 'نظرة سريعة' : 'Quick Overview'} />
              <CardBody>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                    <p className="text-blue-600 dark:text-blue-400 font-bold text-lg">12</p>
                    <p className="text-blue-700 dark:text-blue-300 text-xs">{isRtl ? 'بانتظار الكشف' : 'Waiting Triage'}</p>
                  </div>
                  <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                    <p className="text-green-600 dark:text-green-400 font-bold text-lg">8</p>
                    <p className="text-green-700 dark:text-green-300 text-xs">{isRtl ? 'غرف العمليات' : 'OT Scheduled'}</p>
                  </div>
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded-lg">
                    <p className="text-yellow-600 dark:text-yellow-400 font-bold text-lg">4</p>
                    <p className="text-yellow-700 dark:text-yellow-300 text-xs">{isRtl ? 'صيانة حرجة' : 'Critical Maint.'}</p>
                  </div>
                  <div className="bg-purple-50 dark:bg-purple-900/20 p-3 rounded-lg">
                    <p className="text-purple-600 dark:text-purple-400 font-bold text-lg">23</p>
                    <p className="text-purple-700 dark:text-purple-300 text-xs">{isRtl ? 'موظفون حاضرون' : 'On Duty Staff'}</p>
                  </div>
                </div>
              </CardBody>
            </Card>
          </div>
        </div>
      </div>
    </LayoutContent>
  );
}
