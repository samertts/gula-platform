import { useState, useEffect } from 'react';
import { cn } from '@gula/ui-platform';
import { useNurse } from '@/contexts/NurseContext';
import { medicationsService } from '@/services/medications';
import { MedicationVerification } from '@/components/MedicationVerification';
import type { Medication } from '@/utils/types';

type MedicationFilter = 'all' | 'scheduled' | 'given' | 'missed';

function MedicationAdministration() {
  const { user } = useNurse();
  const [medications, setMedications] = useState<Medication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedMed, setSelectedMed] = useState<Medication | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [filter, setFilter] = useState<MedicationFilter>(() => {
    const stored = localStorage.getItem('gula-nurse-med-filter');
    return stored === 'all' || stored === 'scheduled' || stored === 'given' || stored === 'missed'
      ? stored
      : 'scheduled';
  });

  useEffect(() => {
    localStorage.setItem('gula-nurse-med-filter', filter);
    loadMedications();
  }, [filter, user?.ward]);

  const loadMedications = async () => {
    setLoading(true);
    setError('');
    try {
      let list = await medicationsService.getScheduled(user?.ward);
      if (filter === 'given') list = list.filter(m => m.status === 'given');
      else if (filter === 'missed') list = list.filter(m => m.status === 'missed');
      else if (filter === 'scheduled') list = list.filter(m => m.status === 'scheduled');
      setMedications(list);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل تحميل الأدوية');
    } finally {
      setLoading(false);
    }
  };

  const handleAdminister = async (rights: Medication['rightsVerified']) => {
    if (!selectedMed) return;
    setVerifying(true);
    try {
      await medicationsService.administer(selectedMed.id, {
        administeredTime: new Date().toISOString(),
        rightsVerified: rights,
      });
      setSuccessMsg(`تم إعطاء ${selectedMed.name} للمريض ${selectedMed.patientName}`);
      setSelectedMed(null);
      loadMedications();
      setTimeout(() => setSuccessMsg(''), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل تسجيل الإعطاء');
    } finally {
      setVerifying(false);
    }
  };

  const handleHold = async (med: Medication) => {
    const reason = prompt('سبب الإيقاف المؤقت:');
    if (!reason) return;
    try {
      await medicationsService.hold(med.id, reason);
      loadMedications();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل إيقاف الدواء');
    }
  };

  const handleRefuse = async (med: Medication) => {
    const reason = prompt('سبب الرفض:');
    if (!reason) return;
    try {
      await medicationsService.recordRefusal(med.id, reason);
      loadMedications();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل تسجيل الرفض');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-black text-neutral-900 dark:text-neutral-100">إدارة الأدوية</h1>
        <button
          onClick={loadMedications}
          className="p-2 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-700 rounded-xl transition-colors"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>

      {successMsg && (
        <div className="bg-success-50 dark:bg-success-900/20 border border-success-200 dark:border-success-800 p-3 rounded-2xl">
          <p className="text-xs text-success-600 dark:text-success-400 font-bold flex items-center gap-2">
            <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" />
            </svg>
            {successMsg}
          </p>
        </div>
      )}

      <div className="flex gap-2 flex-wrap">
        {(['scheduled', 'all', 'given', 'missed'] as const).map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              'px-3 py-1.5 text-xs font-bold rounded-xl transition-colors',
              filter === f
                ? 'bg-primary-500 text-white'
                : 'bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-400 hover:bg-neutral-200 dark:hover:bg-neutral-600',
            )}
          >
            {f === 'scheduled' ? 'مجدول' : f === 'all' ? 'الكل' : f === 'given' ? 'تم الإعطاء' : 'تم الفوات'}
          </button>
        ))}
      </div>

      {error && (
        <div className="bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 p-3 rounded-2xl">
          <p className="text-xs text-danger-600 dark:text-danger-400 font-bold">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : medications.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700">
          <p className="text-4xl mb-3">💊</p>
          <p className="text-sm font-bold text-neutral-500 dark:text-neutral-400">لا توجد أدوية</p>
          <p className="text-xs text-neutral-400 dark:text-neutral-500 mt-1">
            {filter === 'scheduled' ? 'لا توجد أدوية مجدولة حالياً' : 'لا توجد أدوية في هذه القائمة'}
          </p>
        </div>
      ) : selectedMed ? (
        <MedicationVerification
          medication={selectedMed}
          onVerify={handleAdminister}
          onCancel={() => setSelectedMed(null)}
          loading={verifying}
        />
      ) : (
        <div className="space-y-3">
          {medications.map(med => (
            <button
              key={med.id}
              onClick={() => setSelectedMed(med)}
              className={cn(
                'w-full text-right bg-white dark:bg-neutral-800 rounded-2xl border-2 p-4 transition-all hover:shadow-md',
                med.status === 'scheduled' ? 'border-primary-200 dark:border-primary-800' :
                med.status === 'given' ? 'border-success-200 dark:border-success-800' :
                'border-neutral-200 dark:border-neutral-700',
              )}
            >
              <div className="flex items-start gap-3">
                <div className={cn(
                  'w-10 h-10 rounded-xl flex items-center justify-center text-lg shrink-0',
                  med.status === 'scheduled' ? 'bg-primary-100 dark:bg-primary-900/30' :
                  med.status === 'given' ? 'bg-success-100 dark:bg-success-900/30' :
                  'bg-neutral-100 dark:bg-neutral-700',
                )}>
                  💊
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-bold text-sm text-neutral-900 dark:text-neutral-100">{med.name}</p>
                    <span className={cn(
                      'text-[10px] px-1.5 py-0.5 rounded-lg font-bold',
                      med.status === 'scheduled' ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400' :
                      med.status === 'given' ? 'bg-success-100 dark:bg-success-900/30 text-success-600 dark:text-success-400' :
                      'bg-neutral-100 dark:bg-neutral-700 text-neutral-500',
                    )}>
                      {med.status === 'scheduled' ? 'مجدول' : med.status === 'given' ? 'تم الإعطاء' : med.status === 'missed' ? 'تم الفوات' : med.status === 'refused' ? 'رفض' : 'معلق'}
                    </span>
                  </div>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">{med.dosage} • {med.route}</p>
                  <p className="text-xs text-neutral-400 dark:text-neutral-500 mt-0.5">
                    {med.patientName} • السرير {med.bed} • {med.scheduledTime}
                  </p>
                </div>
                {med.status === 'scheduled' && (
                  <div className="flex gap-1 shrink-0">
                    <span onClick={(e) => { e.stopPropagation(); handleHold(med); }} className="p-1.5 text-warning-500 hover:bg-warning-50 dark:hover:bg-warning-900/20 rounded-lg" title="إيقاف مؤقت">
                      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <rect x="6" y="4" width="4" height="16" /><rect x="14" y="4" width="4" height="16" />
                      </svg>
                    </span>
                    <span onClick={(e) => { e.stopPropagation(); handleRefuse(med); }} className="p-1.5 text-danger-500 hover:bg-danger-50 dark:hover:bg-danger-900/20 rounded-lg" title="رفض">
                      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </span>
                  </div>
                )}
              </div>
              {med.notes && (
                <p className="text-[10px] text-neutral-400 dark:text-neutral-500 mt-2 mr-[52px]">ملاحظة: {med.notes}</p>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default MedicationAdministration;
