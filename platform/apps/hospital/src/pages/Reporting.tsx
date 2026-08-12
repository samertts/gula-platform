import { useState } from 'react';
import {
  Card, CardHeader, CardBody, Badge, Select, LayoutContent, useRTL,
} from '@gula/ui-platform';

interface ReportMetric {
  label?: string;
  labelAr: string;
  value: string | number;
  change: number;
  trend: 'up' | 'down' | 'stable';
}

interface ReportSection {
  title: string;
  titleAr: string;
  metrics: ReportMetric[];
}

const MOCK_SECTIONS: ReportSection[] = [
  {
    title: 'المؤشرات السريرية', titleAr: 'المؤشرات السريرية',
    metrics: [
      { labelAr: 'متوسط مدة الإقامة (أيام)', value: 4.2, change: -0.3, trend: 'down' },
      { labelAr: 'معدل إعادة الدخول (30 يوماً)', value: '8.5%', change: -1.2, trend: 'down' },
      { labelAr: 'معدل الوفيات', value: '1.8%', change: -0.2, trend: 'down' },
      { labelAr: 'معدل العدوى المكتسبة', value: '3.2%', change: 0.4, trend: 'up' },
      { labelAr: 'العمليات الجراحية', value: 187, change: 12, trend: 'up' },
    ],
  },
  {
    title: 'مؤشرات الموارد', titleAr: 'مؤشرات الموارد',
    metrics: [
      { labelAr: 'نسبة إشغال الأسرة', value: '78.5%', change: 2.1, trend: 'up' },
      { labelAr: 'معدل دوران الأسرة', value: 3.8, change: 0.5, trend: 'up' },
      { labelAr: 'معدل استخدام غرف العمليات', value: '72%', change: -5, trend: 'down' },
      { labelAr: 'مخزون الأدوية (أيام)', value: 24, change: -3, trend: 'down' },
    ],
  },
  {
    title: 'مؤشرات مالية', titleAr: 'مؤشرات مالية',
    metrics: [
      { labelAr: 'الإيرادات الشهرية', value: '$3.25M', change: 150000, trend: 'up' },
      { labelAr: 'المصروفات الشهرية', value: '$2.78M', change: 82000, trend: 'up' },
      { labelAr: 'صافي الدخل', value: '$470K', change: 68000, trend: 'up' },
      { labelAr: 'تكلفة السرير اليومي', value: '$185', change: 12, trend: 'up' },
    ],
  },
  {
    title: 'مؤشرات الموظفين', titleAr: 'مؤشرات الموظفين',
    metrics: [
      { labelAr: 'نسبة الممرضين لكل سرير', value: '1.2:1', change: 0.05, trend: 'up' },
      { labelAr: 'معدل الغياب', value: '4.5%', change: -0.3, trend: 'down' },
      { labelAr: 'ساعات التدريب لكل موظف', value: 18, change: 3, trend: 'up' },
    ],
  },
];

export function Reporting() {
  const { isRtl } = useRTL();
  const [period, setPeriod] = useState('monthly');
  const [selectedReport, setSelectedReport] = useState('clinical');

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
              {isRtl ? 'التقارير والتحليلات' : 'Reports & Analytics'}
            </h1>
            <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
              {isRtl ? 'تقارير أداء المستشفى الشاملة' : 'Comprehensive hospital performance reports'}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Select
              value={selectedReport}
              onChange={e => setSelectedReport(e.target.value)}
              options={[
                { value: 'clinical', label: isRtl ? 'سريري' : 'Clinical' },
                { value: 'operational', label: isRtl ? 'تشغيلي' : 'Operational' },
                { value: 'financial', label: isRtl ? 'مالي' : 'Financial' },
                { value: 'quality', label: isRtl ? 'الجودة' : 'Quality' },
              ]}
              className="w-32"
            />
            <Select
              value={period}
              onChange={e => setPeriod(e.target.value)}
              options={[
                { value: 'daily', label: isRtl ? 'يومي' : 'Daily' },
                { value: 'weekly', label: isRtl ? 'أسبوعي' : 'Weekly' },
                { value: 'monthly', label: isRtl ? 'شهري' : 'Monthly' },
                { value: 'quarterly', label: isRtl ? 'ربع سنوي' : 'Quarterly' },
                { value: 'annual', label: isRtl ? 'سنوي' : 'Annual' },
              ]}
              className="w-32"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[{ value: '78.5%', label: 'نسبة الإشغال', labelEn: 'Occupancy Rate', color: 'bg-blue-500' },
            { value: '4.2', label: 'متوسط الإقامة', labelEn: 'Avg Stay (days)', color: 'bg-green-500' },
            { value: '187', label: 'العمليات الجراحية', labelEn: 'Surgeries', color: 'bg-purple-500' },
            { value: '8.5%', label: 'معدل إعادة الدخول', labelEn: 'Readmission Rate', color: 'bg-orange-500' },
          ].map(s => (
            <Card key={s.label} variant="elevated" padding="md">
              <CardBody>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs text-neutral-500">{isRtl ? s.label : s.labelEn}</p>
                    <p className="text-2xl font-bold mt-1 text-neutral-900 dark:text-neutral-50">{s.value}</p>
                  </div>
                  <div className={`w-2 h-8 rounded-full ${s.color}`} />
                </div>
              </CardBody>
            </Card>
          ))}
        </div>

        {MOCK_SECTIONS.map(section => (
          <Card key={section.title}>
            <CardHeader title={isRtl ? section.titleAr : section.title} />
            <CardBody>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
                {section.metrics.map(m => (
                  <div key={m.labelAr} className="bg-neutral-50 dark:bg-neutral-800/50 rounded-lg p-4">
                    <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-1">
                      {isRtl ? m.labelAr : (m.label ?? m.labelAr)}
                    </p>
                    <p className="text-lg font-bold text-neutral-900 dark:text-neutral-50">{m.value}</p>
                    <div className="flex items-center gap-1 mt-1">
                      <span className={`text-xs font-medium ${
                        m.trend === 'up' ? 'text-green-600' : m.trend === 'down' ? 'text-red-600' : 'text-neutral-400'
                      }`}>
                        {m.change > 0 ? '+' : ''}{m.change}
                        {typeof m.change === 'number' && typeof m.value === 'string' && m.value.includes('%') ? '%' : ''}
                      </span>
                      <span className="text-xs text-neutral-400">
                        {m.trend === 'up' ? (isRtl ? '↑' : '↑') : m.trend === 'down' ? (isRtl ? '↓' : '↓') : '→'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        ))}
      </div>
    </LayoutContent>
  );
}
