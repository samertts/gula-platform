import { useState, useEffect, useRef } from 'react';
import { cn } from '@gula/ui-platform';
import { medicationsService } from '@/services/medications';
import { patientsService } from '@/services/patients';
import type { Medication, Patient } from '@/utils/types';

type ScanType = 'medication' | 'patient';

export function BarcodeScanning() {
  const [scanType, setScanType] = useState<ScanType>('medication');
  const [code, setCode] = useState('');
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState<Medication | Patient | null>(null);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<string[]>(() => {
    return JSON.parse(localStorage.getItem('gula-nurse-barcode-history') || '[]').slice(0, 20);
  });
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, [scanType]);

  const handleScan = async () => {
    if (!code.trim()) {
      setError('يرجى إدخال أو مسح الباركود');
      return;
    }
    setScanning(true);
    setError('');
    setResult(null);

    try {
      if (scanType === 'medication') {
        const med = await medicationsService.verifyBarcode(code.trim());
        setResult(med);
      } else {
        const patients = await patientsService.search(code.trim());
        if (patients.length > 0) {
          setResult(patients[0]);
        } else {
          setError('لم يتم العثور على مريض بهذا الباركود');
        }
      }
      const newHistory = [code.trim(), ...history.filter(h => h !== code.trim())].slice(0, 20);
      setHistory(newHistory);
      localStorage.setItem('gula-nurse-barcode-history', JSON.stringify(newHistory));
      setCode('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل قراءة الباركود');
    } finally {
      setScanning(false);
    }
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem('gula-nurse-barcode-history');
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-black text-neutral-900 dark:text-neutral-100">مسح الباركود</h1>

      <div className="flex gap-2 bg-neutral-100 dark:bg-neutral-700 rounded-xl p-1">
        {(['medication', 'patient'] as ScanType[]).map(t => (
          <button
            key={t}
            onClick={() => { setScanType(t); setResult(null); setError(''); }}
            className={cn(
              'flex-1 py-2 text-xs font-bold rounded-lg transition-colors',
              scanType === t
                ? 'bg-white dark:bg-neutral-600 text-neutral-900 dark:text-neutral-100 shadow-sm'
                : 'text-neutral-500',
            )}
          >
            {t === 'medication' ? 'دواء' : 'مريض'}
          </button>
        ))}
      </div>

      <div className="bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 p-6 text-center">
        <div className={cn(
          'w-24 h-24 mx-auto mb-4 rounded-2xl flex items-center justify-center text-3xl transition-colors',
          scanning ? 'bg-primary-100 dark:bg-primary-900/30' : 'bg-neutral-100 dark:bg-neutral-700',
        )}>
          {scanning ? (
            <div className="w-10 h-10 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
          ) : '📷'}
        </div>
        <p className="text-sm text-neutral-500 dark:text-neutral-400 mb-4">
          وجه الكاميرا نحو الباركود أو أدخل الرمز يدوياً
        </p>

        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={code}
            onChange={e => { setCode(e.target.value); setError(''); }}
            onKeyDown={e => e.key === 'Enter' && handleScan()}
            placeholder="أدخل رمز الباركود..."
            className="flex-1 px-4 py-2.5 bg-neutral-50 dark:bg-neutral-700 border-2 border-neutral-200 dark:border-neutral-600 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none ltr:text-left"
            dir="ltr"
          />
          <button
            onClick={handleScan}
            disabled={scanning}
            className="px-5 py-2.5 bg-primary-500 text-white rounded-xl font-bold text-sm hover:bg-primary-600 transition-colors disabled:opacity-50"
          >
            {scanning ? '...' : 'بحث'}
          </button>
        </div>

        {error && (
          <div className="mt-4 bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 p-3 rounded-xl">
            <p className="text-xs text-danger-600 dark:text-danger-400 font-bold">{error}</p>
          </div>
        )}
      </div>

      {result && (
        <div className="bg-success-50 dark:bg-success-900/20 border border-success-200 dark:border-success-800 rounded-2xl p-4">
          <p className="text-xs text-success-600 dark:text-success-400 font-bold mb-2">تم العثور على:</p>
          {'name' in result && 'dosage' in result ? (
            <div>
              <p className="font-bold text-neutral-900 dark:text-neutral-100">{result.name}</p>
              <p className="text-xs text-neutral-500">{result.dosage} • {result.route}</p>
              <p className="text-xs text-neutral-400">{result.patientName} • السرير {result.bed}</p>
            </div>
          ) : (
            <div>
              <p className="font-bold text-neutral-900 dark:text-neutral-100">{result.name}</p>
              <p className="text-xs text-neutral-500">MRN: {result.mrn} • السرير {result.bed}</p>
              <p className="text-xs text-neutral-400">{result.diagnosis}</p>
            </div>
          )}
        </div>
      )}

      {history.length > 0 && (
        <div className="bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold text-sm text-neutral-700 dark:text-neutral-300">آخر عمليات المسح</h3>
            <button onClick={clearHistory} className="text-[10px] text-danger-500 font-bold hover:text-danger-600">مسح</button>
          </div>
          <div className="space-y-1.5">
            {history.map((h, i) => (
              <button
                key={`${h}-${i}`}
                onClick={() => { setCode(h); }}
                className="w-full text-left px-3 py-2 bg-neutral-50 dark:bg-neutral-700/50 rounded-xl text-xs text-neutral-500 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-700 transition-colors ltr:text-left font-mono"
                dir="ltr"
              >
                {h}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
