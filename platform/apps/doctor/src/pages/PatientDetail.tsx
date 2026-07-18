import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardBody, Badge, Button, Tabs, LayoutContent, LayoutSplit, LoadingSpinner } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import { usePatientContext } from '../contexts/PatientContext';
import { useClinicalContext } from '../contexts/ClinicalContext';
import { VitalSigns } from '../components/VitalSigns';
import { MedicationList } from '../components/MedicationList';
import { LabResultView } from '../components/LabResultView';
import { AlertBanner } from '../components/AlertBanner';

const MOCK_MEDS = [
  { id: 'm1', name: 'Lisinopril', nameAr: 'ليسينوبريل', strength: '10mg', form: 'Tablet', dose: '10mg', frequency: 'QD', route: 'PO', startDate: '2024-01-15', status: 'active' as const, prescribedBy: 'Dr. Ahmed' },
  { id: 'm2', name: 'Metformin', nameAr: 'ميتفورمين', strength: '500mg', form: 'Tablet', dose: '500mg', frequency: 'BID', route: 'PO', startDate: '2024-03-01', status: 'active' as const, prescribedBy: 'Dr. Ahmed' },
  { id: 'm3', name: 'Atorvastatin', nameAr: 'أتورفاستاتين', strength: '20mg', form: 'Tablet', dose: '20mg', frequency: 'QHS', route: 'PO', startDate: '2024-02-01', status: 'active' as const, prescribedBy: 'Dr. Ahmed' },
];

