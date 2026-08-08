import { Card, CardHeader, CardBody, Badge } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import type { LabResult } from '../services/clinical';

interface LabResultViewProps {
  results: LabResult[];
  title?: string;
}

const flagStyles: Record<string, { variant: 'success' | 'warning' | 'danger'; label: string; labelAr: string }> = {
  normal: { variant: 'success', label: 'Normal', labelAr: 'طبيعي' },
  high: { variant: 'warning', label: 'High', labelAr: 'مرتفع' },
  low: { variant: 'warning', label: 'Low', labelAr: 'منخفض' },
  critical_high: { variant: 'danger', label: 'Critical High', labelAr: 'مرتفع حرج' },
  critical_low: { variant: 'danger', label: 'Critical Low', labelAr: 'منخفض حرج' },
  abnormal: { variant: 'warning', label: 'Abnormal', labelAr: 'غير طبيعي' },
};

const categoryColors: Record<string, string> = {
  Hematology: 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400',
  Chemistry: 'bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400',
  Immunology: 'bg-purple-100 text-purple-700 dark:bg-purple-900/20 dark:text-purple-400',
  Microbiology: 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400',
  Endocrinology: 'bg-orange-100 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400',
  Toxicology: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400',
};

export function LabResultView({ results, title }: LabResultViewProps) {
  const { isRtl } = useRTL();
  const defaultTitle = isRtl ? 'نتائج المختبر' : 'Lab Results';

  const grouped = results.reduce<Record<string, LabResult[]>>((acc, r) => {
    const category = r.category || 'Other';
    if (!acc[category]) acc[category] = [];
    acc[category].push(r);
    return acc;
  }, {});

  return (
    <Card>
      <CardHeader title={title || defaultTitle} subtitle={`${results.length} ${isRtl ? 'نتيجة' : 'results'}`} />
      <CardBody>
        {results.length === 0 ? (
          <p className="text-sm text-neutral-500 text-center py-4">
            {isRtl ? 'لا توجد نتائج مختبر' : 'No lab results'}
          </p>
        ) : (
          <div className="space-y-4">
            {Object.entries(grouped).map(([category, categoryResults]) => (
              <div key={category}>
                <div className="flex items-center gap-2 mb-2">
                  <span className={`px-2 py-0.5 rounded-lg text-xs font-bold ${categoryColors[category] || 'bg-neutral-100 text-neutral-700'}`}>
                    {isRtl ? category : category}
                  </span>
                </div>
                <div className="divide-y divide-neutral-100 dark:divide-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl overflow-hidden">
                  {categoryResults.map(result => {
                    const flag = flagStyles[result.flag] || flagStyles.normal;
                    return (
                      <div key={result.id} className="p-3 hover:bg-neutral-50 dark:hover:bg-neutral-800/50">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm text-neutral-900 dark:text-neutral-50">
                              {isRtl ? result.testNameAr : result.testName}
                            </p>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className="text-sm font-bold">{result.result}</span>
                              <span className="text-xs text-neutral-400">{result.unit}</span>
                            </div>
                            <p className="text-xs text-neutral-500 mt-0.5">
                              {isRtl ? 'النطاق المرجعي' : 'Reference'}: {result.referenceRange}
                            </p>
                          </div>
                          <Badge variant={flag.variant} size="sm">
                            {isRtl ? flag.labelAr : flag.label}
                          </Badge>
                        </div>
                        {result.interpretation && (
                          <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1 italic">
                            {result.interpretation}
                          </p>
                        )}
                        <p className="text-[10px] text-neutral-400 mt-1">
                          {new Date(result.performedAt).toLocaleDateString(isRtl ? 'ar-IQ' : 'en-US')}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardBody>
    </Card>
  );
}
