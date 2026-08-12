import { useState } from 'react';
import { Button, Card, CardBody, EmptyState, Input, LoadingSpinner } from '@gula/ui-platform';
import { CarePlanCard } from '../components/CarePlanCard';
import { getPatientCarePlans } from '../services/carePlans';
import type { CarePlan as Plan } from '../utils/types';

export default function CarePlan() {
  const [patientId, setPatientId] = useState('');
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPlans = async () => {
    const normalizedPatientId = patientId.trim();
    if (!normalizedPatientId || loading) return;
    setLoading(true);
    setError(null);
    try {
      setPlans(await getPatientCarePlans(normalizedPatientId));
    } catch (cause) {
      setPlans([]);
      setError(cause instanceof Error ? cause.message : 'تعذر تحميل خطط الرعاية من الخادم');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div>
        <h1 className="text-2xl font-bold">خطط الرعاية التمريضية</h1>
        <p className="text-gray-500">عرض خطط الرعاية المعتمدة من السجل الصحي للمريض المحدد</p>
      </div>

      <Card>
        <CardBody>
          <div className="flex flex-col sm:flex-row items-end gap-3">
            <div className="flex-1 w-full">
              <Input
                label="معرّف المريض المعتمد"
                value={patientId}
                onChange={(event) => setPatientId(event.target.value)}
                placeholder="أدخل معرّف المريض من السجل الصحي"
                onKeyDown={(event) => {
                  if (event.key === 'Enter') void loadPlans();
                }}
              />
            </div>
            <Button variant="primary" onClick={() => void loadPlans()} loading={loading} disabled={!patientId.trim()}>
              تحميل الخطط
            </Button>
          </div>
        </CardBody>
      </Card>

      {error && (
        <div className="rounded-xl border border-danger-200 bg-danger-50 p-4 text-sm text-danger-700" role="alert">
          <div className="flex items-center justify-between gap-3">
            <span>{error}</span>
            <Button variant="outline" size="sm" onClick={() => void loadPlans()} disabled={loading || !patientId.trim()}>
              إعادة المحاولة
            </Button>
          </div>
        </div>
      )}

      {loading ? (
        <LoadingSpinner />
      ) : plans.length === 0 ? (
        <EmptyState
          title="لا توجد خطط معروضة"
          description={patientId.trim() ? 'لم يُعد Backend خطط رعاية لهذا المريض.' : 'أدخل معرّف مريض مصادقاً لتحميل خطط الرعاية.'}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {plans.map((plan) => <CarePlanCard key={plan.id} plan={plan} />)}
        </div>
      )}
    </div>
  );
}
