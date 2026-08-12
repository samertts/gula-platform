import { useState } from 'react';
import {
  Card, CardHeader, CardBody, Badge, Select, LayoutContent, useRTL,
} from '@gula/ui-platform';
import { FinanceSummary } from '../components/FinanceSummary';

const MOCK_REVENUE_DATA = [
  { month: 'يناير', monthEn: 'Jan', revenue: 425000, expenses: 380000, net: 45000 },
  { month: 'فبراير', monthEn: 'Feb', revenue: 450000, expenses: 395000, net: 55000 },
  { month: 'مارس', monthEn: 'Mar', revenue: 470000, expenses: 410000, net: 60000 },
  { month: 'أبريل', monthEn: 'Apr', revenue: 445000, expenses: 400000, net: 45000 },
  { month: 'مايو', monthEn: 'May', revenue: 480000, expenses: 420000, net: 60000 },
  { month: 'يونيو', monthEn: 'Jun', revenue: 510000, expenses: 435000, net: 75000 },
  { month: 'يوليو', monthEn: 'Jul', revenue: 495000, expenses: 430000, net: 65000 },
];

const MOCK_REVENUE_BREAKDOWN = [
  { categoryAr: 'خدمات المرضى الداخليين', amount: 1250000, percentage: 42 },
  { categoryAr: 'خدمات العيادات الخارجية', amount: 680000, percentage: 23 },
  { categoryAr: 'خدمات الطوارئ', amount: 420000, percentage: 14 },
  { categoryAr: 'المختبر', amount: 310000, percentage: 10 },
  { categoryAr: 'الصيدلية', amount: 220000, percentage: 7 },
  { categoryAr: 'خدمات أخرى', amount: 120000, percentage: 4 },
];

const MOCK_EXPENSE_BREAKDOWN = [
  { categoryAr: 'الرواتب والأجور', amount: 980000, percentage: 38 },
  { categoryAr: 'الأدوية والمستلزمات', amount: 520000, percentage: 20 },
  { categoryAr: 'الصيانة والتشغيل', amount: 280000, percentage: 11 },
  { categoryAr: 'المعدات الطبية', amount: 350000, percentage: 14 },
  { categoryAr: 'الخدمات العامة', amount: 180000, percentage: 7 },
  { categoryAr: 'مصاريف إدارية', amount: 145000, percentage: 6 },
  { categoryAr: 'أخرى', amount: 105000, percentage: 4 },
];

export function Finance() {
  const { isRtl } = useRTL();
  const [period, setPeriod] = useState('monthly');

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
              {isRtl ? 'الإدارة المالية' : 'Financial Management'}
            </h1>
            <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
              {isRtl ? 'لوحة المؤشرات المالية للمستشفى' : 'Hospital financial dashboard'}
            </p>
          </div>
          <Select
            value={period}
            onChange={e => setPeriod(e.target.value)}
            options={[
              { value: 'daily', label: isRtl ? 'يومي' : 'Daily' },
              { value: 'weekly', label: isRtl ? 'أسبوعي' : 'Weekly' },
              { value: 'monthly', label: isRtl ? 'شهري' : 'Monthly' },
              { value: 'annual', label: isRtl ? 'سنوي' : 'Annual' },
            ]}
            className="w-32"
          />
        </div>

        <FinanceSummary
          totalRevenue={3250000}
          totalExpenses={2780000}
          netIncome={470000}
          period={period}
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader title={isRtl ? 'الإيرادات الشهرية' : 'Monthly Revenue Trend'} />
            <CardBody>
              <div className="space-y-2">
                {MOCK_REVENUE_DATA.map(row => (
                  <div key={row.month} className="flex items-center gap-4">
                    <span className="w-16 text-sm text-neutral-500">{isRtl ? row.month : row.monthEn}</span>
                    <div className="flex-1 h-6 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden relative">
                      <div className="absolute inset-0 flex">
                        <div
                          className="h-full bg-green-500 rounded-r-full"
                          style={{ width: `${(row.revenue / 510000) * 100}%` }}
                        />
                      </div>
                    </div>
                    <span className="text-sm font-medium w-24 text-left text-neutral-700 dark:text-neutral-300">
                      ${(row.revenue / 1000).toFixed(0)}K
                    </span>
                    <span className={`text-xs font-medium w-16 text-left ${
                      row.net >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {row.net >= 0 ? '+' : ''}${(row.net / 1000).toFixed(0)}K
                    </span>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>

          <div className="space-y-6">
            <Card>
              <CardHeader title={isRtl ? 'توزيع الإيرادات' : 'Revenue Breakdown'} />
              <CardBody>
                <div className="space-y-3">
                  {MOCK_REVENUE_BREAKDOWN.map(item => (
                    <div key={item.categoryAr} className="flex items-center gap-3">
                      <span className="text-sm flex-1">{isRtl ? item.categoryAr : item.categoryAr}</span>
                      <div className="w-32 h-2 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
                        <div className="h-full bg-primary-500 rounded-full" style={{ width: `${item.percentage}%` }} />
                      </div>
                      <span className="text-xs font-medium text-neutral-500 w-16 text-left">{item.percentage}%</span>
                    </div>
                  ))}
                </div>
              </CardBody>
            </Card>

            <Card>
              <CardHeader title={isRtl ? 'توزيع المصروفات' : 'Expense Breakdown'} />
              <CardBody>
                <div className="space-y-3">
                  {MOCK_EXPENSE_BREAKDOWN.map(item => (
                    <div key={item.categoryAr} className="flex items-center gap-3">
                      <span className="text-sm flex-1">{isRtl ? item.categoryAr : item.categoryAr}</span>
                      <div className="w-32 h-2 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
                        <div className="h-full bg-red-500 rounded-full" style={{ width: `${item.percentage}%` }} />
                      </div>
                      <span className="text-xs font-medium text-neutral-500 w-16 text-left">{item.percentage}%</span>
                    </div>
                  ))}
                </div>
              </CardBody>
            </Card>
          </div>
        </div>
      </div>
    </LayoutContent>
  );
}
