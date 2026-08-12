import { useState, useEffect } from 'react';
import { Button, Input, cn } from '@gula/ui-platform';
import { getFamilyMembers, addFamilyMember, removeFamilyMember } from '../services/family';
import { FamilyMemberCard } from '../components/FamilyMemberCard';
import type { FamilyMember } from '../types';

const relationshipOptions = [
  { value: 'spouse', label: 'زوج/زوجة' },
  { value: 'child', label: 'ابن/ابنة' },
  { value: 'parent', label: 'والد/والدة' },
  { value: 'sibling', label: 'أخ/أخت' },
  { value: 'other', label: 'آخر' },
];

export function FamilyAccounts() {
  const [members, setMembers] = useState<FamilyMember[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newName, setNewName] = useState('');
  const [newNationalId, setNewNationalId] = useState('');
  const [newRelationship, setNewRelationship] = useState('child');
  const [newDob, setNewDob] = useState('');
  const [newGender, setNewGender] = useState<'male' | 'female'>('male');
  const [error, setError] = useState('');

  useEffect(() => {
    loadMembers();
  }, []);

  async function loadMembers() {
    try {
      const data = await getFamilyMembers();
      setMembers(data);
    } catch {} finally {
      setIsLoading(false);
    }
  }

  async function handleAdd() {
    setError('');
    if (!newName.trim()) { setError('الرجاء إدخال الاسم'); return; }
    if (!newNationalId.trim()) { setError('الرجاء إدخال الرقم الوطني'); return; }

    try {
      const member = await addFamilyMember({
        nationalId: newNationalId,
        name: newName,
        relationship: newRelationship as FamilyMember['relationship'],
        dateOfBirth: newDob,
        gender: newGender,
        canViewRecords: true,
        canBookAppointments: false,
      });
      setMembers([...members, member]);
      setShowAddForm(false);
      setNewName('');
      setNewNationalId('');
      setNewRelationship('child');
      setNewDob('');
      setNewGender('male');
    } catch (err) {
      setError((err as Error).message || 'فشل إضافة العضو');
    }
  }

  async function handleRemove(id: string) {
    try {
      await removeFamilyMember(id);
      setMembers(members.filter((m) => m.id !== id));
    } catch {}
  }

  if (isLoading) {
    return (
      <div className="pb-24 px-4 pt-4 space-y-4">
        {[1, 2].map((i) => (
          <div key={i} className="bg-neutral-100 dark:bg-neutral-800 rounded-2xl h-24 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="pb-24 px-4 pt-4">
      {showAddForm ? (
        <div className="bg-white dark:bg-neutral-800 rounded-3xl p-6 border border-neutral-200 dark:border-neutral-700 shadow-sm mb-6">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-sm font-black text-neutral-900 dark:text-neutral-50">إضافة فرد جديد</h3>
            <button
              onClick={() => setShowAddForm(false)}
              className="text-xs text-neutral-500"
            >
              إلغاء
            </button>
          </div>
          <div className="space-y-4">
            <Input
              label="الاسم الكامل"
              placeholder="الاسم الثلاثي"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
            />
            <Input
              label="الرقم الوطني"
              placeholder="أدخل الرقم الوطني (14 رقم)"
              value={newNationalId}
              onChange={(e) => setNewNationalId(e.target.value.replace(/\D/g, '').slice(0, 14))}
              inputMode="numeric"
            />
            <Input
              label="تاريخ الميلاد"
              type="date"
              value={newDob}
              onChange={(e) => setNewDob(e.target.value)}
            />
            <div>
              <label className="block text-xs font-bold text-neutral-500 mb-1.5">صلة القرابة</label>
              <div className="flex gap-2 flex-wrap">
                {relationshipOptions.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setNewRelationship(opt.value)}
                    className={cn(
                      'px-4 py-2 rounded-xl text-xs font-bold',
                      newRelationship === opt.value
                        ? 'bg-primary-500 text-white'
                        : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-500',
                    )}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-xs font-bold text-neutral-500 mb-1.5">الجنس</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setNewGender('male')}
                  className={cn(
                    'flex-1 px-4 py-2 rounded-xl text-xs font-bold',
                    newGender === 'male' ? 'bg-primary-500 text-white' : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-500',
                  )}
                >
                  ذكر
                </button>
                <button
                  onClick={() => setNewGender('female')}
                  className={cn(
                    'flex-1 px-4 py-2 rounded-xl text-xs font-bold',
                    newGender === 'female' ? 'bg-primary-500 text-white' : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-500',
                  )}
                >
                  أنثى
                </button>
              </div>
            </div>
            {error && <p className="text-xs text-danger-600">{error}</p>}
            <Button fullWidth onClick={handleAdd}>
              إضافة
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-between mb-6">
          <div>
            <p className="text-xs text-neutral-500">{members.length} أفراد</p>
          </div>
          <Button size="sm" onClick={() => setShowAddForm(true)}>
            إضافة فرد
          </Button>
        </div>
      )}

      {members.length === 0 && !showAddForm ? (
        <div className="text-center py-16">
          <svg className="w-16 h-16 mx-auto text-neutral-300 dark:text-neutral-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <p className="text-sm text-neutral-500 mb-2">لا يوجد أفراد عائلة</p>
          <p className="text-[10px] text-neutral-400 mb-4">أضف أفراد عائلتك لإدارة سجلاتهم الصحية</p>
          <Button onClick={() => setShowAddForm(true)}>
            إضافة فرد العائلة
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          {members.map((member) => (
            <FamilyMemberCard
              key={member.id}
              member={member}
              onRemove={handleRemove}
            />
          ))}
        </div>
      )}
    </div>
  );
}
