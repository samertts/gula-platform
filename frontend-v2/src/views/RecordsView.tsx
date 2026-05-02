import { Plus, Search, Filter, MoreHorizontal, User } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { cn } from '../lib/utils';

export function RecordsView() {
  const { t } = useLanguage();
  const navigate = useNavigate();

  const patients = [
    { name: "Ahmed Mansour", id: "P-9021", nhid: "GULA-882-99-XC", status: "Active", age: "42", blood: "A+", date: "2024-04-19" },
    { name: "Sara Khalid", id: "P-8842", nhid: "GULA-441-22-BY", status: "Stable", age: "29", blood: "O-", date: "2024-04-18" },
    { name: "Karwan Ali", id: "P-7721", nhid: "GULA-331-55-ZA", status: "Critical", age: "55", blood: "B+", date: "2024-04-17" },
    { name: "Leyla Demir", id: "P-6612", nhid: "GULA-221-88-WE", status: "Recovered", age: "34", blood: "AB+", date: "2024-04-15" }
  ];

  return (
    <div className="p-8 space-y-8 animate-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-6 max-w-7xl mx-auto w-full">
        <div className="editorial-stack">
          <span className="text-xs font-bold uppercase tracking-[0.2em] text-indigo-600">{t.healthRecords}</span>
          <h2 className="font-headline text-3xl lg:text-4xl font-bold text-slate-900 mt-1 tracking-tight">Clinical Database</h2>
        </div>
        <button className="w-full sm:w-auto px-5 py-2.5 bg-indigo-600 text-white font-bold text-sm rounded-xl shadow-lg shadow-indigo-100 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-2">
          <Plus size={18} />
          {t.addPatient}
        </button>
      </div>

      <div className="max-w-7xl mx-auto w-full bg-white rounded-2xl border border-slate-100 overflow-hidden shadow-sm">
        <div className="p-6 border-b border-slate-50 flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <input 
              type="text" 
              placeholder="Filter patients..."
              className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-100 rounded-xl text-sm focus:ring-4 focus:ring-indigo-100 focus:bg-white transition-all"
            />
          </div>
          <button className="p-2 text-slate-400 hover:bg-slate-50 rounded-lg">
            <Filter size={20} />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-right">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
              <tr>
                <th className="px-6 py-4 font-semibold">{t.patientName}</th>
                <th className="px-6 py-4 font-semibold">National ID</th>
                <th className="px-6 py-4 font-semibold">{t.age}</th>
                <th className="px-6 py-4 font-semibold">{t.bloodType}</th>
                <th className="px-6 py-4 font-semibold">{t.status}</th>
                <th className="px-6 py-4 font-semibold">{t.date}</th>
                <th className="px-6 py-4 text-left"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {patients.map((patient, i) => (
                <tr 
                  key={i} 
                  onClick={() => navigate(`/patients/${patient.id}`)}
                  className="hover:bg-slate-50 transition-colors cursor-pointer group"
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600 font-bold text-xs group-hover:bg-indigo-600 group-hover:text-white transition-all">
                        <User size={16} />
                      </div>
                      <div>
                        <p className="text-sm font-bold text-slate-900">{patient.name}</p>
                        <p className="text-[10px] text-slate-400 font-mono tracking-tighter">{patient.id}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-xs font-bold text-indigo-600 bg-indigo-50 px-2 py-1 rounded-lg">
                      {patient.nhid}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-medium text-slate-600">{patient.age}</td>
                  <td className="px-6 py-4 font-medium text-slate-600">{patient.blood}</td>
                  <td className="px-6 py-4">
                    <span className={cn(
                      "px-3 py-1 rounded-full text-[10px] font-semibold transition-colors",
                      patient.status === 'Critical' ? 'bg-red-50 text-red-700' :
                      patient.status === 'Active' ? 'bg-indigo-50 text-indigo-700' :
                      'bg-green-50 text-green-700'
                    )}>
                      {patient.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-medium text-slate-500">{patient.date}</td>
                  <td className="px-6 py-4 text-left">
                    <button className="p-2 text-slate-300 hover:text-slate-600 rounded-lg">
                      <MoreHorizontal size={18} />
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
