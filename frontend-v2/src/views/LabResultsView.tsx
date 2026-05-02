import { Microscope, FileText, Download, CheckCircle2, AlertCircle, FileSearch, Plus, Loader2, ShieldCheck, X } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { cn } from '../lib/utils';
import { motion, AnimatePresence } from 'motion/react';
import { db, auth, handleFirestoreError } from '../firebase';
import { collection, query, onSnapshot, addDoc, serverTimestamp, orderBy, where } from 'firebase/firestore';
import { useEffect, useState } from 'react';
import { AISummary } from '../components/AISummary';
import { toast } from 'sonner';

interface LabReport {
  id?: string;
  testName: string;
  date: any;
  status: 'Normal' | 'Critical' | 'Action Required';
  findings: string;
  patientId: string;
}

export function LabResultsView() {
  const { t } = useLanguage();
  const [reports, setReports] = useState<LabReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAdding, setIsAdding] = useState(false);
  const [showSimulateModal, setShowSimulateModal] = useState(false);
  const [newTestName, setNewTestName] = useState("");

  useEffect(() => {
    if (!auth.currentUser) return;

    // We query for current user's patients' lab results
    // We filter by ownerId to match security rules
    const q = query(
      collection(db, 'lab_results'), 
      where('ownerId', '==', auth.currentUser.uid),
      orderBy('date', 'desc')
    );
    
    const unsubscribe = onSnapshot(q, (snapshot) => {
      const docs = snapshot.docs.map(doc => {
        const data = doc.data();
        return { 
          id: doc.id, 
          ...data,
          // Fallback to title if testName is missing for legacy data
          testName: data.testName || data.title || "Unknown Test"
        } as LabReport;
      });
      setReports(docs);
      setIsLoading(false);
    }, (error) => {
      handleFirestoreError(error, 'list', 'lab_results');
    });

    return () => unsubscribe();
  }, []);

  const addTestReport = async () => {
    if (!auth.currentUser) return;
    
    // Validation: Ensure testName is not empty
    if (!newTestName.trim()) {
      toast.error('Test Name is required');
      return;
    }

    setIsAdding(true);
    try {
      await addDoc(collection(db, 'lab_results'), {
        testName: newTestName.trim(),
        title: newTestName.trim(), // Keep title for legacy support
        findings: "Glucose levels stable",
        status: "Normal",
        date: serverTimestamp(),
        patientId: "TEST-001",
        ownerId: auth.currentUser.uid
      });
      setNewTestName("");
      setShowSimulateModal(false);
      toast.success('Simulation successful: Result added');
    } catch (error) {
      handleFirestoreError(error, 'create', 'lab_results');
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500 max-w-7xl mx-auto w-full">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-6 w-full">
        <div className="editorial-stack">
          <span className="text-xs font-bold uppercase tracking-[0.2em] text-indigo-600">{t.laboratoryReports}</span>
          <h2 className="font-headline text-3xl lg:text-4xl font-bold text-slate-900 mt-1 tracking-tight">Diagnostics Hub</h2>
        </div>
        <div className="flex gap-2 w-full sm:w-auto">
          <button 
            onClick={() => setShowSimulateModal(true)}
            disabled={isAdding}
            className="flex-1 sm:flex-none px-5 py-2.5 bg-indigo-600 text-white font-bold text-sm rounded-xl shadow-lg shadow-indigo-200 hover:scale-105 active:scale-95 transition-all flex items-center justify-center gap-2"
          >
            <Plus size={18} />
            Simulate Lab Data
          </button>
          <button className="flex-1 sm:flex-none px-5 py-2.5 bg-white text-slate-600 font-bold text-sm rounded-xl border border-slate-100 shadow-sm flex items-center justify-center gap-2">
            <FileSearch size={18} />
            Search Archive
          </button>
        </div>
      </div>

      {/* Simulation Modal */}
      <AnimatePresence>
        {showSimulateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowSimulateModal(false)}
              className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
            />
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="relative bg-white w-full max-w-md rounded-3xl p-8 shadow-2xl border border-slate-200"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-bold text-xl text-slate-900">Simulate Result</h3>
                <button onClick={() => setShowSimulateModal(false)} className="p-2 hover:bg-slate-50 rounded-full transition-colors">
                  <X size={20} className="text-slate-400" />
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-black uppercase text-slate-400 tracking-widest mb-1.5">{t.testName}</label>
                  <input 
                    autoFocus
                    type="text"
                    value={newTestName}
                    onChange={(e) => setNewTestName(e.target.value)}
                    placeholder="e.g. Complete Blood Count"
                    className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all font-medium"
                    onKeyDown={(e) => e.key === 'Enter' && addTestReport()}
                  />
                </div>
                
                <button 
                  onClick={addTestReport}
                  disabled={isAdding}
                  className="w-full py-4 bg-indigo-600 text-white rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-indigo-700 transition-colors"
                >
                  {isAdding ? <Loader2 className="animate-spin" size={18} /> : <Plus size={18} />}
                  Add Result
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {isLoading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="w-10 h-10 text-indigo-600 animate-spin" />
        </div>
      ) : (
        <div className="grid gap-4">
          <AnimatePresence mode="popLayout">
            {reports.map((report, i) => (
              <motion.div 
                key={report.id || i}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-all flex flex-col md:flex-row md:items-center justify-between gap-6"
              >
                <div className="flex items-center gap-6">
                  <div className={cn(
                    "w-12 h-12 rounded-xl flex items-center justify-center border",
                    report.status === 'Critical' ? 'bg-red-50 border-red-100 text-red-600' :
                    report.status === 'Action Required' ? 'bg-amber-50 border-amber-100 text-amber-600' :
                    'bg-green-50 border-green-100 text-green-600'
                  )}>
                    {report.status === 'Normal' ? <CheckCircle2 size={24} /> : <AlertCircle size={24} />}
                  </div>
                  <div>
                    <h4 className="text-base font-bold text-slate-900">{report.testName}</h4>
                    <div className="flex items-center gap-4 mt-1">
                      <span className="text-[10px] text-slate-400 font-mono tracking-tighter truncate max-w-[100px]">{report.id}</span>
                      <span className="w-1 h-1 bg-slate-200 rounded-full"></span>
                      <span className="text-[10px] text-slate-400 font-medium uppercase">
                        {report.date?.toDate ? report.date.toDate().toLocaleDateString() : 'Pending'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex-1 md:px-8 space-y-3">
                  <p className="text-xs text-slate-500 font-medium">{t.result}: <span className={cn(
                    "font-bold",
                    report.status === 'Critical' ? 'text-red-700' :
                    report.status === 'Action Required' ? 'text-amber-700' :
                    'text-green-700'
                  )}>{report.findings}</span></p>
                  <div className="flex items-center gap-3">
                    <AISummary findings={report.findings} testTitle={report.testName} />
                    <div className="flex items-center gap-1.5 px-2 py-1 bg-emerald-50 text-emerald-600 rounded-lg text-[8px] font-black uppercase tracking-tight">
                       <ShieldCheck size={10} />
                       Verified 
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <button className="flex items-center gap-2 px-4 py-2 bg-slate-50 hover:bg-indigo-600 hover:text-white text-slate-600 text-xs font-bold rounded-xl transition-all">
                    <Download size={16} />
                    {t.exportReport}
                  </button>
                  <button className="p-2 text-slate-300 hover:text-slate-600 transition-colors">
                    <FileText size={20} />
                  </button>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          {reports.length === 0 && (
            <div className="text-center py-20 bg-slate-50 rounded-3xl border-2 border-dashed border-slate-200">
              <Microscope size={48} className="mx-auto text-slate-300 mb-4" />
              <p className="text-slate-500 font-medium">No laboratory records found in the intelligence cloud.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
