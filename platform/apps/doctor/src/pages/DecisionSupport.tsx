import { useState } from 'react';
import { Card, CardHeader, CardBody, Input, Button, Badge, LayoutContent, Tabs } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import { DecisionCard } from '../components/DecisionCard';
import { queryDecisionSupport, type DecisionSupportResult } from '../services/decisionSupport';

export function DecisionSupport() {
  const { isRtl } = useRTL();
  const [patientId, setPatientId] = useState('');
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<DecisionSupportResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<DecisionSupportResult[]>([]);
  const [activeTab, setActiveTab] = useState('query');

  const handleQuery = async () => {
    if (!patientId.trim() || !query.trim() || isLoading) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await queryDecisionSupport({
        patientId: patientId.trim(),
        query: query.trim(),
      });
      setResult(response);
      setHistory((previous) => [response, ...previous]);
    } catch (cause) {
      setResult(null);
      setError(cause instanceof Error ? cause.message : (isRtl ? 'تعذر الوصول إلى خدمة دعم القرار.' : 'Clinical decision support is unavailable.'));
    } finally {
      setIsLoading(false);
    }
  };

  const tabs = [
    { id: 'query', label: isRtl ? 'استعلام' : 'Query' },
    { id: 'history', label: isRtl ? 'السجل' : 'History' },
  ];

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
            {isRtl ? 'دعم القرار السريري' : 'Clinical Decision Support'}
          </h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            {isRtl ? 'مدعوم بالذكاء الاصطناعي مع توصيات مبنية على الأدلة' : 'AI-powered with evidence-based recommendations'}
          </p>
        </div>

        <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

        {activeTab === 'query' && (
          <>
            <Card>
              <CardHeader title={isRtl ? 'استعلام سريري' : 'Clinical Query'} />
              <CardBody>
                <div className="space-y-4">
                  <Input
                    label={isRtl ? 'معرّف المريض المعتمد' : 'Verified patient ID'}
                    value={patientId}
                    onChange={e => setPatientId(e.target.value)}
                    placeholder={isRtl ? 'أدخل معرّف المريض من السجل المعتمد' : 'Enter the verified patient identifier'}
                  />
                  <Input
                    label={isRtl ? 'الاستعلام السريري' : 'Clinical query'}
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    placeholder={isRtl
                      ? 'اكتب الاستعلام السريري... مثال: ألم صدر مع ضيق تنفس لدى مريض سكري عمر 65 سنة'
                      : 'Enter clinical query... e.g., Chest pain with SOB in a 65-year-old diabetic'}
                  />
                  <Button variant="primary" onClick={handleQuery} loading={isLoading} disabled={!patientId.trim() || !query.trim()}>
                    {isRtl ? 'تحليل' : 'Analyze'}
                  </Button>
                </div>
              </CardBody>
            </Card>

            {error && (
              <div className="rounded-xl border border-danger-200 bg-danger-50 p-4 text-sm text-danger-700 dark:border-danger-800 dark:bg-danger-900/20 dark:text-danger-300" role="alert">
                <div className="flex items-center justify-between gap-3">
                  <span>{error}</span>
                  <Button variant="outline" onClick={() => void handleQuery()} disabled={isLoading || !patientId.trim() || !query.trim()}>
                    {isRtl ? 'إعادة المحاولة' : 'Retry'}
                  </Button>
                </div>
              </div>
            )}

            {isLoading && (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                  <p className="text-sm text-neutral-500">{isRtl ? 'جاري تحليل البيانات السريرية...' : 'Analyzing clinical data...'}</p>
                </div>
              </div>
            )}

            {result && !isLoading && (
              <DecisionCard result={result} />
            )}
          </>
        )}

        {activeTab === 'history' && (
          <div className="space-y-4">
            {history.length === 0 ? (
              <Card>
                <CardBody>
                  <p className="text-sm text-neutral-500 text-center py-8">
                    {isRtl ? 'لا يوجد سجل استعلامات' : 'No query history'}
                  </p>
                </CardBody>
              </Card>
            ) : (
              history.map(h => (
                <DecisionCard key={h.id} result={h} />
              ))
            )}
          </div>
        )}
      </div>
    </LayoutContent>
  );
}
