import { useState } from 'react';
import { Card, CardHeader, CardBody, Button, Badge, LayoutContent } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import { SignaturePad } from '../components/SignaturePad';

interface PendingDocument {
  id: string;
  title: string;
  titleAr: string;
  patientName: string;
  patientNameAr: string;
  type: string;
  typeAr: string;
  createdAt: string;
}

const MOCK_PENDING: PendingDocument[] = [
  { id: 'pd1', title: 'Discharge Summary', titleAr: 'ملخص خروج', patientName: 'Ahmed Ali', patientNameAr: 'أحمد علي', type: 'discharge_summary', typeAr: 'ملخص خروج', createdAt: '2024-12-15' },
  { id: 'pd2', title: 'Prescription #RX-2024-0042', titleAr: 'وصفة طبية #RX-2024-0042', patientName: 'Sara Mohammed', patientNameAr: 'سارة محمد', type: 'prescription', typeAr: 'وصفة طبية', createdAt: '2024-12-14' },
  { id: 'pd3', title: 'Clinical Note - Follow Up', titleAr: 'ملاحظة سريرية - متابعة', patientName: 'Hassan Ibrahim', patientNameAr: 'حسن إبراهيم', type: 'clinical_note', typeAr: 'ملاحظة سريرية', createdAt: '2024-12-13' },
];

const SIGNED_DOCUMENTS: PendingDocument[] = [
  { id: 'sd1', title: 'Prescription #RX-2024-0030', titleAr: 'وصفة طبية #RX-2024-0030', patientName: 'Noor Khalid', patientNameAr: 'نور خالد', type: 'prescription', typeAr: 'وصفة طبية', createdAt: '2024-12-10' },
];

export function DigitalSignature() {
  const { isRtl } = useRTL();
  const [pendingDocs] = useState(MOCK_PENDING);
  const [signedDocs] = useState(SIGNED_DOCUMENTS);
  const [activeDoc, setActiveDoc] = useState<PendingDocument | null>(null);
  const [signatureData, setSignatureData] = useState<string | null>(null);

  const handleSign = (sigData: string) => {
    setSignatureData(sigData);
  };

  const handleSubmitSignature = () => {
    if (!signatureData || !activeDoc) return;
    setActiveDoc(null);
    setSignatureData(null);
  };

  const typeIcons: Record<string, string> = {
    prescription: '💊',
    clinical_note: '📝',
    discharge_summary: '📋',
    lab_order: '🔬',
    radiology_order: '📡',
    referral: '🔄',
    consent_form: '📄',
  };

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
            {isRtl ? 'التوقيع الرقمي' : 'Digital Signature'}
          </h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            {isRtl ? 'توقيع المستندات السريرية إلكترونياً' : 'Electronically sign clinical documents'}
          </p>
        </div>

        {activeDoc ? (
          <div className="space-y-4">
            <Card>
              <CardHeader
                title={isRtl ? activeDoc.titleAr : activeDoc.title}
                subtitle={`${isRtl ? activeDoc.patientNameAr : activeDoc.patientName}`}
                action={
                  <Button variant="ghost" size="sm" onClick={() => setActiveDoc(null)}>
                    {isRtl ? 'رجوع' : 'Back'}
                  </Button>
                }
              />
              <CardBody>
                <div className="p-4 rounded-xl bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 mb-4">
                  <p className="text-xs text-neutral-500 mb-1">{isRtl ? 'المستند' : 'Document'}: {isRtl ? activeDoc.typeAr : activeDoc.type}</p>
                  <p className="text-xs text-neutral-500">{isRtl ? 'التاريخ' : 'Date'}: {activeDoc.createdAt}</p>
                  <div className="mt-3 p-3 bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700">
                    <p className="text-sm text-neutral-700 dark:text-neutral-300">
                      {isRtl
                        ? `أقر أنا الدكتور بأن المعلومات الواردة في هذا المستند صحيحة وكاملة.`
                        : 'I, the doctor, confirm that the information in this document is accurate and complete.'}
                    </p>
                  </div>
                </div>

                <SignaturePad
                  onSave={handleSign}
                  onClear={() => setSignatureData(null)}
                />

                {signatureData && (
                  <div className="mt-4">
                    <Button variant="primary" fullWidth onClick={handleSubmitSignature}>
                      {isRtl ? 'تأكيد التوقيع' : 'Confirm Signature'}
                    </Button>
                  </div>
                )}
              </CardBody>
            </Card>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader title={isRtl ? 'المستندات المعلقة' : 'Pending Documents'} subtitle={`${pendingDocs.length} ${isRtl ? 'مستند' : 'documents'}`} />
              <CardBody>
                {pendingDocs.length === 0 ? (
                  <p className="text-sm text-neutral-500 text-center py-4">{isRtl ? 'لا توجد مستندات معلقة' : 'No pending documents'}</p>
                ) : (
                  <div className="space-y-2">
                    {pendingDocs.map(doc => (
                      <button
                        key={doc.id}
                        onClick={() => setActiveDoc(doc)}
                        className="w-full p-3 rounded-xl bg-neutral-50 dark:bg-neutral-900 hover:bg-neutral-100 dark:hover:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 flex items-center gap-3 transition-colors"
                      >
                        <span className="text-xl">{typeIcons[doc.type] || '📄'}</span>
                        <div className="flex-1 text-right">
                          <p className="font-medium text-sm">{isRtl ? doc.titleAr : doc.title}</p>
                          <p className="text-xs text-neutral-500">{isRtl ? doc.patientNameAr : doc.patientName}</p>
                        </div>
                        <Badge variant="warning" size="sm">{isRtl ? 'معلق' : 'Pending'}</Badge>
                      </button>
                    ))}
                  </div>
                )}
              </CardBody>
            </Card>

            <Card>
              <CardHeader title={isRtl ? 'المستندات الموقعة' : 'Signed Documents'} subtitle={`${signedDocs.length} ${isRtl ? 'مستند' : 'documents'}`} />
              <CardBody>
                {signedDocs.length === 0 ? (
                  <p className="text-sm text-neutral-500 text-center py-4">{isRtl ? 'لا توجد مستندات موقعة' : 'No signed documents'}</p>
                ) : (
                  <div className="space-y-2">
                    {signedDocs.map(doc => (
                      <div key={doc.id} className="p-3 rounded-xl bg-success-50 dark:bg-success-900/10 border border-success-200 dark:border-success-900/20 flex items-center gap-3">
                        <span className="text-xl">{typeIcons[doc.type] || '📄'}</span>
                        <div className="flex-1 text-right">
                          <p className="font-medium text-sm">{isRtl ? doc.titleAr : doc.title}</p>
                          <p className="text-xs text-neutral-500">{isRtl ? doc.patientNameAr : doc.patientName}</p>
                        </div>
                        <Badge variant="success" size="sm">{isRtl ? 'موقع' : 'Signed'}</Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardBody>
            </Card>
          </div>
        )}
      </div>
    </LayoutContent>
  );
}
