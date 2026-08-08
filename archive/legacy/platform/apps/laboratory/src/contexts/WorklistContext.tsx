import { createContext, useContext, useState, useCallback, useMemo, type ReactNode } from 'react';
import type { Sample, Priority } from '@/utils/types';

interface WorklistState {
  samples: Sample[];
  isLoading: boolean;
  filterStatus: string[];
  filterPriority: Priority[];
  searchQuery: string;
}

interface WorklistContextValue extends WorklistState {
  setSamples: (samples: Sample[]) => void;
  addSample: (sample: Sample) => void;
  updateSample: (id: string, updates: Partial<Sample>) => void;
  setFilterStatus: (statuses: string[]) => void;
  setFilterPriority: (priorities: Priority[]) => void;
  setSearchQuery: (query: string) => void;
  filteredSamples: Sample[];
  pendingCount: number;
  urgentCount: number;
}

const WorklistContext = createContext<WorklistContextValue | null>(null);

export function WorklistProvider({ children }: { children: ReactNode }) {
  const [samples, setSamples] = useState<Sample[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string[]>([]);
  const [filterPriority, setFilterPriority] = useState<Priority[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  const addSample = useCallback((sample: Sample) => {
    setSamples(prev => [sample, ...prev]);
  }, []);

  const updateSample = useCallback((id: string, updates: Partial<Sample>) => {
    setSamples(prev => prev.map(s => s.id === id ? { ...s, ...updates } : s));
  }, []);

  const filteredSamples = useMemo(() => {
    let result = [...samples];

    if (filterStatus.length > 0) {
      result = result.filter(s => filterStatus.includes(s.status));
    }

    if (filterPriority.length > 0) {
      result = result.filter(s => filterPriority.includes(s.priority));
    }

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(s =>
        s.sampleId.toLowerCase().includes(q) ||
        s.patientName.toLowerCase().includes(q) ||
        s.patientId.toLowerCase().includes(q) ||
        s.barcode.toLowerCase().includes(q)
      );
    }

    return result;
  }, [samples, filterStatus, filterPriority, searchQuery]);

  const pendingCount = useMemo(
    () => samples.filter(s => !['released', 'archived', 'disposed'].includes(s.status)).length,
    [samples],
  );

  const urgentCount = useMemo(
    () => samples.filter(s => s.priority === 'urgent' || s.priority === 'stat').length,
    [samples],
  );

  const value = useMemo(() => ({
    samples,
    isLoading,
    filterStatus,
    filterPriority,
    searchQuery,
    setSamples,
    addSample,
    updateSample,
    setFilterStatus,
    setFilterPriority,
    setSearchQuery,
    filteredSamples,
    pendingCount,
    urgentCount,
  }), [samples, isLoading, filterStatus, filterPriority, searchQuery, filteredSamples, pendingCount, urgentCount]);

  return <WorklistContext.Provider value={value}>{children}</WorklistContext.Provider>;
}

export function useWorklist() {
  const ctx = useContext(WorklistContext);
  if (!ctx) throw new Error('useWorklist must be used within WorklistProvider');
  return ctx;
}