export function PatientDetail() {
  const { patientId } = useParams<{ patientId: string }>();
  const { isRtl } = useRTL();
  const navigate = useNavigate();
  const { selectedPatient, loadPatient, isLoadingPatient } = usePatientContext();
  const { vitalSigns, loadVitalSigns, labResults, loadLabResults, allergies, loadAllergies, isLoading } = useClinicalContext();
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (patientId) {
      loadPatient(patientId);
      loadVitalSigns(patientId);
      loadLabResults(patientId);
      loadAllergies(patientId);
    }
  }, [patientId]);

  if (isLoadingPatient || !selectedPatient) {
    return <LoadingSpinner />;
  }

  const patient = selectedPatient;
  const age = new Date().getFullYear() - new Date(patient.dateOfBirth).getFullYear();

  const tabs = [
    { id: 'overview', label: isRtl ? 'نظرة عامة' : 'Overview' },
    { id: 'vitals', label: isRtl ? 'العلامات الحيوية' : 'Vitals' },
    { id: 'medications', label: isRtl ? 'الأدوية' : 'Medications' },
    { id: 'lab', label: isRtl ? 'المختبر' : 'Lab' },
    { id: 'allergies', label: isRtl ? 'الحساسية' : 'Allergies' },
  ];

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="p-2 rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-800">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d={isRtl ? "M19 12H5M12 19l-7-7 7-7" : "M5 12h14M12 5l7 7-7 7"} />
            </svg>
          </button>
          <div>
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
              {patient.nameAr || patient.name}
            </h1>
            <p className="text-sm text-neutral-500">
              {isRtl ? `${age} سنة` : `${age} years`} | {patient.gender === 'male' ? (isRtl ? 'ذكر' : 'Male') : (isRtl ? 'أنثى' : 'Female')}
              {patient.bloodType && ` | ${patient.bloodType}`}
            </p>
          </div>
        </div>

        <AlertBanner
          alerts={[
            ...allergies.filter(a => a.severity === 'severe').map(a => ({
              id: a.id,
              type: 'critical' as const,
              title: isRtl ? 'حساسية شديدة' : 'Severe Allergy',
              titleAr: 'حساسية شديدة',
              message: `${a.allergen}: ${a.reaction}`,
              messageAr: `${a.allergenAr || a.allergen}: ${a.reaction}`,
            })),
            ...(patient.chronicConditions?.length > 0 ? [{
              id: 'chronic',
              type: 'warning' as const,
              title: isRtl ? 'حالات مزمنة' : 'Chronic Conditions',
              titleAr: 'حالات مزمنة',
              message: patient.chronicConditions.join(', '),
              messageAr: patient.chronicConditions.join(', '),
            }] : []),
          ]}
        />

        <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

        {activeTab === 'overview' && (
          <LayoutSplit ratio="2:1" left={
            <div className="space-y-4">
              <Card>
                <CardHeader title={isRtl ? 'معلومات المريض' : 'Patient Information'} />
                <CardBody>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-neutral-500">{isRtl ? 'الاسم' : 'Name'}</p>
                      <p className="font-medium">{patient.nameAr || patient.name}</p>
                    </div>
                    {patient.nationalId && (
                      <div>
                        <p className="text-neutral-500">{isRtl ? 'الرقم الوطني' : 'National ID'}</p>
                        <p className="font-medium font-mono">{patient.nationalId}</p>
                      </div>
                    )}
                    <div>
                      <p className="text-neutral-500">{isRtl ? 'تاريخ الميلاد' : 'Date of Birth'}</p>
                      <p className="font-medium">{new Date(patient.dateOfBirth).toLocaleDateString(isRtl ? 'ar-IQ' : 'en-US')}</p>
                    </div>
                    <div>
                      <p className="text-neutral-500">{isRtl ? 'فصيلة الدم' : 'Blood Type'}</p>
                      <p className="font-medium">{patient.bloodType || '-'}</p>
                    </div>
                    {patient.phone && (
                      <div>
                        <p className="text-neutral-500">{isRtl ? 'الهاتف' : 'Phone'}</p>
                        <p className="font-medium">{patient.phone}</p>
                      </div>
                    )}
                    {patient.email && (
                      <div>
                        <p className="text-neutral-500">{isRtl ? 'البريد' : 'Email'}</p>
                        <p className="font-medium">{patient.email}</p>
                      </div>
                    )}
                  </div>
                </CardBody>
              </Card>

              {vitalSigns.length > 0 && (
                <VitalSigns vitals={vitalSigns[vitalSigns.length - 1]} history={vitalSigns} />
              )}

              <LabResultView results={labResults.slice(0, 5)} />
            </div>
          } right={
            <div className="space-y-4">
              <MedicationList medications={MOCK_MEDS} />
              <Card>
                <CardHeader title={isRtl ? 'الإجراءات' : 'Actions'} />
                <CardBody className="space-y-2">
                  <Button fullWidth variant="primary" onClick={() => navigate(`/patients/${patientId}/timeline`)}>
                    {isRtl ? 'التاريخ السريري' : 'Clinical Timeline'}
                  </Button>
                  <Button fullWidth variant="secondary" onClick={() => navigate(`/patients/${patientId}/visits`)}>
                    {isRtl ? 'الزيارات' : 'Visits'}
                  </Button>
                  <Button fullWidth variant="secondary" onClick={() => navigate(`/patients/${patientId}/diagnoses`)}>
                    {isRtl ? 'التشخيصات' : 'Diagnoses'}
                  </Button>
                  <Button fullWidth variant="secondary" onClick={() => navigate(`/patients/${patientId}/orders`)}>
                    {isRtl ? 'الطلبات' : 'Orders'}
                  </Button>
                  <Button fullWidth variant="outline" onClick={() => navigate(`/patients/${patientId}/lab-requests`)}>
                    {isRtl ? 'طلب مختبر' : 'Lab Request'}
                  </Button>
                  <Button fullWidth variant="outline" onClick={() => navigate(`/patients/${patientId}/radiology`)}>
                    {isRtl ? 'طلب أشعة' : 'Radiology Request'}
                  </Button>
                </CardBody>
              </Card>
            </div>
          } />
        )}

        {activeTab === 'vitals' && vitalSigns.length > 0 && (
          <VitalSigns vitals={vitalSigns[vitalSigns.length - 1]} showHistory history={vitalSigns} onRecord={() => {}} />
        )}

        {activeTab === 'medications' && (
          <MedicationList medications={MOCK_MEDS} />
        )}

        {activeTab === 'lab' && (
          <LabResultView results={labResults} />
        )}

        {activeTab === 'allergies' && (
          <Card>
            <CardHeader title={isRtl ? 'الحساسية' : 'Allergies'} />
            <CardBody>
              {allergies.length === 0 ? (
                <p className="text-sm text-neutral-500 text-center py-4">{isRtl ? 'لا توجد حساسية مسجلة' : 'No allergies recorded'}</p>
              ) : (
                <div className="space-y-2">
                  {allergies.map(a => (
                    <div key={a.id} className="p-3 rounded-xl bg-neutral-50 dark:bg-neutral-900 flex items-center justify-between">
                      <div>
                        <p className="font-medium text-sm">{isRtl ? a.allergenAr : a.allergen}</p>
                        <p className="text-xs text-neutral-500">{a.reaction}</p>
                      </div>
                      <Badge variant={a.severity === 'severe' ? 'danger' : a.severity === 'moderate' ? 'warning' : 'info'}>
                        {a.severity === 'severe' ? (isRtl ? 'شديدة' : 'Severe') : a.severity === 'moderate' ? (isRtl ? 'متوسطة' : 'Moderate') : (isRtl ? 'خفيفة' : 'Mild')}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardBody>
          </Card>
        )}
      </div>
    </LayoutContent>
  );
}
