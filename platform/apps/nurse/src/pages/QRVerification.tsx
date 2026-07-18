import { useState } from 'react';
import { cn } from '@gula/ui-platform';
import { patientsService } from '@/services/patients';
import type { Patient } from '@/utils/types';

export function QRVerification() {
  const [scanning, setScanning] = useState(false);
  const [qrCode, setQrCode] = useState('');
  const [patient, setPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [verified, setVerified] = useState(false);

  const handleVerify = async () => {
    if (!qrCode.trim()) {
      setError('يرجى إدخال رمز QR');
      return;
    }
    setLoading(true);
    setError('');
    setVerified(false);
    try {
      const result = await patientsService.verifyBedside(qrCode.trim(), 'qr', qrCode.trim());
      if (result.verified) {
        setPatient(result.patient);
        setVerified(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل التحقق من رمز QR');
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setQrCode('');
    setPatient(null);
    setVerified(false);
    setError('');
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-black text-neutral-900 dark:text-neutral-100">التحقق بـ QR</h1>

      <div className="bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 p-6 text-center">
        <div className={cn(
          'w-24 h-24 mx-auto mb-4 rounded-2xl flex items-center justify-center text-4xl transition-all',
          verified ? 'bg-success-100 dark:bg-success-900/30' : scanning ? 'bg-primary-100 dark:bg-primary-900/30' : 'bg-neutral-100 dark:bg-neutral-700',
        )}>
          {verified ? '✅' : scanning ? (
            <div className="w-10 h-10 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
          ) : '📱'}
        </div>

        {!verified ? (
          <>
            <p className="text-sm text-neutral-500 dark:text-neutral-400 mb-1">التحقق من هوية المريض عبر QR</p>
            <p className="text-xs text-neutral-400 dark:text-neutral-500 mb-4">امسح رمز QR الموجود على سوار المريض</p>

            <div className="max-w-sm mx-auto space-y-3">
              <input
                type="text"
                value={qrCode}
                onChange={e => { setQrCode(e.target.value); setError(''); }}
                placeholder="أدخل رمز QR أو استخدم الكاميرا..."
                className="w-full px-4 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none ltr:text-left"
                dir="ltr"
              />

              <div className="flex gap-2">
                <button
                  onClick={() => setScanning(true)}
                  className="flex-1 py-2.5 bg-primary-500 text-white rounded-xl font-bold text-sm hover:bg-primary-600 transition-colors"
                >
                  فتح الكاميرا
                </button>
                <button
                  onClick={handleVerify}
                  disabled={loading || !qrCode.trim()}
                  className="flex-1 py-2.5 bg-success-500 text-white rounded-xl font-bold text-sm hover:bg-success-600 transition-colors disabled:opacity-50"
                >
                  {loading ? 'جاري التحقق...' : 'تحقق'}
                </button>
              </div>
            </div>
          </>
        ) : patient && (
          <div className="space-y-4">
            <p className="text-sm font-bold text-success-600 dark:text-success-400">تم التحقق بنجاح ✓</p>
            <div className="bg-white dark:bg-neutral-700 rounded-xl p-4 text-right max-w-sm mx-auto border border-success-200 dark:border-success-800">
              <div className="flex items-center gap-3 mb-3">
                <div className={cn('w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-lg', patient.gender === 'أنثى' ? 'bg-pink-500' : 'bg-blue-500')}>
                  {patient.name.charAt(0)}
                </div>
                <div>
                  <p className="font-bold text-neutral-900 dark:text-neutral-100">{patient.name}</p>
                  <p className="text-xs text-neutral-500">{patient.mrn}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div><span className="text-neutral-400">السرير:</span> <span className="font-bold text-neutral-700 dark:text-neutral-300">{patient.bed}</span></div>
                <div><span className="text-neutral-400">العمر:</span> <span className="font-bold text-neutral-700 dark:text-neutral-300">{patient.age} سنة</span></div>
                <div className="col-span-2"><span className="text-neutral-400">التشخيص:</span> <span className="font-bold text-neutral-700 dark:text-neutral-300">{patient.diagnosis}</span></div>
              </div>
            </div>
            <button onClick={reset} className="px-6 py-2.5 bg-primary-500 text-white rounded-xl font-bold text-sm hover:bg-primary-600 transition-colors">
              تحقق من مريض آخر
            </button>
          </div>
        )}

        {error && (
          <div className="mt-4 bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 p-3 rounded-xl">
            <p className="text-xs text-danger-600 dark:text-danger-400 font-bold">{error}</p>
          </div>
        )}
      </div>

      {scanning && !verified && (
        <div className="bg-neutral-900/95 fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-neutral-800 rounded-3xl p-6 max-w-sm w-full text-center">
            <div className="w-48 h-48 mx-auto mb-4 border-2 border-dashed border-primary-500 rounded-2xl flex items-center justify-center">
              <div className="w-32 h-32 border-2 border-primary-500 rounded-lg relative">
                <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-primary-500" />
                <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-primary-500" />
                <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-primary-500" />
                <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-primary-500" />
              </div>
            </div>
            <p className="text-sm text-neutral-500 dark:text-neutral-400 mb-4">وجه الكاميرا نحو رمز QR</p>
            <button onClick={() => setScanning(false)} className="px-6 py-2.5 bg-danger-500 text-white rounded-xl font-bold text-sm hover:bg-danger-600 transition-colors">
              إلغاء
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
