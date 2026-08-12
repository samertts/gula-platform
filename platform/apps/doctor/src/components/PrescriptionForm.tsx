import { useState, useCallback } from 'react';
import { Card, CardHeader, CardBody, Input, Button, Badge } from '@gula/ui-platform';
import { useRTL, useDebounce } from '@gula/ui-platform';
import { searchMedications, checkDrugInteractions, type DrugInteraction, type MedicationSearchResult } from '../services/prescriptions';

interface PrescriptionFormData {
  patientId: string;
  medications: PrescriptionMedicationEntry[];
  diagnosis?: string;
  diagnosisAr?: string;
  notes?: string;
  notesAr?: string;
}

interface PrescriptionMedicationEntry {
  medicationCode: string;
  medicationName: string;
  medicationNameAr: string;
  strength: string;
  form: string;
  route: string;
  dose: string;
  frequency: string;
  duration: string;
  quantity: number;
  refills: number;
  instructions: string;
  instructionsAr: string;
  substitutionAllowed: boolean;
  interactions: DrugInteraction[];
}

const frequencies = [
  { value: 'QD', label: 'Once daily', labelAr: 'مرة يومياً' },
  { value: 'BID', label: 'Twice daily', labelAr: 'مرتين يومياً' },
  { value: 'TID', label: 'Three times daily', labelAr: 'ثلاث مرات يومياً' },
  { value: 'QID', label: 'Four times daily', labelAr: 'أربع مرات يومياً' },
  { value: 'QHS', label: 'At bedtime', labelAr: 'قبل النوم' },
  { value: 'QAM', label: 'In the morning', labelAr: 'في الصباح' },
  { value: 'QPM', label: 'In the evening', labelAr: 'في المساء' },
  { value: 'PRN', label: 'As needed', labelAr: 'عند الحاجة' },
  { value: 'STAT', label: 'Immediately', labelAr: 'فوراً' },
];

const routes = [
  { value: 'PO', label: 'Oral', labelAr: 'فموي' },
  { value: 'IV', label: 'Intravenous', labelAr: 'وريدي' },
  { value: 'IM', label: 'Intramuscular', labelAr: 'عضلي' },
  { value: 'SC', label: 'Subcutaneous', labelAr: 'تحت الجلد' },
  { value: 'TOP', label: 'Topical', labelAr: 'موضعي' },
  { value: 'INH', label: 'Inhalation', labelAr: 'استنشاق' },
  { value: 'SL', label: 'Sublingual', labelAr: 'تحت اللسان' },
  { value: 'PR', label: 'Rectal', labelAr: 'شرجي' },
];

interface PrescriptionFormProps {
  patientId: string;
  patientName: string;
  patientNameAr: string;
  onSubmit: (data: PrescriptionFormData) => void;
  onCancel?: () => void;
}

