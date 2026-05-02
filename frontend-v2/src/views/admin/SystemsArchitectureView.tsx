import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Shield, 
  Server, 
  Database, 
  Search,
  MoreVertical,
  Edit,
  Trash2,
  CheckCircle,
  AlertTriangle,
  Globe,
  Network
} from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { db } from '../../firebase';
import { collection, query, getDocs, orderBy, doc, updateDoc } from 'firebase/firestore';
import { UserProfile, Tenant } from '../../types/domain';
import { motion } from 'motion/react';
import { toast } from 'sonner';

export function SystemsArchitectureView() {
  const { t } = useLanguage();
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const userSnap = await getDocs(query(collection(db, 'users'), orderBy('createdAt', 'desc')));
        const tenantSnap = await getDocs(collection(db, 'tenants'));
        
        setUsers(userSnap.docs.map(d => ({ uid: d.id, ...d.data() } as unknown as UserProfile)));
        setTenants(tenantSnap.docs.map(d => ({ id: d.id, ...d.data() } as unknown as Tenant)));
      } catch (error) {
        console.error('Error fetching system data:', error);
        toast.error('Failed to load system architecture data');
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleRoleChange = async (uid: string, newRole: string) => {
    try {
      await updateDoc(doc(db, 'users', uid), { role: newRole });
      setUsers(prev => prev.map(u => u.uid === uid ? { ...u, role: newRole as any } : u));
      toast.success(`Role updated to ${newRole}`);
    } catch (error) {
      toast.error('Failed to update role');
    }
  };

  const filteredUsers = users.filter(user => 
    user.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.role.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-black text-slate-900 tracking-tighter uppercase">{t.systemDashboard}</h1>
        <p className="text-slate-500 font-medium">{t.globalStatus}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { label: 'Active Nodes', value: users.length, icon: Users, color: 'indigo' },
          { label: 'Cloud Regions', value: '4', icon: Globe, color: 'emerald' },
          { label: 'Tenants', value: tenants.length, icon: Server, color: 'blue' },
          { label: 'Database Health', value: '99.9%', icon: Database, color: 'amber' }
        ].map((stat, i) => (
          <div key={i} className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm flex items-center gap-4">
            <div className={`w-12 h-12 rounded-2xl bg-${stat.color}-50 text-${stat.color}-600 flex items-center justify-center`}>
              <stat.icon size={24} />
            </div>
            <div>
              <p className="text-xs font-black text-slate-400 uppercase tracking-widest">{stat.label}</p>
              <p className="text-2xl font-black text-slate-900">{stat.value}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-[2.5rem] border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-8 border-b border-slate-50 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center">
              <Network size={24} />
            </div>
            <div>
              <h2 className="text-xl font-black text-slate-900 tracking-tight">Identity Network</h2>
              <p className="text-xs font-medium text-slate-400">Manage all registered nodes and their permissions</p>
            </div>
          </div>
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              placeholder="Filter nodes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 pr-6 py-3 bg-slate-50 border-none rounded-2xl text-sm font-medium focus:ring-2 focus:ring-indigo-500 transition-all w-full md:w-64"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50">
                <th className="px-8 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Node User</th>
                <th className="px-8 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Access Role</th>
                <th className="px-8 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Health Status</th>
                <th className="px-8 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">Verification</th>
                <th className="px-8 py-4 text-[10px] font-black text-slate-400 uppercase tracking-widest"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {filteredUsers.map((user) => (
                <tr key={user.uid} className="hover:bg-slate-50/50 transition-colors group">
                  <td className="px-8 py-5">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center font-black text-xs">
                        {user.name?.[0] || user.email[0].toUpperCase()}
                      </div>
                      <div className="flex flex-col">
                        <span className="text-sm font-black text-slate-900">{user.name || 'Unnamed Node'}</span>
                        <span className="text-[10px] font-medium text-slate-400">{user.email}</span>
                      </div>
                    </div>
                  </td>
                  <td className="px-8 py-5">
                    <select
                      value={user.role}
                      onChange={(e) => handleRoleChange(user.uid, e.target.value)}
                      className="text-xs font-bold py-1.5 px-3 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="citizen">Citizen</option>
                      <option value="physician">Physician</option>
                      <option value="technician">Technician</option>
                      <option value="pathologist">Pathologist</option>
                      <option value="researcher">Researcher</option>
                      <option value="regulator">Regulator</option>
                      <option value="ministry_admin">Ministry Admin</option>
                      <option value="admin">System Admin</option>
                      <option value="master_admin">Master Admin</option>
                    </select>
                  </td>
                  <td className="px-8 py-5">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                      <span className="text-xs font-bold text-slate-600">Sync Optimal</span>
                    </div>
                  </td>
                  <td className="px-8 py-5">
                    {user.verified ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-600 text-[10px] font-black uppercase tracking-wider">
                        <CheckCircle size={10} /> Verified
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-50 text-amber-600 text-[10px] font-black uppercase tracking-wider">
                        <AlertTriangle size={10} /> Pending
                      </span>
                    )}
                  </td>
                  <td className="px-8 py-5 text-right opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all">
                      <MoreVertical size={18} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
