import { useState, useRef } from 'react';
import { cn } from '@gula/ui-platform';
import type { Patient } from '@/utils/types';

interface BedsideCheckProps {
  patient: Patient;
  onVerified: (method: 'qr' | 'barcode' | 'manual') => void;
  onCancel: () => void;
}

type VerificationMethod = 'qr' | 'barcode' | 'manual';

const methodIcons: Record<VerificationMethod, string> = {
  qr: '📱',
  barcode: '📋',
  manual: '✏️',
};

export function BedsideCheck({ patient, onVerified, onCancel }: BedsideCheckProps) {
  const [method, setMethod] = useState<VerificationMethod>('manual');
  const [manualId, setManualId] = useState('');
  const [error, setError] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const [scanning, setScanning] = useState(false);

  const handleManualVerify = () => {
    if (!manualId.trim()) {
      setError('يرجى إدخال رقم المريض');
      return;
    }
    if (manualId.trim() === patient.mrn) {
      onVerified('manual');
    } else {
      setError('رقم المريض غير متطابق');
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className={cn(
          'w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-3 text-3xl',
          'bg-primary-100 dark:bg-primary-900/30',
        )}>
          {methodIcons[method]}
        </div>
        <h3 className="text-lg font-bold text-neutral-900 dark:text-neutral-100">التحقق من هوية المريض</h3>
        <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
          اختر طريقة التحقق
        </p>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {(['qr', 'barcode', 'manual'] as VerificationMethod[]).map(m => (
          <button
            key={m}
            type="button"
            onClick={() => { setMethod(m); setError(''); }}
            className={cn(
              'p-3 rounded-2xl border-2 text-center transition-all',
              method === m
                ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                : 'border-neutral-200 dark:border-neutral-700 hover:border-neutral-300 dark:hover:border-neutral-600',
            )}
          >
            <span className="text-2xl block mb-1">{methodIcons[m]}</span>
            <span className={cn(
              'text-xs font-bold',
              method === m ? 'text-primary-600 dark:text-primary-400' : 'text-neutral-500',
            )}>
              {m === 'qr' ? 'QR' : m === 'barcode' ? 'باركود' : 'يدوي'}
            </span>
          </button>
        ))}
      </div>

      {method === 'manual' && (
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-bold text-neutral-600 dark:text-neutral-400 mb-2">
              أدخل رقم الملف الطبي (MRN)
            </label>
            <input
              ref={inputRef}
              type="text"
              value={manualId}
              onChange={e => { setManualId(e.target.value); setError(''); }}
              placeholder={patient.mrn}
              className="w-full px-4 py-3 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-2xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none"
              autoFocus
            />
            {error && (
              <p className="text-xs text-danger-500 mt-1">{error}</p>
            )}
          </div>

          <div className="bg-neutral-50 dark:bg-neutral-700/50 p-4 rounded-2xl">
            <p className="text-sm font-bold text-neutral-700 dark:text-neutral-300">بيانات المريض المتوقعة:</p>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
              {patient.name} • {patient.mrn} • {patient.bed}
            </p>
          </div>

          <button
            type="button"
            onClick={handleManualVerify}
            className="w-full py-3 bg-primary-500 text-white rounded-2xl font-bold text-sm hover:bg-primary-600 transition-colors"
          >
            تحقق
          </button>
        </div>
      )}

      {method !== 'manual' && (
        <div className="bg-neutral-50 dark:bg-neutral-700/50 p-6 rounded-2xl text-center">
          {scanning ? (
            <div className="space-y-3">
              <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-sm text-neutral-500 dark:text-neutral-400">جاري المسح...</p>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-neutral-500 dark:text-neutral-400">
                وجه الكاميرا نحو {method === 'qr' ? 'رمز QR' : 'الباركود'} الموجود على سوار المريض
              </p>
              <button
                type="button"
                onClick={() => setScanning(true)}
                className="px-6 py-2.5 bg-primary-500 text-white rounded-xl font-bold text-sm hover:bg-primary-600 transition-colors"
              >
                بدء المسح
              </button>
            </div>
          )}
        </div>
      )}

      <div className="flex gap-3">
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 py-2.5 bg-neutral-100 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300 rounded-2xl font-bold text-sm hover:bg-neutral-200 transition-colors"
        >
          إلغاء
        </button>
      </div>
    </div>
  );
}
