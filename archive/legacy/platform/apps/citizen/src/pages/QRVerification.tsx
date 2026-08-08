import { useState } from 'react';
import { Button, cn } from '@gula/ui-platform';
import { QRScanner } from '../components/QRScanner';

export function QRVerification() {
  const [scanResult, setScanResult] = useState<string | null>(null);
  const [scanError, setScanError] = useState<string | null>(null);
  const [verified, setVerified] = useState(false);

  function handleScan(data: string) {
    setScanResult(data);
    try {
      const parsed = JSON.parse(data);
      if (parsed.id && parsed.nationalId) {
        setVerified(true);
      } else {
        setScanError('رمز QR غير صالح');
      }
    } catch {
      setScanError('تنسيق رمز QR غير صحيح');
    }
  }

  function handleError(error: string) {
    setScanError(error);
  }

  function handleReset() {
    setScanResult(null);
    setScanError(null);
    setVerified(false);
  }

  return (
    <div className="pb-24 px-4 pt-4">
      <div className="text-center mb-6">
        <h2 className="text-lg font-black text-neutral-900 dark:text-neutral-50 mb-1">مسح رمز QR</h2>
        <p className="text-xs text-neutral-500">امسح رمز QR للتحقق من الهوية الصحية</p>
      </div>

      {!scanResult ? (
        <>
          <QRScanner
            onScan={handleScan}
            onError={handleError}
            className="mb-4"
          />
          {scanError && (
            <div className="p-4 bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 rounded-2xl mb-4">
              <p className="text-xs text-danger-600 dark:text-danger-400">{scanError}</p>
            </div>
          )}
          <div className="bg-primary-50 dark:bg-primary-900/20 rounded-2xl p-4 border border-primary-100 dark:border-primary-800">
            <div className="flex items-center gap-2 mb-1">
              <svg className="w-4 h-4 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-xs font-bold text-primary-700 dark:text-primary-400">طريقة الاستخدام</p>
            </div>
            <ol className="text-[11px] text-primary-600 dark:text-primary-500 space-y-1 list-decimal list-inside">
              <li>وجه الكاميرا نحو رمز QR على البطاقة الصحية</li>
              <li>انتظر حتى يتم التعرف على الرمز تلقائياً</li>
              <li>سيتم التحقق من صحة الهوية وعرض النتيجة</li>
            </ol>
          </div>
        </>
      ) : (
        <div className="text-center">
          {verified ? (
            <div className="bg-success-50 dark:bg-success-900/20 rounded-3xl p-8 border border-success-200 dark:border-success-800">
              <div className="w-20 h-20 bg-success-500 rounded-full flex items-center justify-center mx-auto mb-4 shadow-xl shadow-success-200 dark:shadow-success-900/30">
                <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="text-xl font-black text-success-700 dark:text-success-400 mb-2">تم التحقق!</h3>
              <p className="text-sm text-success-600 dark:text-success-500 mb-6">الهوية الصحية صحيحة وموثقة</p>
              <div className="bg-white dark:bg-neutral-800 rounded-2xl p-4 mb-6 text-right">
                <pre className="text-xs text-neutral-600 dark:text-neutral-400 whitespace-pre-wrap font-mono text-left" dir="ltr">
                  {JSON.stringify(JSON.parse(scanResult), null, 2)}
                </pre>
              </div>
              <Button onClick={handleReset} variant="outline" fullWidth>
                مسح رمز آخر
              </Button>
            </div>
          ) : (
            <div className="bg-danger-50 dark:bg-danger-900/20 rounded-3xl p-8 border border-danger-200 dark:border-danger-800">
              <div className="w-20 h-20 bg-danger-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <h3 className="text-xl font-black text-danger-700 dark:text-danger-400 mb-2">فشل التحقق</h3>
              <p className="text-sm text-danger-600 dark:text-danger-500 mb-6">
                {scanError || 'رمز QR غير صالح أو منتهي الصلاحية'}
              </p>
              <Button onClick={handleReset} variant="outline" fullWidth>
                إعادة المحاولة
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
