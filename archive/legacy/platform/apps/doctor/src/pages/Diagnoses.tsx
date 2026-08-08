import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardBody, Button, Badge, LayoutContent } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import { DiagnosisInput } from '../components/DiagnosisInput';

interface DiagnosisRecord {
  id: string;
  code: string;
  codingSystem: 'ICD-10' | 'ICD-11';
  description: string;
  descriptionAr: string;
  type: 'primary' | 'secondary' | 'complication';
  status: 'active' | 'resolved' | 'chronic' | 'suspected';
  date: string;
}

const MOCK_DIAGNOSES: DiagnosisRecord[] = [
  { id: 'd1', code: 'E11.9', codingSystem: 'ICD-10', description: 'Type 2 diabetes mellitus without complications', descriptionAr: 'داء السكري من النوع 2 دون مضاعفات', type: 'primary', status: 'chronic', date: '2020-03-15' },
  { id: 'd2', code: 'I10', codingSystem: 'ICD-10', description: 'Essential (primary) hypertension', descriptionAr: 'ارتفاع ضغط الدم الأساسي', type: 'primary', status: 'chronic', date: '2019-06-20' },
  { id: 'd3', code: 'E78.5', codingSystem: 'ICD-10', description: 'Hyperlipidemia', descriptionAr: 'فرط شحميات الدم', type: 'secondary', status: 'active', date: '2021-01-10' },
];

export function Diagnoses() {
  const { patientId } = useParams<{ patientId: string }>();
  const { isRtl } = useRTL();
  const navigate = useNavigate();
  const [diagnoses, setDiagnoses] = useState<DiagnosisRecord[]>(MOCK_DIAGNOSES);
  const [showAddForm, setShowAddForm] = useState(false);

  const handleAddDiagnosis = (data: { code: string; codingSystem: 'ICD-10' | 'ICD-11'; description: string; descriptionAr: string; type: 'primary' | 'secondary' | 'complication'; status: 'active' | 'chronic' | 'suspected'; notes?: string }) => {
    const newDiagnosis: DiagnosisRecord = {
      id: `d-${Date.now()}`,
      code: data.code,
      codingSystem: data.codingSystem,
      description: data.description,
      descriptionAr: data.descriptionAr,
      type: data.type,
      status: data.status,
      date: new Date().toISOString().split('T')[0],
    };
    setDiagnoses(prev => [newDiagnosis, ...prev]);
    setShowAddForm(false);
  };

  const typeColors: Record<string, 'primary' | 'default' | 'warning'> = {
    primary: 'primary',
    secondary: 'default',
    complication: 'warning',
  };
  const statusColors: Record<string, 'success' | 'default' | 'danger' | 'warning'> = {
    active: 'success',
    chronic: 'warning',
    resolved: 'default',
    suspected: 'danger',
  };

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={() => navigate(-1)} className="p-2 rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-800">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d={isRtl ? "M19 12H5M12 19l-7-7 7-7" : "M5 12h14M12 5l7 7-7 7"} />
              </svg>
            </button>
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
              {isRtl ? 'التشخيصات' : 'Diagnoses'}
            </h1>
          </div>
          <Button variant="primary" onClick={() => setShowAddForm(true)}>
            {isRtl ? 'إضافة تشخيص' : 'Add Diagnosis'}
          </Button>
        </div>

        {showAddForm && (
          <DiagnosisInput
            onAdd={handleAddDiagnosis}
            existingDiagnoses={diagnoses.map(d => d.code)}
          />
        )}

        <div className="space-y-2">
          {diagnoses.map(diag => (
            <Card key={diag.id} padding="md">
              <CardBody>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <code className="text-sm font-mono font-bold text-primary-600 dark:text-primary-400">{diag.code}</code>
                      <Badge variant={typeColors[diag.type]} size="xs">
                        {isRtl ? (diag.type === 'primary' ? 'رئيسي' : diag.type === 'secondary' ? 'ثانوي' : 'مضاعف') : diag.type}
                      </Badge>
                      <Badge variant={statusColors[diag.status]} size="xs">
                        {diag.status === 'active' ? (isRtl ? 'نشط' : 'Active') :
                         diag.status === 'chronic' ? (isRtl ? 'مزمن' : 'Chronic') :
                         diag.status === 'resolved' ? (isRtl ? 'منتهي' : 'Resolved') :
                         (isRtl ? 'مشتبه' : 'Suspected')}
                      </Badge>
                    </div>
                    <p className="font-medium text-sm">
                      {isRtl ? diag.descriptionAr : diag.description}
                    </p>
                    <p className="text-xs text-neutral-400 mt-1">
                      {diag.codingSystem} | {new Date(diag.date).toLocaleDateString(isRtl ? 'ar-IQ' : 'en-US')}
                    </p>
                  </div>
                </div>
              </CardBody>
            </Card>
          ))}
          {diagnoses.length === 0 && (
            <p className="text-sm text-neutral-500 text-center py-8">{isRtl ? 'لا توجد تشخيصات' : 'No diagnoses'}</p>
          )}
        </div>
      </div>
    </LayoutContent>
  );
}
