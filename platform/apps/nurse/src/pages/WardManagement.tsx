import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { cn } from '@gula/ui-platform';
import { useNurse } from '@/contexts/NurseContext';
import { patientsService } from '@/services/patients';
import { WardMap } from '@/components/WardMap';
import { PatientAssignCard } from '@/components/PatientAssignCard';
import type { Patient, BedAssignment } from '@/utils/types';
import { ROUTES } from '@/utils/routes';

export function WardManagement() {
  const navigate = useNavigate();
  const { user, selectedWard, setSelectedWard } = useNurse();
  const [beds, setBeds] = useState<BedAssignment[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [view, setView] = useState<'map' | 'list'>('map');
  const [search, setSearch] = useState('');

  const ward = selectedWard || user?.ward || '';
  const filteredPatients = patients.filter(p =>
    !search || p.name.includes(search) || p.mrn.includes(search) || p.diagnosis.includes(search)
  );

  useEffect(() => {
    if (ward) loadWardData();
  }, [ward]);

  const loadWardData = async () => {
    setLoading(true);
    setError('');
    try {
      const [bedData, patientData] = await Promise.all([
        patientsService.getBedAssignments(ward),
        patientsService.getList(ward),
      ]);
      setBeds(bedData);
      setPatients(patientData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'فشل تحميل بيانات الجناح');
    } finally {
      setLoading(false);
    }
  };

  const handleBedClick = (bed: BedAssignment) => {
    if (bed.status === 'occupied' && bed.patientId) {
      navigate(`/patient/${bed.patientId}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-black text-neutral-900 dark:text-neutral-100">إدارة الجناح</h1>
        <div className="flex gap-1 bg-neutral-100 dark:bg-neutral-700 rounded-xl p-1">
          <button onClick={() => setView('map')} className={cn('px-3 py-1.5 text-xs font-bold rounded-lg transition-colors', view === 'map' ? 'bg-white dark:bg-neutral-600 text-neutral-900 dark:text-neutral-100 shadow-sm' : 'text-neutral-500')}>
            خريطة
          </button>
          <button onClick={() => setView('list')} className={cn('px-3 py-1.5 text-xs font-bold rounded-lg transition-colors', view === 'list' ? 'bg-white dark:bg-neutral-600 text-neutral-900 dark:text-neutral-100 shadow-sm' : 'text-neutral-500')}>
            قائمة
          </button>
        </div>
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="بحث عن مريض..."
          className="flex-1 px-4 py-2.5 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-sm text-neutral-900 dark:text-neutral-100 placeholder-neutral-400 focus:border-primary-500 focus:outline-none"
        />
        <button onClick={loadWardData} className="p-2.5 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-xl text-neutral-400 hover:text-neutral-600 transition-colors">
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
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
      ) : view === 'map' ? (
        beds.length === 0 ? (
          <div className="text-center py-12 bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700">
            <p className="text-4xl mb-3">🏥</p>
            <p className="text-sm font-bold text-neutral-500 dark:text-neutral-400">لا توجد أسرة في هذا الجناح</p>
          </div>
        ) : (
          <div className="bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700 p-4">
            <WardMap beds={beds} onBedClick={handleBedClick} />
          </div>
        )
      ) : filteredPatients.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-neutral-800 rounded-2xl border border-neutral-200 dark:border-neutral-700">
          <p className="text-4xl mb-3">👥</p>
          <p className="text-sm font-bold text-neutral-500 dark:text-neutral-400">{search ? 'لا توجد نتائج للبحث' : 'لا يوجد مرضى في هذا الجناح'}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredPatients.map(patient => (
            <PatientAssignCard
              key={patient.id}
              patient={patient}
              onClick={() => navigate(`/patient/${patient.id}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