export function PrescriptionForm({ patientId, patientName, patientNameAr, onSubmit, onCancel }: PrescriptionFormProps) {
  const { isRtl } = useRTL();
  const [medications, setMedications] = useState<PrescriptionMedicationEntry[]>([]);
  const [diagnosis, setDiagnosis] = useState('');
  const [diagnosisAr, setDiagnosisAr] = useState('');
  const [notes, setNotes] = useState('');
  const [notesAr, setNotesAr] = useState('');
  const [medSearch, setMedSearch] = useState('');
  const [medResults, setMedResults] = useState<MedicationSearchResult[]>([]);
  const [isSearchingMed, setIsSearchingMed] = useState(false);
  const [interactions, setInteractions] = useState<DrugInteraction[]>([]);
  const [currentMed, setCurrentMed] = useState<Partial<PrescriptionMedicationEntry>>({});

  const searchMed = useCallback(async (q: string) => {
    if (q.length < 2) { setMedResults([]); return; }
    setIsSearchingMed(true);
    try {
      const results = await searchMedications(q);
      setMedResults(results);
    } catch {
      setMedResults([]);
    } finally {
      setIsSearchingMed(false);
    }
  }, []);

  const debouncedSearchMed = useDebounce(searchMed, 300);

  const handleMedSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setMedSearch(e.target.value);
    debouncedSearchMed(e.target.value);
  };

  const selectMedication = (med: MedicationSearchResult) => {
    setCurrentMed({
      medicationCode: med.code,
      medicationName: med.name,
      medicationNameAr: med.nameAr,
      strength: med.strength,
      form: med.form,
      route: 'PO',
      dose: '',
      frequency: 'BID',
      duration: '7 days',
      quantity: 1,
      refills: 0,
      instructions: '',
      instructionsAr: '',
      substitutionAllowed: true,
      interactions: [],
    });
    setMedSearch('');
    setMedResults([]);
  };

  const addMedication = async () => {
    if (!currentMed.medicationCode || !currentMed.dose) return;

    const newMed = currentMed as PrescriptionMedicationEntry;
    setMedications(prev => [...prev, newMed]);

    try {
      const drugCheck = await checkDrugInteractions(patientId, [
        ...medications.map(m => ({ code: m.medicationCode, name: m.medicationName })),
        { code: newMed.medicationCode, name: newMed.medicationName },
      ]);
      setInteractions(drugCheck.filter(i => i.severity === 'major' || i.severity === 'contraindicated'));
    } catch {}

    setCurrentMed({});
  };

  const removeMedication = (index: number) => {
    setMedications(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      patientId,
      medications,
      diagnosis: diagnosis || undefined,
      diagnosisAr: diagnosisAr || undefined,
      notes: notes || undefined,
      notesAr: notesAr || undefined,
    });
  };

  return (
    <Card>
      <CardHeader
        title={isRtl ? 'وصفة طبية جديدة' : 'New Prescription'}
        subtitle={`${patientNameAr || patientName}`}
      />
      <CardBody>
        <form onSubmit={handleSubmit} className="space-y-6">
          {interactions.length > 0 && (
            <div className="p-4 rounded-xl bg-danger-50 dark:bg-danger-900/10 border border-danger-200 dark:border-danger-900/30">
              <p className="font-bold text-danger-700 dark:text-danger-400 mb-2">
                {isRtl ? 'تحذير: تفاعلات دوائية' : 'Warning: Drug Interactions'}
              </p>
              {interactions.map((interaction, i) => (
                <p key={i} className="text-sm text-danger-600 dark:text-danger-300">
                  {isRtl ? interaction.descriptionAr : interaction.description}
                </p>
              ))}
            </div>
          )}

          <div>
            <p className="font-medium text-neutral-700 dark:text-neutral-300 mb-3">
              {isRtl ? 'إضافة دواء' : 'Add Medication'}
            </p>
            <div className="relative mb-3">
              <Input
                value={medSearch}
                onChange={handleMedSearchChange}
                placeholder={isRtl ? 'ابحث عن دواء...' : 'Search medication...'}
              />
              {medResults.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-xl shadow-lg max-h-48 overflow-y-auto">
                  {medResults.map(med => (
                    <button
                      key={med.code}
                      type="button"
                      onClick={() => selectMedication(med)}
                      className="w-full text-right p-3 hover:bg-neutral-50 dark:hover:bg-neutral-700 border-b border-neutral-100 dark:border-neutral-700 last:border-0"
                    >
                      <p className="font-medium text-sm">{isRtl ? med.nameAr : med.name}</p>
                      <p className="text-xs text-neutral-500">{med.strength} | {med.form}</p>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {currentMed.medicationCode && (
              <div className="p-4 rounded-xl bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 space-y-3">
                <p className="font-medium text-sm text-primary-600">
                  {isRtl ? currentMed.medicationNameAr : currentMed.medicationName}
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <Input label={isRtl ? 'الجرعة' : 'Dose'} value={currentMed.dose || ''} onChange={e => setCurrentMed(p => ({ ...p, dose: e.target.value }))} placeholder="e.g., 500mg" />
                  <div>
                    <label className="block text-sm font-medium mb-1">{isRtl ? 'التكرار' : 'Frequency'}</label>
                    <select value={currentMed.frequency} onChange={e => setCurrentMed(p => ({ ...p, frequency: e.target.value }))} className="w-full rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-3 py-2 text-sm">
                      {frequencies.map(f => <option key={f.value} value={f.value}>{isRtl ? f.labelAr : f.label}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">{isRtl ? 'الطريق' : 'Route'}</label>
                    <select value={currentMed.route} onChange={e => setCurrentMed(p => ({ ...p, route: e.target.value }))} className="w-full rounded-xl border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-3 py-2 text-sm">
                      {routes.map(r => <option key={r.value} value={r.value}>{isRtl ? r.labelAr : r.label}</option>)}
                    </select>
                  </div>
                  <Input label={isRtl ? 'المدة' : 'Duration'} value={currentMed.duration || ''} onChange={e => setCurrentMed(p => ({ ...p, duration: e.target.value }))} placeholder="e.g., 7 days" />
                  <Input label={isRtl ? 'الكمية' : 'Quantity'} type="number" value={currentMed.quantity || 1} onChange={e => setCurrentMed(p => ({ ...p, quantity: parseInt(e.target.value) || 0 }))} />
                </div>
                <Input label={isRtl ? 'تعليمات (عربي)' : 'Instructions (Arabic)'} value={currentMed.instructionsAr || ''} onChange={e => setCurrentMed(p => ({ ...p, instructionsAr: e.target.value }))} />
                <Input label={isRtl ? 'تعليمات (إنجليزي)' : 'Instructions (English)'} value={currentMed.instructions || ''} onChange={e => setCurrentMed(p => ({ ...p, instructions: e.target.value }))} />
                <Button type="button" variant="secondary" onClick={addMedication}>
                  {isRtl ? 'إضافة الدواء' : 'Add Medication'}
                </Button>
              </div>
            )}
          </div>

          {medications.length > 0 && (
            <div>
              <p className="font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                {isRtl ? 'الأدوية المضافة' : 'Added Medications'} ({medications.length})
              </p>
              <div className="space-y-2">
                {medications.map((med, i) => (
                  <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-success-50 dark:bg-success-900/10 border border-success-100 dark:border-success-900/20">
                    <div>
                      <p className="font-medium text-sm">{isRtl ? med.medicationNameAr : med.medicationName}</p>
                      <p className="text-xs text-neutral-500">{med.dose} {med.frequency} | {med.duration}</p>
                    </div>
                    <button type="button" onClick={() => removeMedication(i)} className="text-danger-500 hover:text-danger-700 text-sm">
                      {isRtl ? 'حذف' : 'Remove'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <Input label={isRtl ? 'التشخيص (عربي)' : 'Diagnosis (Arabic)'} value={diagnosisAr} onChange={e => setDiagnosisAr(e.target.value)} />
          <Input label={isRtl ? 'التشخيص (إنجليزي)' : 'Diagnosis (English)'} value={diagnosis} onChange={e => setDiagnosis(e.target.value)} />
          <Input label={isRtl ? 'ملاحظات (عربي)' : 'Notes (Arabic)'} value={notesAr} onChange={e => setNotesAr(e.target.value)} />
          <Input label={isRtl ? 'ملاحظات (إنجليزي)' : 'Notes (English)'} value={notes} onChange={e => setNotes(e.target.value)} />

          <div className="flex gap-3 pt-2">
            <Button type="submit" variant="primary" disabled={medications.length === 0}>
              {isRtl ? 'حفظ الوصفة' : 'Save Prescription'}
            </Button>
            {onCancel && (
              <Button type="button" variant="ghost" onClick={onCancel}>
                {isRtl ? 'إلغاء' : 'Cancel'}
              </Button>
            )}
          </div>
        </form>
      </CardBody>
    </Card>
  );
}
