import { useState, useEffect } from 'react';
import { cn } from '@gula/ui-platform';
import { useNurse } from '@/contexts/NurseContext';
import { patientsService } from '@/services/patients';
import { BedsideCheck } from '@/components/BedsideCheck';
import type { Patient } from '@/utils/types';

function BedsideVerification() {
  const { user } = useNurse();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [verified, setVerified] = useState(false);
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadPatients();
  }, [user?.ward]);

  const loadPatients = async () => {
    try {
      const list = await patientsService.getList(user?.ward);
      setPatients(list);
    } catch {
      setError('فشل تحميل قائمة المرضى');
    } finally {
      setLoading(false);
    }
  };

  const handleVerified = async (method: 'qr' | 'barcode' | 'manual') => {
    if (!selectedPatient) return;
    try {
      const result = await patientsService.verifyBedside(selectedPatient.id, method, selectedPatient.mrn);
      if (result.verified) {
        setVerified(true);
        setTimeout(() => {
          setVerified(false);
          setSelectedPatient(null);
        }, 3000);
      }
    } catch {
      setError('فشل التحقق من هوية المريض');
    }
  };

  const filteredPatients = patients.filter(p =>
    !search || p.name.includes(search) || p.mrn.includes(search) || p.bed.includes(search)
  );

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-black text-neutral-900 dark:text-neutral-100">التحقق بجانب السرير</h1>

      {verified && (
        <div className="bg-success-50 dark:bg-success-900/20 border border-success-200 dark:border-success-800 p-4 rounded-2xl text-center">
          <p className="text-2xl mb-2">✅</p>
          <p className="text-sm font-bold text-success-600 dark:text-success-400">تم التحقق بنجاح</p>
          <p className="text-xs text-success-500 mt-0.5">{selectedPatient?.name}</p>
        </div>
      )}

      {error && (
        <div className="bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 p-3 rounded-2xl">
          <p className="text-xs text-danger-600 dark:text-danger-400 font-bold">{error}</p>
        </div>
      )}

      {selectedPatient && !verified ? (
        <BedsideCheck
          patient={selectedPatient}
          onVerified={handleVerified}
          onCancel={() => { setSelectedPatient(null); setError(''); }}
        />
      ) : (
        <>
          <div className="relative">
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="بحث عن مريض بالاسم أو MRN..."
              className="w-full px-4 py-2.5 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none pr-10"
            />
            <svg className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
            </svg>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : filteredPatients.length === 0 ? (
            <div className="text-center py-12 bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700">
              <p className="text-4xl mb-3">🔍</p>
              <p className="text-sm font-bold text-neutral-500 dark:text-neutral-400">لا توجد نتائج</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredPatients.map(p => (
                <button
                  key={p.id}
                  onClick={() => setSelectedPatient(p)}
                  className="w-full text-right bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 p-4 hover:shadow-md transition-all"
                >
                  <div className="flex items-center gap-3">
                    <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-sm', p.gender === 'أنثى' ? 'bg-pink-500' : 'bg-blue-500')}>
                      {p.name.charAt(0)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-bold text-neutral-900 dark:text-neutral-100">{p.name}</p>
                      <p className="text-xs text-neutral-500 dark:text-neutral-400">{p.mrn} • السرير {p.bed}</p>
                    </div>
                    <svg className="w-4 h-4 text-neutral-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M9 18l6-6-6-6" />
                    </svg>
                  </div>
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default BedsideVerification;
