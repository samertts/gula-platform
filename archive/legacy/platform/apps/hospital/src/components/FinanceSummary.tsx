import { Card, CardBody, useRTL } from '@gula/ui-platform';

interface FinanceSummaryProps {
  totalRevenue: number;
  totalExpenses: number;
  netIncome: number;
  period: string;
}

export function FinanceSummary({ totalRevenue, totalExpenses, netIncome }: FinanceSummaryProps) {
  const { isRtl } = useRTL();
  const marginPct = totalRevenue > 0 ? ((netIncome / totalRevenue) * 100).toFixed(1) : '0.0';

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card variant="elevated" padding="lg" className="border-r-4 border-green-500">
        <CardBody>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
            {isRtl ? 'إجمالي الإيرادات' : 'Total Revenue'}
          </p>
          <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">
            ${(totalRevenue / 1000).toFixed(0)}K
          </p>
          <p className="text-xs text-neutral-400 mt-1">
            {isRtl ? 'الإيرادات الإجمالية للفترة' : 'Gross revenue for period'}
          </p>
        </CardBody>
      </Card>

      <Card variant="elevated" padding="lg" className="border-r-4 border-red-500">
        <CardBody>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
            {isRtl ? 'إجمالي المصروفات' : 'Total Expenses'}
          </p>
          <p className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">
            ${(totalExpenses / 1000).toFixed(0)}K
          </p>
          <p className="text-xs text-neutral-400 mt-1">
            {isRtl ? 'المصروفات التشغيلية للفترة' : 'Operating expenses for period'}
          </p>
        </CardBody>
      </Card>

      <Card variant="elevated" padding="lg" className={`border-r-4 ${netIncome >= 0 ? 'border-blue-500' : 'border-red-600'}`}>
        <CardBody>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
            {isRtl ? 'صافي الدخل' : 'Net Income'}
          </p>
          <p className={`text-2xl font-bold mt-1 ${netIncome >= 0 ? 'text-blue-600 dark:text-blue-400' : 'text-red-600 dark:text-red-400'}`}>
            ${(Math.abs(netIncome) / 1000).toFixed(0)}K
            {netIncome < 0 ? ` ${isRtl ? '(خسارة)' : '(Loss)'}` : ''}
          </p>
          <p className="text-xs text-neutral-400 mt-1">
            {isRtl ? 'صافي الربح التشغيلي' : 'Net operating profit'}
          </p>
        </CardBody>
      </Card>

      <Card variant="elevated" padding="lg" className="border-r-4 border-purple-500">
        <CardBody>
          <p className="text-xs text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
            {isRtl ? 'هامش الربح' : 'Profit Margin'}
          </p>
          <p className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1">
            {marginPct}%
          </p>
          <p className="text-xs text-neutral-400 mt-1">
            {isRtl ? 'نسبة الربح إلى الإيرادات' : 'Profit to revenue ratio'}
          </p>
        </CardBody>
      </Card>
    </div>
  );
}
