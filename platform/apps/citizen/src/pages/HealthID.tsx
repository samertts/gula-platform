import { useState } from 'react';
import { Button, cn } from '@gula/ui-platform';
import { useAuth } from '../contexts/AuthContext';
import { HealthCard } from '../components/HealthCard';
import { ROUTES } from '../utils/routes';

export function HealthID() {
  const { user } = useAuth();
  const [showQR, setShowQR] = useState(false);

  if (!user) return null;

  const qrData = JSON.stringify({
    id: user.id,
    nationalId: user.nationalId,
    name: user.name,
    verificationLevel: user.verificationLevel,
    ts: Date.now(),
  });

  return (
    <div className="pb-24 px-4 pt-4">
      <HealthCard user={user} qrData={showQR ? qrData : undefined} className="mb-6" />

      <div className="space-y-4">
        <Button
          fullWidth
          variant={showQR ? 'secondary' : 'primary'}
          size="lg"
          onClick={() => setShowQR(!showQR)}
          icon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <rect x="3" y="3" width="6" height="6" rx="1" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
              <rect x="15" y="3" width="6" height="6" rx="1" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
              <rect x="15" y="15" width="6" height="6" rx="1" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15h3v3H3z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 15v6" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 9v3" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h3" />
            </svg>
          }
        >
          {showQR ? 'إخفاء رمز QR' : 'عرض رمز QR'}
        </Button>

        <div className="bg-white dark:bg-neutral-800 rounded-2xl p-5 border border-neutral-200 dark:border-neutral-700 shadow-sm">
          <h3 className="text-sm font-black text-neutral-900 dark:text-neutral-50 mb-4">معلومات إضافية</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-xs text-neutral-500">حالة التحقق</span>
              <span className={cn(
                'text-xs font-bold',
                user.identityVerified ? 'text-success-600' : 'text-warning-600',
              )}>
                {user.identityVerified ? 'موثق' : 'غير موثق'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-neutral-500">مستوى التحقق</span>
              <span className="text-xs font-bold text-neutral-900 dark:text-neutral-50">
                {user.verificationLevel === 'Level_3' ? 'مستوى 3 - بيومتري' :
                 user.verificationLevel === 'Level_2' ? 'مستوى 2 - موثق' : 'مستوى 1 - أساسي'}
              </span>
            </div>
            {user.email && (
              <div className="flex justify-between">
                <span className="text-xs text-neutral-500">البريد الإلكتروني</span>
                <span className="text-xs font-bold text-neutral-900 dark:text-neutral-50">{user.email}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-xs text-neutral-500">تاريخ التسجيل</span>
              <span className="text-xs font-bold text-neutral-900 dark:text-neutral-50">
                {new Date(user.createdAt).toLocaleDateString('ar-IQ')}
              </span>
            </div>
          </div>
        </div>

        <div className="flex gap-3">
          <Button
            fullWidth
            variant="outline"
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
              </svg>
            }
          >
            مشاركة
          </Button>
          <Button
            fullWidth
            variant="outline"
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            }
          >
            حفظ
          </Button>
        </div>

        <div className="bg-primary-50 dark:bg-primary-900/20 rounded-2xl p-4 border border-primary-100 dark:border-primary-800">
          <div className="flex items-center gap-2 mb-1">
            <svg className="w-4 h-4 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-xs font-bold text-primary-700 dark:text-primary-400">معلومات الأمان</p>
          </div>
          <p className="text-[11px] text-primary-600 dark:text-primary-500 leading-relaxed">
            رمز QR يحتوي على توقيع رقمي للتحقق من هويتك. لا تشارك رمز QR إلا مع مقدمي الرعاية الصحية الموثوقين.
          </p>
        </div>
      </div>
    </div>
  );
}
