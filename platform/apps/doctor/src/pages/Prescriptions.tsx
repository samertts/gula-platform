import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardBody, Button, Badge, LayoutContent } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import { PrescriptionForm } from '../components/PrescriptionForm';

interface PrescriptionRecord {
  id: string;
  patientName: string;
  patientNameAr: string;
  medications: { name: string; nameAr: string }[];
  status: string;
  statusAr: string;
  isSigned: boolean;
  createdAt: string;
  isControlled: boolean;
}

const MOCK_RX: PrescriptionRecord[] = [
  { id: 'rx1', patientName: 'Ahmed Ali', patientNameAr: 'أحمد علي', medications: [{ name: 'Lisinopril', nameAr: 'ليسينوبريل' }, { name: 'Metformin', nameAr: 'ميتفورمين' }], status: 'active', statusAr: 'نشط', isSigned: true, createdAt: '2024-12-15', isControlled: false },
  { id: 'rx2', patientName: 'Sara Mohammed', patientNameAr: 'سارة محمد', medications: [{ name: 'Albuterol Inhaler', nameAr: 'البوتيرول' }], status: 'dispensed', statusAr: 'صرف', isSigned: true, createdAt: '2024-12-10', isControlled: false },
  { id: 'rx3', patientName: 'Hassan Ibrahim', patientNameAr: 'حسن إبراهيم', medications: [{ name: 'Tramadol', nameAr: 'ترامادول' }], status: 'active', statusAr: 'نشط', isSigned: false, createdAt: '2024-12-14', isControlled: true },
];

export function Prescriptions() {
  const { isRtl } = useRTL();
  const navigate = useNavigate();
  const [prescriptions, setPrescriptions] = useState<PrescriptionRecord[]>(MOCK_RX);
  const [showForm, setShowForm] = useState(false);

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
            {isRtl ? 'الوصفات الطبية' : 'Prescriptions'}
          </h1>
          <Button variant="primary" onClick={() => setShowForm(true)}>
            {isRtl ? 'وصفة جديدة' : 'New Prescription'}
          </Button>
        </div>

        {showForm && (
          <PrescriptionForm
            patientId="p1"
            patientName="Ahmed Ali"
            patientNameAr="أحمد علي"
            onSubmit={(data) => {
              setPrescriptions(prev => [{
                id: `rx-${Date.now()}`,
                patientName: 'Ahmed Ali',
                patientNameAr: 'أحمد علي',
                medications: data.medications.map(m => ({ name: m.medicationName, nameAr: m.medicationNameAr })),
                status: 'active',
                statusAr: 'نشط',
                isSigned: false,
                createdAt: new Date().toISOString().split('T')[0],
                isControlled: data.medications.some(m => m.medicationCode.startsWith('C-')),
              }, ...prev]);
              setShowForm(false);
            }}
            onCancel={() => setShowForm(false)}
          />
        )}

        <div className="space-y-3">
          {prescriptions.map(rx => (
            <Card key={rx.id} hover padding="md" onClick={() => {}}>
              <CardBody>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm">{rx.patientNameAr || rx.patientName}</span>
                      {rx.isControlled && <Badge variant="danger" size="xs">{isRtl ? 'مخدر' : 'Controlled'}</Badge>}
                    </div>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {rx.medications.map((med, i) => (
                        <Badge key={i} variant="default" size="sm">{isRtl ? med.nameAr : med.name}</Badge>
                      ))}
                    </div>
                    <p className="text-xs text-neutral-400 mt-1">{new Date(rx.createdAt).toLocaleDateString(isRtl ? 'ar-IQ' : 'en-US')}</p>
                  </div>
                  <div className="text-right space-y-1">
                    <Badge variant={rx.status === 'active' ? 'success' : rx.status === 'dispensed' ? 'info' : 'default'}>
                      {isRtl ? rx.statusAr : rx.status}
                    </Badge>
                    {rx.isSigned ? (
                      <Badge variant="success" size="xs">{isRtl ? 'موقع' : 'Signed'}</Badge>
                    ) : (
                      <Badge variant="warning" size="xs">{isRtl ? 'غير موقع' : 'Unsigned'}</Badge>
                    )}
                  </div>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      </div>
    </LayoutContent>
  );
}
