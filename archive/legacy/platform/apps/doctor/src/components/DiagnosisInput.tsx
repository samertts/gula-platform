import { useState, useCallback } from 'react';
import { Card, CardHeader, CardBody, Input, Button, Badge } from '@gula/ui-platform';
import { useRTL, useDebounce } from '@gula/ui-platform';

interface ICDCode {
  code: string;
  description: string;
  descriptionAr: string;
  system: 'ICD-10' | 'ICD-11';
  category: string;
}

interface DiagnosisInputProps {
  onAdd: (diagnosis: {
    code: string;
    codingSystem: 'ICD-10' | 'ICD-11';
    description: string;
    descriptionAr: string;
    type: 'primary' | 'secondary' | 'complication';
    status: 'active' | 'chronic' | 'suspected';
    notes?: string;
  }) => void;
  existingDiagnoses?: string[];
}

const MOCK_ICD_CODES: ICDCode[] = [
  { code: 'E11.9', description: 'Type 2 diabetes mellitus without complications', descriptionAr: 'داء السكري من النوع 2 دون مضاعفات', system: 'ICD-10', category: 'Endocrine' },
  { code: 'I10', description: 'Essential (primary) hypertension', descriptionAr: 'ارتفاع ضغط الدم الأساسي', system: 'ICD-10', category: 'Cardiovascular' },
  { code: 'J45.9', description: 'Asthma', descriptionAr: 'الربو', system: 'ICD-10', category: 'Respiratory' },
  { code: 'N18.9', description: 'Chronic kidney disease', descriptionAr: 'مرض الكلى المزمن', system: 'ICD-10', category: 'Renal' },
  { code: 'J44.9', description: 'COPD', descriptionAr: 'مرض الانسداد الرئوي المزمن', system: 'ICD-10', category: 'Respiratory' },
  { code: 'K21.9', description: 'GERD', descriptionAr: 'الارتجاع المعدي المريئي', system: 'ICD-10', category: 'Digestive' },
  { code: 'F32.9', description: 'Major depressive disorder', descriptionAr: 'اضطراب اكتئابي كبير', system: 'ICD-10', category: 'Mental' },
  { code: 'M54.5', description: 'Low back pain', descriptionAr: 'آلام أسفل الظهر', system: 'ICD-10', category: 'Musculoskeletal' },
  { code: 'E78.5', description: 'Hyperlipidemia', descriptionAr: 'فرط شحميات الدم', system: 'ICD-10', category: 'Metabolic' },
  { code: 'D64.9', description: 'Anemia', descriptionAr: 'فقر الدم', system: 'ICD-10', category: 'Hematologic' },
  { code: 'MG26', description: 'Chronic pain', descriptionAr: 'الألم المزمن', system: 'ICD-11', category: 'Pain' },
  { code: '5B51.0', description: 'Type 1 diabetes mellitus', descriptionAr: 'داء السكري من النوع 1', system: 'ICD-11', category: 'Endocrine' },
];

export function DiagnosisInput({ onAdd, existingDiagnoses = [] }: DiagnosisInputProps) {
  const { isRtl } = useRTL();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<ICDCode[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedType, setSelectedType] = useState<'primary' | 'secondary' | 'complication'>('secondary');
  const [selectedStatus, setSelectedStatus] = useState<'active' | 'chronic' | 'suspected'>('active');
  const [notes, setNotes] = useState('');

  const searchICD = useCallback(async (q: string) => {
    if (q.length < 2) {
      setResults([]);
      return;
    }
    setIsSearching(true);
    await new Promise(r => setTimeout(r, 200));
    const filtered = MOCK_ICD_CODES.filter(
      d => d.code.includes(q) || d.description.toLowerCase().includes(q.toLowerCase()) || d.descriptionAr.includes(q),
    );
    setResults(filtered);
    setIsSearching(false);
  }, []);

  const debouncedSearch = useDebounce(searchICD, 300);

  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    debouncedSearch(e.target.value);
  };

  const handleSelect = (code: ICDCode) => {
    onAdd({
      code: code.code,
      codingSystem: code.system,
      description: code.description,
      descriptionAr: code.descriptionAr,
      type: selectedType,
      status: selectedStatus,
      notes: notes || undefined,
    });
    setQuery('');
    setResults([]);
    setNotes('');
  };

  return (
    <Card>
      <CardHeader title={isRtl ? 'إضافة تشخيص' : 'Add Diagnosis'} />
      <CardBody>
        <div className="space-y-4">
          <Input
            label={isRtl ? 'البحث عن رمز ICD' : 'Search ICD Code'}
            value={query}
            onChange={handleQueryChange}
            placeholder={isRtl ? 'ابحث بالرمز أو الوصف...' : 'Search by code or description...'}
          />

          {isSearching && (
            <p className="text-sm text-neutral-500">{isRtl ? 'جاري البحث...' : 'Searching...'}</p>
          )}

          {results.length > 0 && (
            <div className="max-h-60 overflow-y-auto border border-neutral-200 dark:border-neutral-700 rounded-xl divide-y divide-neutral-100 dark:divide-neutral-800">
              {results.map(code => (
                <button
                  key={code.code}
                  type="button"
                  onClick={() => handleSelect(code)}
                  disabled={existingDiagnoses.includes(code.code)}
                  className="w-full text-right p-3 hover:bg-neutral-50 dark:hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <code className="text-sm font-mono font-bold text-primary-600 dark:text-primary-400">
                      {code.code}
                    </code>
                    <Badge variant="default" size="xs">{code.system}</Badge>
                    <Badge variant="info" size="xs">{code.category}</Badge>
                  </div>
                  <p className="text-sm text-neutral-700 dark:text-neutral-300 mt-0.5">
                    {isRtl ? code.descriptionAr : code.description}
                  </p>
                </button>
              ))}
            </div>
          )}

          {query && results.length === 0 && !isSearching && (
            <p className="text-sm text-neutral-500">{isRtl ? 'لا توجد نتائج' : 'No results found'}</p>
          )}

          {query && results.length > 0 && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
                    {isRtl ? 'النوع' : 'Type'}
                  </label>
                  <select
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value as any)}
                    className="w-full rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-3 py-2 text-sm"
                  >
                    <option value="primary">{isRtl ? 'رئيسي' : 'Primary'}</option>
                    <option value="secondary">{isRtl ? 'ثانوي' : 'Secondary'}</option>
                    <option value="complication">{isRtl ? 'مضاعفة' : 'Complication'}</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
                    {isRtl ? 'الحالة' : 'Status'}
                  </label>
                  <select
                    value={selectedStatus}
                    onChange={(e) => setSelectedStatus(e.target.value as any)}
                    className="w-full rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-3 py-2 text-sm"
                  >
                    <option value="active">{isRtl ? 'نشط' : 'Active'}</option>
                    <option value="chronic">{isRtl ? 'مزمن' : 'Chronic'}</option>
                    <option value="suspected">{isRtl ? 'مشتبه' : 'Suspected'}</option>
                  </select>
                </div>
              </div>

              <Input
                label={isRtl ? 'ملاحظات' : 'Notes'}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </>
          )}
        </div>
      </CardBody>
    </Card>
  );
}
