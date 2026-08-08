import { useState, useCallback } from 'react';
import { Input, Button, Card, CardHeader, CardBody, Badge } from '@gula/ui-platform';
import { useRTL, useDebounce } from '@gula/ui-platform';
import { searchPatients, type Patient, type PatientSearchResult } from '../services/patient';

interface FHIRSearchProps {
  onPatientSelect: (patient: Patient) => void;
  mode?: 'simple' | 'advanced';
}

export function FHIRSearch({ onPatientSelect, mode = 'simple' }: FHIRSearchProps) {
  const { isRtl } = useRTL();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<PatientSearchResult | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [advancedFilters, setAdvancedFilters] = useState({
    nationalId: '',
    name: '',
    phone: '',
    dateOfBirth: '',
    gender: '',
    city: '',
    governorate: '',
  });

  const performSearch = useCallback(async (q: string) => {
    if (!q.trim() && mode === 'simple') return;
    setIsSearching(true);
    try {
      const params = mode === 'simple'
        ? { query: q, pageSize: 20 }
        : { ...advancedFilters, query: q, pageSize: 20 };
      const res = await searchPatients(params);
      setResults(res);
    } catch {
      setResults(null);
    } finally {
      setIsSearching(false);
    }
  }, [mode, advancedFilters]);

  const debouncedSearch = useDebounce(performSearch, 300);

  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    if (mode === 'simple') {
      debouncedSearch(e.target.value);
    }
  };

  const handleAdvancedSearch = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(query);
  };

  const handleParamChange = (key: string, value: string) => {
    setAdvancedFilters(prev => ({ ...prev, [key]: value }));
  };

  return (
    <Card>
      <CardHeader
        title={isRtl ? 'البحث عن مريض' : 'Patient Search'}
        subtitle={isRtl ? 'FHIR - بحث متوافق مع المعايير العالمية' : 'FHIR-compliant search'}
      />
      <CardBody>
        <div className="space-y-4">
          <div className="flex gap-2">
            <div className="flex-1">
              <Input
                value={query}
                onChange={handleQueryChange}
                placeholder={isRtl ? 'ابحث باسم المريض، الرقم الوطني، أو رقم الهاتف...' : 'Search by name, national ID, or phone...'}
              />
            </div>
            {mode === 'advanced' && (
              <Button variant="primary" onClick={handleAdvancedSearch} loading={isSearching}>
                {isRtl ? 'بحث' : 'Search'}
              </Button>
            )}
          </div>

          {mode === 'advanced' && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 p-4 rounded-xl bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700">
              <Input label={isRtl ? 'الرقم الوطني' : 'National ID'} value={advancedFilters.nationalId} onChange={e => handleParamChange('nationalId', e.target.value)} />
              <Input label={isRtl ? 'الاسم' : 'Name'} value={advancedFilters.name} onChange={e => handleParamChange('name', e.target.value)} />
              <Input label={isRtl ? 'رقم الهاتف' : 'Phone'} value={advancedFilters.phone} onChange={e => handleParamChange('phone', e.target.value)} />
              <Input label={isRtl ? 'تاريخ الميلاد' : 'Date of Birth'} type="date" value={advancedFilters.dateOfBirth} onChange={e => handleParamChange('dateOfBirth', e.target.value)} />
              <div>
                <label className="block text-sm font-medium mb-1">{isRtl ? 'الجنس' : 'Gender'}</label>
                <select value={advancedFilters.gender} onChange={e => handleParamChange('gender', e.target.value)} className="w-full rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-3 py-2 text-sm">
                  <option value="">{isRtl ? 'الكل' : 'All'}</option>
                  <option value="male">{isRtl ? 'ذكر' : 'Male'}</option>
                  <option value="female">{isRtl ? 'أنثى' : 'Female'}</option>
                </select>
              </div>
              <Input label={isRtl ? 'المدينة' : 'City'} value={advancedFilters.city} onChange={e => handleParamChange('city', e.target.value)} />
            </div>
          )}

          {isSearching && (
            <div className="flex items-center justify-center py-8">
              <div className="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
            </div>
          )}

          {results && !isSearching && (
            <div className="space-y-2">
              <p className="text-sm text-neutral-500">
                {results.total} {isRtl ? 'نتيجة' : 'result(s)'}
              </p>
              {results.patients.length === 0 ? (
                <p className="text-sm text-neutral-500 text-center py-4">
                  {isRtl ? 'لم يتم العثور على مرضى' : 'No patients found'}
                </p>
              ) : (
                <div className="divide-y divide-neutral-100 dark:divide-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl overflow-hidden max-h-96 overflow-y-auto">
                  {results.patients.map(patient => (
                    <button
                      key={patient.id}
                      onClick={() => onPatientSelect(patient)}
                      className="w-full text-right p-4 hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-600 dark:text-primary-400 font-bold shrink-0">
                          {(patient.nameAr || patient.name).charAt(0)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm text-neutral-900 dark:text-neutral-50">
                            {patient.nameAr || patient.name}
                          </p>
                          <p className="text-xs text-neutral-500">
                            {patient.gender === 'male' ? (isRtl ? 'ذكر' : 'Male') : (isRtl ? 'أنثى' : 'Female')}
                            {patient.dateOfBirth && ` | ${new Date().getFullYear() - new Date(patient.dateOfBirth).getFullYear()} ${isRtl ? 'سنة' : 'yrs'}`}
                          </p>
                          <div className="flex gap-1.5 mt-1">
                            {patient.nationalId && (
                              <Badge variant="default" size="xs">{patient.nationalId}</Badge>
                            )}
                            {patient.bloodType && (
                              <Badge variant="info" size="xs">{patient.bloodType}</Badge>
                            )}
                          </div>
                        </div>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-neutral-400 shrink-0">
                          <path d={isRtl ? "M15 18l-6-6 6-6" : "M9 18l6-6-6-6"} />
                        </svg>
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {results.mpiMatchCount !== undefined && results.mpiMatchCount > 0 && (
                <div className="p-3 rounded-xl bg-warning-50 dark:bg-warning-950 border border-warning-200 dark:border-warning-900">
                  <p className="text-xs text-warning-700 dark:text-warning-400">
                    {isRtl
                      ? `تم العثور على ${results.mpiMatchCount} تطابق محتمل في MPI`
                      : `${results.mpiMatchCount} potential MPI matches found`}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </CardBody>
    </Card>
  );
}
