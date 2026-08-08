import { useState } from 'react';
import { Card, CardHeader, CardBody, Input, Button, Badge, LayoutContent, Tabs } from '@gula/ui-platform';
import { useRTL, useDebounce } from '@gula/ui-platform';
import { DecisionCard } from '../components/DecisionCard';
import { queryDecisionSupport, type DecisionSupportResult } from '../services/decisionSupport';

const MOCK_RESULT: DecisionSupportResult = {
  id: 'ds-1',
  patientId: 'p1',
  query: 'Chest pain with shortness of breath in a 65-year-old diabetic patient',
  summary: 'Based on the patient profile and symptoms, the most likely diagnosis is Acute Coronary Syndrome. Immediate ECG and troponin testing are recommended. Consider differential diagnosis of pulmonary embolism and aortic dissection.',
  summaryAr: 'بناءً على ملف المريض والأعراض، التشخيص الأكثر احتمالاً هو المتلازمة الإكليلية الحادة. يوصى بإجراء تخطيط قلب فوري واختبار التروبونين. النظر في التشخيص التفريقي للانصمام الرئوي وتسليخ الأبهر.',
  recommendations: [
    { id: 'r1', title: 'ECG', titleAr: 'تخطيط القلب', description: 'Perform 12-lead ECG immediately', descriptionAr: 'إجراء تخطيط قلب بـ 12 سلكاً فوراً', priority: 'critical', category: 'test', evidence: 'ACC/AHA Guideline for STEMI', evidenceAr: 'إرشادات ACC/AHA للاحتشاء القلبي', references: [] },
    { id: 'r2', title: 'Troponin', titleAr: 'التروبونين', description: 'High-sensitivity troponin I/T STAT', descriptionAr: 'تروبونين عالي الحساسية I/T فوري', priority: 'critical', category: 'test', evidence: 'ESC Guidelines for ACS', evidenceAr: 'إرشادات ESC للمتلازمة الإكليلية الحادة', references: [] },
    { id: 'r3', title: 'Aspirin', titleAr: 'أسبرين', description: 'Loading dose of Aspirin 325mg chewed', descriptionAr: 'جرعة تحميل من الأسبرين 325 ملغ مضغ', priority: 'critical', category: 'medication', evidence: 'AHA/ACC STEMI Guidelines', evidenceAr: 'إرشادات AHA/ACC للاحتشاء القلبي', references: [] },
    { id: 'r4', title: 'Cardiology Consult', titleAr: 'استشارة قلبية', description: 'Urgent cardiology consultation', descriptionAr: 'استشارة قلبية عاجلة', priority: 'high', category: 'referral', evidence: '', evidenceAr: '', references: [] },
    { id: 'r5', title: 'Monitor', titleAr: 'مراقبة', description: 'Continuous cardiac monitoring', descriptionAr: 'مراقبة قلبية مستمرة', priority: 'high', category: 'monitoring', evidence: '', evidenceAr: '', references: [] },
  ],
  differentialDiagnosis: [
    { condition: 'Acute Coronary Syndrome', conditionAr: 'المتلازمة الإكليلية الحادة', probability: 0.75, supportingFactors: ['Chest pain', 'Diabetes', 'Age > 60'], supportingFactorsAr: ['ألم صدر', 'سكري', 'العمر > 60'], rulingOutFactors: [], rulingOutFactorsAr: [] },
    { condition: 'Pulmonary Embolism', conditionAr: 'الانصمام الرئوي', probability: 0.15, supportingFactors: ['Dyspnea', 'Tachypnea'], supportingFactorsAr: ['ضيق نفس', 'تسرع التنفس'], rulingOutFactors: [], rulingOutFactorsAr: [] },
    { condition: 'Aortic Dissection', conditionAr: 'تسليخ الأبهر', probability: 0.10, supportingFactors: ['Sudden onset', 'Severe pain'], supportingFactorsAr: ['بداية مفاجئة', 'ألم شديد'], rulingOutFactors: [], rulingOutFactorsAr: [] },
  ],
  relevantGuidelines: [],
  drugInteractions: [],
  riskFactors: [],
  evidenceLevel: 'moderate',
  confidence: 0.85,
  createdAt: new Date().toISOString(),
};

export function DecisionSupport() {
  const { isRtl } = useRTL();
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<DecisionSupportResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [history, setHistory] = useState<DecisionSupportResult[]>([]);
  const [activeTab, setActiveTab] = useState('query');

  const handleQuery = async () => {
    if (!query.trim()) return;
    setIsLoading(true);
    try {
      await new Promise(r => setTimeout(r, 1500));
      setResult(MOCK_RESULT);
      setHistory(prev => [MOCK_RESULT, ...prev]);
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
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    placeholder={isRtl
                      ? 'اكتب الاستعلام السريري... مثال: ألم صدر مع ضيق تنفس لدى مريض سكري عمر 65 سنة'
                      : 'Enter clinical query... e.g., Chest pain with SOB in a 65-year-old diabetic'}
                  />
                  <Button variant="primary" onClick={handleQuery} loading={isLoading} disabled={!query.trim()}>
                    {isRtl ? 'تحليل' : 'Analyze'}
                  </Button>
                </div>
              </CardBody>
            </Card>

            {isLoading && (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                  <p className="text-sm text-neutral-500">{isRtl ? 'جاري تحليل البيانات السريرية...' : 'Analyzing clinical data...'}</p>
                </div>
              </div>
            )}

            {result && !isLoading && (
              <DecisionCard
                result={result}
                onExplain={(id) => {}}
                onApply={(id) => {}}
                onDismiss={(id) => {}}
              />
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
                <DecisionCard
                  key={h.id}
                  result={h}
                  onExplain={(id) => {}}
                  onApply={(id) => {}}
                  onDismiss={(id) => {}}
                />
              ))
            )}
          </div>
        )}
      </div>
    </LayoutContent>
  );
}
