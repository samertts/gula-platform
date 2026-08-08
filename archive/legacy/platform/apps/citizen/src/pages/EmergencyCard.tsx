import { useState, useEffect } from 'react';
import { Button, Input, cn } from '@gula/ui-platform';
import { getEmergencyInfo, saveEmergencyInfo } from '../services/offline';
import { EmergencyInfo as EmergencyInfoComponent } from '../components/EmergencyInfo';
import type { EmergencyInfo, EmergencyContact } from '../types';

export function EmergencyCard() {
  const [info, setInfo] = useState<EmergencyInfo | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [saved, setSaved] = useState(false);

  const [bloodType, setBloodType] = useState('');
  const [allergies, setAllergies] = useState('');
  const [chronicConditions, setChronicConditions] = useState('');
  const [medications, setMedications] = useState('');
  const [organDonor, setOrganDonor] = useState(false);
  const [preferredHospital, setPreferredHospital] = useState('');
  const [notes, setNotes] = useState('');
  const [contacts, setContacts] = useState<EmergencyContact[]>([]);

  useEffect(() => {
    loadEmergencyInfo();
  }, []);

  async function loadEmergencyInfo() {
    try {
      const data = await getEmergencyInfo();
      if (data) {
        setInfo(data);
        setBloodType(data.bloodType);
        setAllergies(data.allergies.join(', '));
        setChronicConditions(data.chronicConditions.join(', '));
        setMedications(data.medications.join(', '));
        setOrganDonor(data.organDonor);
        setPreferredHospital(data.preferredHospital || '');
        setNotes(data.notes || '');
        setContacts(data.emergencyContacts);
      }
    } catch {} finally {
      setIsLoading(false);
    }
  }

  async function handleSave() {
    const emergencyInfo: EmergencyInfo = {
      bloodType,
      allergies: allergies.split(',').map((a) => a.trim()).filter(Boolean),
      chronicConditions: chronicConditions.split(',').map((c) => c.trim()).filter(Boolean),
      medications: medications.split(',').map((m) => m.trim()).filter(Boolean),
      organDonor,
      preferredHospital: preferredHospital || undefined,
      notes: notes || undefined,
      emergencyContacts: contacts,
    };

    await saveEmergencyInfo(emergencyInfo);
    setInfo(emergencyInfo);
    setIsEditing(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  }

  function addContact() {
    setContacts([...contacts, {
      id: `contact-${Date.now()}`,
      name: '',
      phone: '',
      relationship: '',
      isPrimary: contacts.length === 0,
    }]);
  }

  function updateContact(index: number, field: keyof EmergencyContact, value: string | boolean) {
    const updated = [...contacts];
    updated[index] = { ...updated[index], [field]: value };
    setContacts(updated);
  }

  function removeContact(index: number) {
    setContacts(contacts.filter((_, i) => i !== index));
  }

  if (isLoading) {
    return (
      <div className="pb-24 px-4 pt-4">
        <div className="bg-neutral-100 dark:bg-neutral-800 rounded-3xl h-96 animate-pulse" />
      </div>
    );
  }

  if (info && !isEditing) {
    return (
      <div className="pb-24 px-4 pt-4">
        <EmergencyInfoComponent info={info} />
        <div className="mt-4">
          <Button fullWidth size="lg" variant="secondary" onClick={() => setIsEditing(true)}>
            تعديل المعلومات
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="pb-24 px-4 pt-4">
      <div className="bg-white dark:bg-neutral-800 rounded-3xl p-6 border border-neutral-200 dark:border-neutral-700 shadow-sm">
        <h3 className="text-sm font-black text-neutral-900 dark:text-neutral-50 mb-5">
          معلومات الطوارئ
        </h3>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-neutral-500 mb-1">فصيلة الدم</label>
            <div className="flex gap-2">
              {['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map((bt) => (
                <button
                  key={bt}
                  onClick={() => setBloodType(bt)}
                  className={cn(
                    'px-4 py-2 rounded-xl text-xs font-bold transition-all',
                    bloodType === bt
                      ? 'bg-danger-500 text-white'
                      : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-500',
                  )}
                >
                  {bt}
                </button>
              ))}
            </div>
          </div>

          <Input
            label="الحساسية (مفصولة بفواصل)"
            placeholder="بنسلين, صويا, ..."
            value={allergies}
            onChange={(e) => setAllergies(e.target.value)}
          />

          <Input
            label="الحالات المزمنة (مفصولة بفواصل)"
            placeholder="سكري, ضغط, ..."
            value={chronicConditions}
            onChange={(e) => setChronicConditions(e.target.value)}
          />

          <Input
            label="الأدوية الحالية (مفصولة بفواصل)"
            placeholder="أسبيرين, ميتفورمين, ..."
            value={medications}
            onChange={(e) => setMedications(e.target.value)}
          />

          <Input
            label="المستشفى المفضل"
            placeholder="اسم المستشفى"
            value={preferredHospital}
            onChange={(e) => setPreferredHospital(e.target.value)}
          />

          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={organDonor}
              onChange={(e) => setOrganDonor(e.target.checked)}
              className="w-5 h-5 rounded border-neutral-300 text-primary-500"
              id="organ-donor"
            />
            <label htmlFor="organ-donor" className="text-sm text-neutral-700 dark:text-neutral-300">
              متبرع بالأعضاء
            </label>
          </div>

          <Input
            label="ملاحظات إضافية"
            placeholder="أي معلومات إضافية..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />

          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-neutral-500">جهات الاتصال للطوارئ</span>
              <button
                onClick={addContact}
                className="text-xs font-bold text-primary-600 dark:text-primary-400"
              >
                + إضافة
              </button>
            </div>
            {contacts.map((contact, i) => (
              <div key={contact.id} className="flex items-center gap-2 mb-2">
                <input
                  placeholder="الاسم"
                  value={contact.name}
                  onChange={(e) => updateContact(i, 'name', e.target.value)}
                  className="flex-1 px-3 py-2 text-xs rounded-xl border border-neutral-300 dark:border-neutral-600 bg-transparent"
                />
                <input
                  placeholder="رقم الهاتف"
                  value={contact.phone}
                  onChange={(e) => updateContact(i, 'phone', e.target.value)}
                  className="flex-1 px-3 py-2 text-xs rounded-xl border border-neutral-300 dark:border-neutral-600 bg-transparent"
                  inputMode="tel"
                />
                <button
                  onClick={() => removeContact(i)}
                  className="w-8 h-8 flex items-center justify-center rounded-xl hover:bg-danger-50 text-neutral-400 hover:text-danger-500"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-6 space-y-3">
          <Button fullWidth size="lg" onClick={handleSave}>
            {saved ? '✓ تم الحفظ' : 'حفظ'}
          </Button>
          {info && (
            <Button fullWidth size="lg" variant="outline" onClick={() => setIsEditing(false)}>
              إلغاء
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
