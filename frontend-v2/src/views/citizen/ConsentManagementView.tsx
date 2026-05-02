import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Shield, Eye, EyeOff, Lock, UserCheck, 
  History as HistoryIcon, Settings2, AlertTriangle, CheckCircle2,
  Stethoscope, Beaker, Plus, X, Clock, Calendar,
  Activity as ActivityIcon, FileText, Loader2
} from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { cn } from '../../lib/utils';
import { PermissionType, ConsentDuration, ConsentRecord } from '../../types/domain';
import { auth, db, handleFirestoreError } from '../../firebase';
import { 
  collection, 
  query, 
  where, 
  onSnapshot, 
  addDoc, 
  updateDoc, 
  doc, 
  serverTimestamp,
  deleteDoc,
  Timestamp
} from 'firebase/firestore';

export const ConsentManagementView: React.FC = () => {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<'active' | 'history'>('active');
  const [showGrantModal, setShowGrantModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  
  const [consents, setConsents] = useState<ConsentRecord[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [selectedPermissions, setSelectedPermissions] = useState<PermissionType[]>([]);
  const [selectedDuration, setSelectedDuration] = useState<ConsentDuration>('1_month');
  const [purposeOfUse, setPurposeOfUse] = useState<'clinical' | 'research'>('clinical');
  const [targetSearch, setTargetSearch] = useState('');
  const [selectedProvider, setSelectedProvider] = useState<{id: string, name: string} | null>(null);

  const mockProviders = [
    { id: 'PROV-001', name: 'Al-Kindi General Hospital', type: 'clinical' },
    { id: 'PROV-002', name: 'Babylon Research Institute', type: 'research' },
    { id: 'PROV-003', name: 'Basra Oncology Center', type: 'clinical' },
    { id: 'PROV-004', name: 'National Bio-Data Project', type: 'research' },
  ];

  const filteredTargets = mockProviders.filter(p => 
    p.type === purposeOfUse && 
    p.name.toLowerCase().includes(targetSearch.toLowerCase())
  );

  useEffect(() => {
    const user = auth.currentUser;
    if (!user) return;

    const q = query(
      collection(db, 'consents'),
      where('citizenId', '==', user.uid)
    );

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const data = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      })) as ConsentRecord[];
      setConsents(data);
      setIsLoading(false);
    }, (error) => {
      handleFirestoreError(error, 'list', 'consents');
    });

    // Fetch audit logs (events)
    const qEvents = query(
      collection(db, 'events'),
      where('senderId', '==', user.uid)
    );

    const unsubscribeEvents = onSnapshot(qEvents, (snapshot) => {
      const data = snapshot.docs
        .map(doc => ({
          id: doc.id,
          ...doc.data()
        }))
        .filter((e: any) => e.type === 'consent_granted' || e.type === 'consent_revoked')
        .sort((a: any, b: any) => {
          const tA = a.createdAt?.seconds || 0;
          const tB = b.createdAt?.seconds || 0;
          return tB - tA;
        });
      setAuditLogs(data);
    }, (error) => {
      handleFirestoreError(error, 'list', 'events');
    });

    return () => {
      unsubscribe();
      unsubscribeEvents();
    };
  }, []);

  const handleGrantConsent = async () => {
    const user = auth.currentUser;
    if (!user || selectedPermissions.length === 0) return;

    setIsSubmitting(true);
    try {
      const expiryDate = new Date();
      if (selectedDuration === '1_day') expiryDate.setDate(expiryDate.getDate() + 1);
      else if (selectedDuration === '1_week') expiryDate.setDate(expiryDate.getDate() + 7);
      else if (selectedDuration === '1_month') expiryDate.setMonth(expiryDate.getMonth() + 1);
      
      const consentData = {
        citizenId: user.uid,
        providerId: selectedProvider?.id || 'GLOBAL-SYSTEM',
        providerName: selectedProvider?.name || 'GULA System Services',
        scope: selectedPermissions.length > 2 ? 'full' : 'limited',
        permissions: selectedPermissions,
        status: 'active',
        duration: selectedDuration,
        expiresAt: selectedDuration === 'permanent' ? null : expiryDate.toISOString(),
        purposeOfUse: purposeOfUse,
        createdAt: serverTimestamp(),
      };

      await addDoc(collection(db, 'consents'), consentData);

      // Emit event
      await addDoc(collection(db, 'events'), {
        type: 'consent_granted',
        recipientId: selectedProvider?.id || 'system',
        senderId: user.uid,
        wing: 'citizen',
        read: false,
        payload: {
          permissions: selectedPermissions,
          providerName: selectedProvider?.name || 'GULA System Services',
          purposeOfUse: purposeOfUse
        },
        createdAt: serverTimestamp()
      });

      setShowGrantModal(false);
      setSelectedPermissions([]);
      setSelectedProvider(null);
      setTargetSearch('');
    } catch (error) {
      handleFirestoreError(error, 'create', 'consents');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRevokeConsent = async (consent: ConsentRecord) => {
    try {
      const consentRef = doc(db, 'consents', consent.id);
      await updateDoc(consentRef, {
        status: 'revoked',
        updatedAt: serverTimestamp()
      });

      // Emit event
      await addDoc(collection(db, 'events'), {
        type: 'consent_revoked',
        recipientId: consent.providerId,
        senderId: auth.currentUser?.uid,
        wing: 'citizen',
        read: false,
        payload: { 
          consentId: consent.id,
          providerName: consent.providerName
        },
        createdAt: serverTimestamp()
      });
    } catch (error) {
      handleFirestoreError(error, 'update', `consents/${consent.id}`);
    }
  };

  const permissionList: { id: PermissionType; label: string; icon: any }[] = [
    { id: 'read_vitals', label: t.vitalSigns, icon: ActivityIcon },
    { id: 'read_labs', label: t.labResults, icon: Beaker },
    { id: 'read_history', label: t.healthRecords, icon: FileText },
    { id: 'emergency', label: t.emergencyAccess, icon: AlertTriangle },
  ];

  const getProviderIcon = (providerId: string) => {
    if (providerId.includes('LAB')) return Beaker;
    if (providerId.includes('DOC')) return UserCheck;
    return Stethoscope;
  };

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-12">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 mb-2">{t.consentManagement}</h1>
          <p className="text-slate-500">You control who accesses your medical data. Granular data sovereignty.</p>
        </div>
        <div className="flex bg-slate-100 p-1 rounded-xl">
           <button 
             onClick={() => setActiveTab('active')}
             className={cn("px-6 py-2 rounded-lg text-sm font-bold transition-all", activeTab === 'active' ? "bg-white text-indigo-600 shadow-sm" : "text-slate-500")}
           >
             Active
           </button>
           <button 
             onClick={() => setActiveTab('history')}
             className={cn("px-6 py-2 rounded-lg text-sm font-bold transition-all", activeTab === 'history' ? "bg-white text-indigo-600 shadow-sm" : "text-slate-500")}
           >
             Audit Log
           </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-4">
           {isLoading ? (
             <div className="flex items-center justify-center p-12">
                <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
             </div>
           ) : activeTab === 'active' ? (
             consents.filter(c => c.status === 'active').map((c, i) => (
               <motion.div
                 key={c.id}
                 initial={{ opacity: 0, scale: 0.98 }}
                 animate={{ opacity: 1, scale: 1 }}
                 className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm hover:border-indigo-200 transition-all flex items-center justify-between group"
               >
                 <div className="flex items-center gap-5">
                   <div className="p-4 bg-slate-50 text-slate-400 group-hover:bg-indigo-50 group-hover:text-indigo-600 rounded-2xl transition-colors">
                     {React.createElement(getProviderIcon(c.providerId || ''), { className: "w-6 h-6" })}
                   </div>
                   <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-bold text-slate-900">{c.providerName || 'Healthcare Provider'}</h3>
                        <span className={cn(
                          "text-[8px] font-black uppercase tracking-[0.1em] px-2 py-0.5 rounded-full",
                          c.purposeOfUse === 'research' ? "bg-purple-100 text-purple-700" : "bg-blue-100 text-blue-700"
                        )}>
                          {c.purposeOfUse || 'clinical'}
                        </span>
                      </div>
                     <div className="flex items-center gap-2 mt-1">
                       <span className={cn(
                          "text-[10px] font-extrabold uppercase tracking-widest px-2 py-0.5 rounded",
                          c.scope === 'full' ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"
                       )}>
                          {c.scope === 'full' ? t.smartDiagnosis : t.details}
                       </span>
                       <span className="text-xs text-slate-400">
                         {c.status === 'active' ? `Expires ${c.expiresAt ? new Date(c.expiresAt).toLocaleDateString() : 'Never'}` : `Revoked`}
                       </span>
                     </div>
                     
                     <div className="flex gap-1.5 flex-wrap mt-3">
                        {c.permissions?.map(pId => {
                          const p = permissionList.find(x => x.id === pId);
                          if(!p) return null;
                          const Icon = p.icon;
                          return (
                            <div key={pId} className="flex items-center gap-1 px-2 py-1 bg-slate-50 text-[8px] font-black uppercase tracking-tighter text-slate-500 rounded-md border border-slate-100 group-hover:border-indigo-100 transition-colors">
                               <Icon className="w-2.5 h-2.5 text-indigo-500" />
                               {p.label}
                            </div>
                          );
                        })}
                     </div>
                   </div>
                 </div>
                 
                 <div className="flex gap-2">
                    <button 
                      onClick={() => handleRevokeConsent(c)}
                      className="p-2 text-slate-400 hover:text-red-600 transition-colors"
                      title="Revoke Access"
                    >
                      <Lock className="w-5 h-5" />
                    </button>
                 </div>
               </motion.div>
             ))
           ) : (
             auditLogs.map((log, i) => (
               <motion.div
                 key={log.id}
                 initial={{ opacity: 0, x: -10 }}
                 animate={{ opacity: 1, x: 0 }}
                 className="bg-white p-5 rounded-2xl border border-slate-100 flex items-center gap-4 relative overflow-hidden"
               >
                 <div className={cn(
                   "absolute left-0 top-0 bottom-0 w-1",
                   log.type === 'consent_granted' ? "bg-green-500" : "bg-red-500"
                 )} />
                 <div className={cn(
                   "p-3 rounded-xl",
                   log.type === 'consent_granted' ? "bg-green-50 text-green-600" : "bg-red-50 text-red-600"
                 )}>
                   {log.type === 'consent_granted' ? <Shield className="w-5 h-5" /> : <Lock className="w-5 h-5" />}
                 </div>
                 <div className="flex-1">
                    <p className="font-bold text-slate-900 leading-tight">
                      {log.type === 'consent_granted' ? 'Access Authorization Granted' : 'Access Authorization Revoked'}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {log.payload?.providerName || 'Healthcare Provider'} • {log.createdAt ? new Date(log.createdAt.seconds * 1000).toLocaleString() : 'Just now'}
                    </p>
                    {log.type === 'consent_granted' && log.payload?.permissions && (
                      <div className="flex gap-1.5 flex-wrap mt-2">
                        {log.payload.permissions.map((pId: string) => {
                          const p = permissionList.find(x => x.id === pId);
                          if(!p) return null;
                          return (
                            <span key={pId} className="px-1.5 py-0.5 bg-slate-50 text-[7px] font-black uppercase text-slate-400 border border-slate-100 rounded">
                              {p.label}
                            </span>
                          );
                        })}
                      </div>
                    )}
                 </div>
                 <div className="text-right">
                    <span className="text-[10px] font-black uppercase tracking-widest text-slate-300">Transaction Ledger</span>
                 </div>
               </motion.div>
             ))
           )}

           {!isLoading && activeTab === 'active' && consents.filter(c => c.status === 'active').length === 0 && (
              <div className="p-20 text-center bg-slate-50 rounded-3xl border-2 border-dashed border-slate-200">
                <Shield className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                <p className="text-slate-500 font-medium">No active data sharing authorizations.</p>
              </div>
           )}
        </div>

        <div className="space-y-6">
           <div className="bg-slate-900 rounded-3xl p-8 text-white relative overflow-hidden shadow-2xl shadow-indigo-100">
              <div className="absolute top-0 right-0 p-4 opacity-10"><Shield className="w-24 h-24" /></div>
              <h3 className="text-xl font-bold mb-4">Emergency Protocol</h3>
              <p className="text-slate-400 text-sm mb-6 leading-relaxed">By default, verified Emergency Departments can access life-saving data (Blood Type, Allergies) without explicit consent in critical situations.</p>
              
              <div className="flex items-center justify-between p-4 bg-white/5 rounded-2xl border border-white/10 mb-6">
                 <div className="flex items-center gap-3">
                   <div className="w-10 h-10 bg-indigo-500 rounded-xl flex items-center justify-center"><AlertTriangle className="w-5 h-5" /></div>
                   <span className="font-bold text-sm tracking-wide">Critical Access</span>
                 </div>
                 <div className="w-12 h-6 bg-green-500 rounded-full relative">
                    <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full" />
                 </div>
              </div>

              <div className="space-y-3">
                 <div className="flex items-center gap-2 text-xs text-indigo-300">
                   <CheckCircle2 className="w-4 h-4" /> GDPR / HIPAA Iraqi Regional Compliant
                 </div>
                 <div className="flex items-center gap-2 text-xs text-indigo-300">
                   <CheckCircle2 className="w-4 h-4" /> Data Scrubbing Enabled
                 </div>
                  <div className="flex items-center gap-2 text-xs text-indigo-300">
                   <CheckCircle2 className="w-4 h-4" /> Periodic Audit Log Export
                 </div>
              </div>
           </div>

           <button 
             onClick={() => setShowGrantModal(true)}
             className="w-full flex items-center justify-center gap-3 py-4 bg-white border-2 border-slate-200 rounded-2xl font-bold text-slate-700 hover:border-indigo-600 transition-all group"
           >
              <Plus className="w-5 h-5 text-indigo-600 group-hover:scale-110 transition-transform" /> {t.grantConsent}
           </button>
        </div>
      </div>

      {/* Grant Access Modal */}
      <AnimatePresence>
        {showGrantModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowGrantModal(false)}
              className="absolute inset-0 bg-slate-900/60 backdrop-blur-md"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="relative w-full max-w-xl bg-white rounded-[2rem] shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
            >
              <div className="p-8 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                 <div>
                    <h2 className="text-2xl font-bold text-slate-900">{t.grantConsent}</h2>
                    <p className="text-slate-500 text-sm">Secure authorization for healthcare providers.</p>
                 </div>
                 <button onClick={() => setShowGrantModal(false)} className="p-2 hover:bg-slate-200 rounded-full transition-colors">
                    <X className="w-6 h-6 text-slate-400" />
                 </button>
              </div>

              <div className="p-8 overflow-y-auto space-y-8 flex-1 custom-scrollbar">
                <div className="space-y-4">
                   <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Purpose of Access</span>
                   <div className="flex bg-slate-100 p-1 rounded-2xl">
                      {(['clinical', 'research'] as const).map(p => (
                        <button
                          key={p}
                          onClick={() => {
                            setPurposeOfUse(p);
                            setSelectedProvider(null);
                          }}
                          className={cn(
                            "flex-1 py-3 rounded-xl text-xs font-bold transition-all",
                            purposeOfUse === p ? "bg-white text-indigo-600 shadow-sm" : "text-slate-500 hover:text-slate-700"
                          )}
                        >
                          {p === 'clinical' ? 'Clinical Care' : 'Medical Research'}
                        </button>
                      ))}
                   </div>
                </div>

                <div className="space-y-4">
                   <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Target Entity</span>
                    {selectedProvider && (
                      <button 
                        onClick={() => setSelectedProvider(null)}
                        className="text-[10px] font-bold text-indigo-600 underline"
                      >
                        Change
                      </button>
                    )}
                   </div>
                   
                   {!selectedProvider ? (
                    <div className="space-y-3">
                      <div className="relative">
                        <input 
                          type="text" 
                          placeholder={`Search ${purposeOfUse === 'clinical' ? 'hospitals & clinics' : 'research projects'}...`}
                          value={targetSearch}
                          onChange={(e) => setTargetSearch(e.target.value)}
                          className="w-full bg-slate-50 border border-slate-200 rounded-xl py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                        />
                        <Shield className="absolute left-3 top-3.5 w-4 h-4 text-slate-400" />
                      </div>
                      
                      <div className="grid grid-cols-1 gap-2 max-h-40 overflow-y-auto pr-2 custom-scrollbar">
                        {filteredTargets.map(target => (
                          <button
                            key={target.id}
                            onClick={() => setSelectedProvider(target)}
                            className="flex items-center justify-between p-3 rounded-xl border border-slate-100 hover:border-indigo-600 transition-all text-left"
                          >
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 bg-slate-100 rounded-lg flex items-center justify-center text-slate-500">
                                {target.type === 'clinical' ? <Stethoscope className="w-4 h-4" /> : <Beaker className="w-4 h-4" />}
                              </div>
                              <span className="text-sm font-medium text-slate-700">{target.name}</span>
                            </div>
                            <Plus className="w-4 h-4 text-slate-400" />
                          </button>
                        ))}
                      </div>
                    </div>
                   ) : (
                    <div className="p-4 bg-indigo-50 border border-indigo-100 rounded-2xl flex items-center gap-4">
                        <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center text-indigo-600 shadow-sm">
                          {purposeOfUse === 'clinical' ? <Stethoscope className="w-6 h-6" /> : <Beaker className="w-6 h-6" />}
                        </div>
                        <div>
                          <p className="font-bold text-slate-900">{selectedProvider.name}</p>
                          <p className="text-xs text-indigo-600">Verified {purposeOfUse === 'clinical' ? 'Provider' : 'Institute'} (ID: {selectedProvider.id})</p>
                        </div>
                    </div>
                   )}
                </div>

                <div className="space-y-4">
                   <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Data Permissions</span>
                   <div className="grid grid-cols-2 gap-3">
                      {permissionList.map(p => (
                        <button
                          key={p.id}
                          onClick={() => {
                             if(selectedPermissions.includes(p.id)) {
                               setSelectedPermissions(selectedPermissions.filter(x => x !== p.id));
                             } else {
                               setSelectedPermissions([...selectedPermissions, p.id]);
                             }
                          }}
                          className={cn(
                            "flex items-center gap-3 p-4 rounded-2xl border transition-all text-left",
                            selectedPermissions.includes(p.id) ? "bg-indigo-600 border-indigo-600 text-white" : "bg-white border-slate-100 text-slate-600 hover:border-indigo-200"
                          )}
                        >
                          <p.icon className={cn("w-5 h-5", selectedPermissions.includes(p.id) ? "text-white" : "text-indigo-600")} />
                          <span className="text-sm font-bold">{p.label}</span>
                        </button>
                      ))}
                   </div>
                </div>

                <div className="space-y-4">
                   <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{t.duration}</span>
                   <div className="flex bg-slate-100 p-1 rounded-2xl">
                      {(['1_day', '1_week', '1_month', 'permanent'] as ConsentDuration[]).map(d => (
                        <button
                          key={d}
                          onClick={() => setSelectedDuration(d)}
                          className={cn(
                            "flex-1 py-3 px-2 rounded-xl text-xs font-bold transition-all",
                            selectedDuration === d ? "bg-white text-indigo-600 shadow-sm" : "text-slate-500 hover:text-slate-700"
                          )}
                        >
                          {d === 'permanent' ? t.permanent : d.replace('_', ' ')}
                        </button>
                      ))}
                   </div>
                </div>
              </div>

              <div className="p-8 bg-slate-50 border-t border-slate-100 flex gap-4">
                 <button 
                  onClick={() => setShowGrantModal(false)} 
                  disabled={isSubmitting}
                  className="flex-1 py-4 text-slate-500 font-bold hover:bg-slate-200 rounded-2xl transition-colors disabled:opacity-50"
                 >
                  Cancel
                 </button>
                 <button 
                   onClick={handleGrantConsent}
                   disabled={isSubmitting || selectedPermissions.length === 0 || !selectedProvider}
                   className="flex-[2] bg-indigo-600 text-white py-4 rounded-2xl font-bold shadow-xl shadow-indigo-100 hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-50 disabled:scale-100 flex items-center justify-center gap-2"
                 >
                   {isSubmitting && <Loader2 className="w-5 h-5 animate-spin" />}
                   Authorize & Sync
                 </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
