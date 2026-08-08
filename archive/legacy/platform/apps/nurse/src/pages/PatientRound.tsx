import { useState, useEffect } from 'react';
import { Card, Button, Checkbox, Input, LoadingSpinner, EmptyState, Badge } from '@gula/ui-platform';
import { useNurse } from '../contexts/NurseContext';

interface RoundPatient {
  id: string;
  name: string;
  bed: string;
  diagnosis: string;
  checkedItems: Record<string, boolean>;
  notes: string;
  completed: boolean;
}

const CHECKLIST_ITEMS = [
  'العلامات الحيوية ضمن الحدود الطبيعية',
  'تم إعطاء الأدوية في الوقت المحدد',
  'لا توجد شكاوى جديدة',
  'الضماد نظيف وجاف',
  'الأنابيب والقسطرة تعمل بشكل صحيح',
  'مستوى الوعي مستقر',
  'تم تسجيل كمية السوائل',
];

export default function PatientRound() {
  const [patients, setPatients] = useState<RoundPatient[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPatient, setSelectedPatient] = useState<string | null>(null);

  useEffect(() => {
    setTimeout(() => {
      setPatients([
        { id: '1', name: 'أحمد علي', bed: 'ICU-01', diagnosis: 'قصور قلب', checkedItems: {}, notes: '', completed: false },
        { id: '2', name: 'مريم خالد', bed: 'Ward-12', diagnosis: 'التهاب رئوي', checkedItems: {}, notes: '', completed: false },
        { id: '3', name: 'حسن كريم', bed: 'Ward-08', diagnosis: 'سكري', checkedItems: {}, notes: '', completed: false },
      ]);
      setLoading(false);
    }, 500);
  }, []);

  const toggleItem = (patientId: string, item: string) => {
    setPatients(prev => prev.map(p =>
      p.id === patientId
        ? { ...p, checkedItems: { ...p.checkedItems, [item]: !p.checkedItems[item] } }
        : p
    ));
  };

  const completeRound = (patientId: string) => {
    setPatients(prev => prev.map(p =>
      p.id === patientId ? { ...p, completed: true } : p
    ));
    setSelectedPatient(null);
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <h1 className="text-2xl font-bold">جولة المرضى</h1>
      <p className="text-gray-500">الجولة السريرية اليومية للمرضى</p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {patients.map(patient => (
          <Card key={patient.id} className={patient.completed ? 'opacity-60' : ''}>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-semibold">{patient.name}</h3>
              {patient.completed && <Badge variant="success">مكتمل</Badge>}
            </div>
            <p className="text-sm text-gray-500">سرير: {patient.bed}</p>
            <p className="text-sm text-gray-500">التشخيص: {patient.diagnosis}</p>
            {!patient.completed && (
              <Button variant="primary" size="sm" className="mt-3" onClick={() => setSelectedPatient(patient.id)}>
                بدء الجولة
              </Button>
            )}
          </Card>
        ))}
      </div>

      {selectedPatient && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-lg mx-4">
            <h2 className="text-xl font-bold mb-4">جولة المريض - {patients.find(p => p.id === selectedPatient)?.name}</h2>
            <div className="space-y-3">
              {CHECKLIST_ITEMS.map(item => (
                <label key={item} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={patients.find(p => p.id === selectedPatient)?.checkedItems[item] || false}
                    onChange={() => toggleItem(selectedPatient, item)}
                    className="w-5 h-5"
                  />
                  <span>{item}</span>
                </label>
              ))}
              <textarea
                className="w-full border rounded-lg p-2 mt-4 dark:bg-gray-700 dark:border-gray-600"
                rows={3}
                placeholder="ملاحظات إضافية..."
                value={patients.find(p => p.id === selectedPatient)?.notes || ''}
                onChange={(e) => setPatients(prev => prev.map(p => p.id === selectedPatient ? { ...p, notes: e.target.value } : p))}
              />
            </div>
            <div className="flex justify-left gap-2 mt-6">
              <Button variant="primary" onClick={() => completeRound(selectedPatient)}>إكمال الجولة</Button>
              <Button variant="ghost" onClick={() => setSelectedPatient(null)}>إلغاء</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
