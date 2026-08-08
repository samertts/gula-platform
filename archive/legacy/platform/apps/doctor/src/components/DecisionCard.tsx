import { Card, CardHeader, CardBody, Badge, Button } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import type { DecisionSupportResult, AiRecommendation, DifferentialDiagnosis } from '../services/decisionSupport';

interface DecisionCardProps {
  result: DecisionSupportResult;
  onExplain?: (recommendationId: string) => void;
  onApply?: (recommendationId: string) => void;
  onDismiss?: (recommendationId: string) => void;
}

const priorityColors: Record<string, 'danger' | 'warning' | 'info' | 'default'> = {
  critical: 'danger',
  high: 'warning',
  medium: 'info',
  low: 'default',
};

const categoryIcons: Record<string, string> = {
  diagnosis: '🔍',
  medication: '💊',
  test: '🔬',
  referral: '🔄',
  monitoring: '📊',
  lifestyle: '🏃',
};

export function DecisionCard({ result, onExplain, onApply, onDismiss }: DecisionCardProps) {
  const { isRtl } = useRTL();
  const criticalRecs = result.recommendations.filter(r => r.priority === 'critical' || r.priority === 'high');
  const otherRecs = result.recommendations.filter(r => r.priority !== 'critical' && r.priority !== 'high');

  return (
    <Card variant="elevated" className="border-r-4 border-primary-500">
      <CardHeader
        title={isRtl ? 'دعم القرار السريري' : 'Clinical Decision Support'}
        subtitle={
          <span className="flex items-center gap-2">
            <Badge variant={result.evidenceLevel === 'high' ? 'success' : result.evidenceLevel === 'moderate' ? 'warning' : 'default'} size="xs">
              {isRtl
                ? (result.evidenceLevel === 'high' ? 'عالٍ' : result.evidenceLevel === 'moderate' ? 'متوسط' : result.evidenceLevel === 'low' ? 'منخفض' : 'رأي خبير')
                : result.evidenceLevel.replace('_', ' ')}
            </Badge>
            <span className="text-xs text-neutral-400">{Math.round(result.confidence * 100)}% {isRtl ? 'ثقة' : 'confidence'}</span>
          </span>
        }
      />
      <CardBody>
        <div className="mb-4 p-3 rounded-xl bg-primary-50 dark:bg-primary-950 border border-primary-100 dark:border-primary-900">
          <p className="text-sm text-neutral-700 dark:text-neutral-300">
            {isRtl ? result.summaryAr : result.summary}
          </p>
        </div>

        {criticalRecs.length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-bold text-danger-600 dark:text-danger-400 mb-2 uppercase tracking-wider">
              {isRtl ? 'توصيات عاجلة' : 'Critical Recommendations'}
            </p>
            <div className="space-y-2">
              {criticalRecs.map(rec => (
                <RecommendationItem
                  key={rec.id}
                  recommendation={rec}
                  onExplain={onExplain}
                  onApply={onApply}
                  onDismiss={onDismiss}
                />
              ))}
            </div>
          </div>
        )}

        {otherRecs.length > 0 && (
          <div>
            <p className="text-xs font-bold text-neutral-500 dark:text-neutral-400 mb-2 uppercase tracking-wider">
              {isRtl ? 'توصيات أخرى' : 'Other Recommendations'}
            </p>
            <div className="space-y-2">
              {otherRecs.map(rec => (
                <RecommendationItem
                  key={rec.id}
                  recommendation={rec}
                  onExplain={onExplain}
                  onApply={onApply}
                  onDismiss={onDismiss}
                />
              ))}
            </div>
          </div>
        )}

        {result.differentialDiagnosis.length > 0 && (
          <div className="mt-4 pt-4 border-t border-neutral-100 dark:border-neutral-700">
            <p className="text-xs font-bold text-neutral-500 dark:text-neutral-400 mb-2 uppercase tracking-wider">
              {isRtl ? 'التشخيص التفريقي' : 'Differential Diagnosis'}
            </p>
            <div className="space-y-2">
              {result.differentialDiagnosis.map((dd, i) => (
                <DifferentialItem key={i} dd={dd} isRtl={isRtl} />
              ))}
            </div>
          </div>
        )}
      </CardBody>
    </Card>
  );
}

function RecommendationItem({
  recommendation,
  onExplain,
  onApply,
  onDismiss,
}: {
  recommendation: AiRecommendation;
  onExplain?: (id: string) => void;
  onApply?: (id: string) => void;
  onDismiss?: (id: string) => void;
}) {
  const isRtl = typeof document !== 'undefined' && document.documentElement.dir === 'rtl';

  return (
    <div className="p-3 rounded-xl bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700">
      <div className="flex items-start gap-2">
        <span className="text-lg">{categoryIcons[recommendation.category] || '📋'}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <p className="font-medium text-sm text-neutral-900 dark:text-neutral-50">
              {isRtl ? recommendation.titleAr : recommendation.title}
            </p>
            <Badge variant={priorityColors[recommendation.priority]} size="xs">
              {isRtl
                ? (recommendation.priority === 'critical' ? 'حرج' : recommendation.priority === 'high' ? 'عالي' : recommendation.priority === 'medium' ? 'متوسط' : 'منخفض')
                : recommendation.priority}
            </Badge>
          </div>
          <p className="text-xs text-neutral-600 dark:text-neutral-400">
            {isRtl ? recommendation.descriptionAr : recommendation.description}
          </p>
          {recommendation.evidence && (
            <p className="text-[10px] text-neutral-500 dark:text-neutral-500 mt-1 italic">
              {isRtl ? recommendation.evidenceAr : recommendation.evidence}
            </p>
          )}
          <div className="flex gap-2 mt-2">
            {onExplain && (
              <button onClick={() => onExplain(recommendation.id)} className="text-xs text-primary-600 dark:text-primary-400 hover:underline">
                {isRtl ? 'شرح' : 'Explain'}
              </button>
            )}
            {onApply && (
              <button onClick={() => onApply(recommendation.id)} className="text-xs text-success-600 dark:text-success-400 hover:underline">
                {isRtl ? 'تطبيق' : 'Apply'}
              </button>
            )}
            {onDismiss && (
              <button onClick={() => onDismiss(recommendation.id)} className="text-xs text-neutral-500 hover:text-neutral-700 hover:underline">
                {isRtl ? 'تجاهل' : 'Dismiss'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function DifferentialItem({ dd, isRtl }: { dd: DifferentialDiagnosis; isRtl: boolean }) {
  const barWidth = `${Math.round(dd.probability * 100)}%`;
  return (
    <div className="p-3 rounded-xl bg-neutral-50 dark:bg-neutral-900">
      <div className="flex items-center justify-between mb-1">
        <p className="text-sm font-medium text-neutral-900 dark:text-neutral-50">
          {isRtl ? dd.conditionAr : dd.condition}
        </p>
        <span className="text-xs text-neutral-500">{Math.round(dd.probability * 100)}%</span>
      </div>
      <div className="w-full h-1.5 rounded-full bg-neutral-200 dark:bg-neutral-700 overflow-hidden">
        <div className="h-full rounded-full bg-primary-500 transition-all" style={{ width: barWidth }} />
      </div>
    </div>
  );
}
