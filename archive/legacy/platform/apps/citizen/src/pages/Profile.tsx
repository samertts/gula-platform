import { useState } from 'react';
import { Button, Input, cn } from '@gula/ui-platform';
import { useAuth } from '../contexts/AuthContext';
import { updateProfile } from '../services/auth';
import { ROUTES } from '../utils/routes';

export function Profile() {
  const { user, updateUser, logout } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [address, setAddress] = useState(user?.address || '');
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  if (!user) return null;

  async function handleSave() {
    setIsSaving(true);
    try {
      const updated = await updateProfile({ name, email, address });
      updateUser(updated);
      setIsEditing(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch {} finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="pb-24 px-4 pt-4">
      <div className="bg-gradient-to-br from-primary-600 to-primary-800 text-white rounded-3xl p-8 text-center mb-6 shadow-xl">
        <div className="w-24 h-24 rounded-3xl bg-white/20 flex items-center justify-center mx-auto mb-4 text-4xl font-black">
          {user.name.charAt(0)}
        </div>
        <h2 className="text-2xl font-black">{user.name}</h2>
        <p className="text-sm text-white/70 mt-1">
          {user.verificationLevel === 'Level_3' ? 'مستوى 3 - بيومتري' : user.verificationLevel === 'Level_2' ? 'مستوى 2 - موثق' : 'مستوى 1 - أساسي'}
        </p>
        <div className="flex items-center justify-center gap-2 mt-3">
          <div className={cn('w-2 h-2 rounded-full', user.identityVerified ? 'bg-success-400' : 'bg-warning-400')} />
          <span className="text-xs text-white/70">{user.identityVerified ? 'موثق' : 'غير موثق'}</span>
        </div>
      </div>

      {isEditing ? (
        <div className="bg-white dark:bg-neutral-800 rounded-3xl p-6 border border-neutral-200 dark:border-neutral-700 shadow-sm space-y-4">
          <Input label="الاسم الكامل" value={name} onChange={(e) => setName(e.target.value)} />
          <Input label="البريد الإلكتروني" value={email} onChange={(e) => setEmail(e.target.value)} inputMode="email" />
          <Input label="العنوان" value={address} onChange={(e) => setAddress(e.target.value)} />
          <div className="flex gap-3 pt-2">
            <Button fullWidth loading={isSaving} onClick={handleSave}>
              {saved ? '✓ تم الحفظ' : 'حفظ'}
            </Button>
            <Button fullWidth variant="outline" onClick={() => setIsEditing(false)}>
              إلغاء
            </Button>
          </div>
        </div>
      ) : (
        <div className="bg-white dark:bg-neutral-800 rounded-3xl p-6 border border-neutral-200 dark:border-neutral-700 shadow-sm">
          <div className="space-y-4">
            <div>
              <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest">الرقم الوطني</p>
              <p className="text-sm font-bold text-neutral-900 dark:text-neutral-50 mt-0.5" dir="ltr">
                {user.nationalId.replace(/(\d{3})(\d{3})(\d{4})(\d{4})/, '$1-$2-$3-$4')}
              </p>
            </div>
            <div>
              <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest">رقم الهاتف</p>
              <p className="text-sm font-bold text-neutral-900 dark:text-neutral-50 mt-0.5">{user.phone}</p>
            </div>
            <div>
              <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest">البريد الإلكتروني</p>
              <p className="text-sm font-bold text-neutral-900 dark:text-neutral-50 mt-0.5">{user.email || 'غير محدد'}</p>
            </div>
            <div>
              <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest">تاريخ الميلاد</p>
              <p className="text-sm font-bold text-neutral-900 dark:text-neutral-50 mt-0.5">
                {new Date(user.dateOfBirth).toLocaleDateString('ar-IQ', { year: 'numeric', month: 'long', day: 'numeric' })}
              </p>
            </div>
            {user.address && (
              <div>
                <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest">العنوان</p>
                <p className="text-sm font-bold text-neutral-900 dark:text-neutral-50 mt-0.5">{user.address}</p>
              </div>
            )}
            <div>
              <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest">تاريخ التسجيل</p>
              <p className="text-sm font-bold text-neutral-900 dark:text-neutral-50 mt-0.5">
                {new Date(user.createdAt).toLocaleDateString('ar-IQ', { year: 'numeric', month: 'long', day: 'numeric' })}
              </p>
            </div>
          </div>
          <Button fullWidth variant="secondary" className="mt-6" onClick={() => setIsEditing(true)}>
            تعديل الملف الشخصي
          </Button>
        </div>
      )}
    </div>
  );
}
