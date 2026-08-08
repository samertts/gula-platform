import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardBody, Button, Badge, Input, LayoutContent, Select } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import type { OrderPriority } from '../services/orders';

interface LabTest {
  code: string;
  name: string;
  nameAr: string;
  sampleType: string;
  container: string;
  fasting: boolean;
}

const AVAILABLE_TESTS: LabTest[] = [
  { code: 'CBC', name: 'Complete Blood Count', nameAr: 'تعداد دم كامل', sampleType: 'Blood', container: 'EDTA', fasting: false },
  { code: 'BMP', name: 'Basic Metabolic Panel', nameAr: 'لوحة استقلابية أساسية', sampleType: 'Blood', container: 'SST', fasting: true },
  { code: 'LFT', name: 'Liver Function Tests', nameAr: 'وظائف الكبد', sampleType: 'Blood', container: 'SST', fasting: false },
  { code: 'RFT', name: 'Renal Function Tests', nameAr: 'وظائف الكلى', sampleType: 'Blood', container: 'SST', fasting: false },
  { code: 'TSH', name: 'Thyroid Stimulating Hormone', nameAr: 'هرمون الغدة الدرقية', sampleType: 'Blood', container: 'SST', fasting: false },
  { code: 'HbA1c', name: 'Hemoglobin A1c', nameAr: 'الهيموغلوبين السكري', sampleType: 'Blood', container: 'EDTA', fasting: false },
  { code: 'UA', name: 'Urinalysis', nameAr: 'تحليل البول', sampleType: 'Urine', container: 'Urine Cup', fasting: false },
  { code: 'PT/INR', name: 'Prothrombin Time / INR', nameAr: 'زمن البروثرومبين', sampleType: 'Blood', container: 'Citrate', fasting: false },
];

export function LabRequests() {
  const { patientId } = useParams<{ patientId: string }>();
  const { isRtl } = useRTL();
  const navigate = useNavigate();
  const [selectedTests, setSelectedTests] = useState<LabTest[]>([]);
  const [priority, setPriority] = useState<OrderPriority>('routine');
  const [searchQuery, setSearchQuery] = useState('');
  const [instructions, setInstructions] = useState('');
  const [clinicalIndication, setClinicalIndication] = useState('');

  const filteredTests = AVAILABLE_TESTS.filter(t =>
    t.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.nameAr.includes(searchQuery),
  );

  const toggleTest = (test: LabTest) => {
    setSelectedTests(prev =>
      prev.find(t => t.code === test.code)
        ? prev.filter(t => t.code !== test.code)
        : [...prev, test],
    );
  };

  const handleSubmit = () => {
    if (selectedTests.length === 0) return;
    navigate(-1);
  };

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="p-2 rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-800">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d={isRtl ? "M19 12H5M12 19l-7-7 7-7" : "M5 12h14M12 5l7 7-7 7"} />
            </svg>
          </button>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
            {isRtl ? 'طلب تحاليل مختبر' : 'Lab Test Request'}
          </h1>
        </div>

        <Card>
          <CardHeader title={isRtl ? 'اختيار الفحوصات' : 'Select Tests'} />
          <CardBody>
            <div className="space-y-4">
              <Input
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder={isRtl ? 'ابحث عن فحص...' : 'Search for a test...'}
              />

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 max-h-80 overflow-y-auto">
                {filteredTests.map(test => (
                  <button
                    key={test.code}
                    onClick={() => toggleTest(test)}
                    className={`p-3 rounded-xl text-right border-2 transition-colors ${
                      selectedTests.find(t => t.code === test.code)
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-950'
                        : 'border-neutral-200 dark:border-neutral-700 hover:border-primary-300'
                    }`}
                  >
                    <p className="font-medium text-sm">{isRtl ? test.nameAr : test.name}</p>
                    <p className="text-xs text-neutral-500 mt-1">
                      {test.code} | {isRtl ? test.sampleType : test.sampleType} | {test.container}
                    </p>
                    {test.fasting && (
                      <Badge variant="warning" size="xs" className="mt-1">
                        {isRtl ? 'صائم' : 'Fasting'}
                      </Badge>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title={isRtl ? 'تفاصيل الطلب' : 'Request Details'} />
          <CardBody>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">{isRtl ? 'الأولوية' : 'Priority'}</label>
                <select
                  value={priority}
                  onChange={e => setPriority(e.target.value as OrderPriority)}
                  className="w-full rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-3 py-2 text-sm"
                >
                  <option value="routine">{isRtl ? 'روتيني' : 'Routine'}</option>
                  <option value="urgent">{isRtl ? 'عاجل' : 'Urgent'}</option>
                  <option value="stat">{isRtl ? 'فوري' : 'STAT'}</option>
                  <option value="asap">{isRtl ? 'في أقرب وقت' : 'ASAP'}</option>
                </select>
              </div>

              <Input
                label={isRtl ? 'التبرير السريري' : 'Clinical Indication'}
                value={clinicalIndication}
                onChange={e => setClinicalIndication(e.target.value)}
              />

              <Input
                label={isRtl ? 'تعليمات إضافية' : 'Additional Instructions'}
                value={instructions}
                onChange={e => setInstructions(e.target.value)}
              />

              {selectedTests.length > 0 && (
                <div className="p-4 rounded-xl bg-primary-50 dark:bg-primary-950 border border-primary-200 dark:border-primary-900">
                  <p className="font-medium text-sm mb-2">
                    {isRtl ? `الفحوصات المختارة (${selectedTests.length})` : `Selected Tests (${selectedTests.length})`}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {selectedTests.map(t => (
                      <Badge key={t.code} variant="primary">{t.code}</Badge>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <Button
                  variant="primary"
                  onClick={handleSubmit}
                  disabled={selectedTests.length === 0}
                >
                  {isRtl ? 'إرسال الطلب' : 'Submit Request'}
                </Button>
                <Button variant="ghost" onClick={() => navigate(-1)}>
                  {isRtl ? 'إلغاء' : 'Cancel'}
                </Button>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>
    </LayoutContent>
  );
}
