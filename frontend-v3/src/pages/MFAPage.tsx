import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { auth } from '@/api/endpoints';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
import { Fingerprint, Smartphone, Key, RefreshCw } from 'lucide-react';

export function MFAPage() {
  const { t } = useTranslation();
  const [totpToken, setTotpToken] = useState('');
  const [setupData, setSetupData] = useState<any>(null);

  const { data: mfaStatus, refetch } = useQuery({
    queryKey: ['mfa-status'],
    queryFn: () => auth.mfaStatus(),
  });

  const setupMutation = useMutation({
    mutationFn: () => auth.mfaSetup(),
    onSuccess: (data) => setSetupData(data),
  });

  const verifyMutation = useMutation({
    mutationFn: () => auth.mfaVerify(totpToken),
    onSuccess: () => {
      toast.success(t('success'));
      setSetupData(null);
      setTotpToken('');
      refetch();
    },
    onError: (err: any) => toast.error(err.message),
  });

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-on-surface flex items-center gap-2">
          <Fingerprint className="h-6 w-6" />
          {t('mfa')}
        </h1>
      </div>

      <div className="rounded-xl border border-outline bg-surface overflow-hidden">
        <div className="px-6 py-4 border-b border-outline">
          <h3 className="font-semibold text-on-surface">{t('status')}</h3>
        </div>
        <div className="p-6 space-y-3">
          {mfaStatus ? (
            <div className="space-y-2">
              {Array.isArray(mfaStatus?.devices) && mfaStatus.devices.map((d: any) => (
                <div key={d.id} className="flex items-center justify-between p-3 rounded-lg bg-surface-container-low">
                  <div className="flex items-center gap-3">
                    <Smartphone className="h-5 w-5 text-on-surface-variant" />
                    <div>
                      <p className="text-sm font-medium text-on-surface">{d.device_name || d.device_type}</p>
                      <p className="text-xs text-on-surface-variant">{d.device_type}</p>
                    </div>
                  </div>
                  <span className="text-xs text-success">{t('active')}</span>
                </div>
              ))}
              {(!mfaStatus?.devices || mfaStatus.devices.length === 0) && (
                <p className="text-sm text-on-surface-variant">{t('noMfaDevices', 'لا توجد أجهزة MFA')}</p>
              )}
            </div>
          ) : (
            <div className="animate-pulse h-16 rounded-lg bg-surface-container-high" />
          )}
        </div>
      </div>

      {setupData ? (
        <div className="rounded-xl border border-outline bg-surface overflow-hidden">
          <div className="px-6 py-4 border-b border-outline">
            <h3 className="font-semibold text-on-surface">{t('totp')}</h3>
          </div>
          <div className="p-6 space-y-4">
            {setupData.secret && (
              <div className="p-4 rounded-lg bg-surface-container-low">
                <p className="text-xs text-on-surface-variant mb-1">{t('secret', 'السر')}:</p>
                <p className="text-sm font-mono font-bold tracking-wider">{setupData.secret}</p>
              </div>
            )}
            {setupData.uri && (
              <div className="p-4 rounded-lg bg-surface-container-low">
                <p className="text-xs text-on-surface-variant mb-1">URI:</p>
                <p className="text-xs font-mono break-all">{setupData.uri}</p>
              </div>
            )}
            {setupData.backup_codes && (
              <div>
                <p className="text-xs text-on-surface-variant mb-2">{t('backupCodes')}:</p>
                <div className="grid grid-cols-2 gap-2">
                  {setupData.backup_codes.map((code: string, i: number) => (
                    <code key={i} className="p-2 rounded bg-surface-container-high text-xs font-mono text-center">{code}</code>
                  ))}
                </div>
              </div>
            )}
            <div className="flex gap-2">
              <Input
                label={t('totp', 'رمز TOTP')}
                value={totpToken}
                onChange={(e) => setTotpToken(e.target.value)}
                placeholder="000000"
              />
              <Button className="self-end" onClick={() => verifyMutation.mutate()} isLoading={verifyMutation.isPending}>
                {t('verify')}
              </Button>
            </div>
          </div>
        </div>
      ) : (
        <Button onClick={() => setupMutation.mutate()} isLoading={setupMutation.isPending}>
          <Key className="h-4 w-4" />
          {t('setupMfa', 'إعداد MFA')}
        </Button>
      )}
    </div>
  );
}
