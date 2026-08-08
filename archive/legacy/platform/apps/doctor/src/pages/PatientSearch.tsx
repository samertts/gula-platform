import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardBody, Input, Button, Badge, Tabs, LayoutContent, EmptyState } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import { FHIRSearch } from '../components/FHIRSearch';
import { PatientCard } from '../components/PatientCard';
import { searchPatients, getRecentPatients, type Patient } from '../services/patient';
import { usePatientContext } from '../contexts/PatientContext';

export function PatientSearch() {
  const { isRtl } = useRTL();
  const navigate = useNavigate();
  const { selectPatient } = usePatientContext();
  const [mode, setMode] = useState<'simple' | 'advanced'>('simple');
  const [recentPatients, setRecentPatients] = useState<Patient[]>([]);
  const [isLoadingRecent, setIsLoadingRecent] = useState(true);

  useState(() => {
    getRecentPatients(1, 10)
      .then(res => setRecentPatients(res.patients))
      .catch(() => {})
      .finally(() => setIsLoadingRecent(false));
  });

  const handlePatientSelect = (patient: Patient) => {
    selectPatient(patient);
    navigate(`/patients/${patient.id}`);
  };

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
            {isRtl ? 'البحث عن مرضى' : 'Patient Search'}
          </h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            {isRtl ? 'ابحث في السجل الصحي الوطني باستخدام معايير FHIR' : 'Search the national health record using FHIR standards'}
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setMode('simple')}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
              mode === 'simple'
                ? 'bg-primary-500 text-white shadow-sm'
                : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300'
            }`}
          >
            {isRtl ? 'بحث بسيط' : 'Simple Search'}
          </button>
          <button
            onClick={() => setMode('advanced')}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
              mode === 'advanced'
                ? 'bg-primary-500 text-white shadow-sm'
                : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300'
            }`}
          >
            {isRtl ? 'بحث متقدم' : 'Advanced Search'}
          </button>
        </div>

        <FHIRSearch onPatientSelect={handlePatientSelect} mode={mode} />

        <Card>
          <CardHeader title={isRtl ? 'المرضى الأخيرون' : 'Recent Patients'} />
          <CardBody>
            {isLoadingRecent ? (
              <div className="space-y-3">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-20 rounded-xl bg-neutral-100 dark:bg-neutral-800 animate-pulse" />
                ))}
              </div>
            ) : recentPatients.length === 0 ? (
              <EmptyState
                title={isRtl ? 'لا يوجد مرضى حديثون' : 'No recent patients'}
                description={isRtl ? 'ابحث عن مريض للبدء' : 'Search for a patient to start'}
              />
            ) : (
              <div className="space-y-2">
                {recentPatients.map(patient => (
                  <PatientCard
                    key={patient.id}
                    patient={patient}
                    onClick={() => handlePatientSelect(patient)}
                  />
                ))}
              </div>
            )}
          </CardBody>
        </Card>
      </div>
    </LayoutContent>
  );
}
