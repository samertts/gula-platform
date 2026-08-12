import {useState, useEffect} from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { 
  Target, 
  Map as MapIcon,
  Search,
  Bell,
  Building2,
  ClipboardList
} from 'lucide-react';
import {motion} from 'motion/react';
import { cn } from '../../lib/utils';
import { MinistryCommandCenter } from '../../components/MinistryCommandCenter';
import { TaskQueue } from '../../components/TaskQueue';
import { Task } from '../../types/domain';
import { apiGet, apiPut } from '../../api/client';
type MapNode = { label: string; val: number; color: string; hospitals: number; critical: number; x: number; y: number };
export function MinistryDashboard() {
  const { t } = useLanguage();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [mapNodes, setMapNodes] = useState<MapNode[]>([]);
  const [selectedNode, setSelectedNode] = useState<MapNode | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [hospitalsRes, nationalRes, ordersRes] = await Promise.allSettled([
          apiGet<{ items: any[]; total: number }>('/hospital'),
          apiGet<any>('/governance/analytics/national'),
          apiGet<{ data: any[] }>('/orders'),
        ]);
        const hospitals: any[] = (hospitalsRes.status === 'fulfilled' && hospitalsRes.value?.items) ? hospitalsRes.value.items : [];
        if (hospitals.length > 0) {
          const colors = ['#6366f1', '#f43f5e', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16'];
          const xs = [400, 550, 650, 600, 450, 250, 150, 180];
          const ys = [50, 150, 300, 450, 550, 520, 400, 200];
          const nodes: MapNode[] = hospitals.slice(0, 8).map((h: any, idx: number) => ({
            label: h.name_ar || h.name || h.code || `Node ${idx + 1}`,
            val: 0,
            color: colors[idx % colors.length] || '#6366f1',
            hospitals: 1,
            critical: 0,
            x: xs[idx % xs.length] || 400,
            y: ys[idx % ys.length] || 50,
          }));
          setMapNodes(nodes);
        } else if (nationalRes.status === 'fulfilled' && nationalRes.value?.laboratories?.by_type) {
          const types = Object.keys(nationalRes.value.laboratories.by_type);
          const colors = ['#6366f1', '#f43f5e', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16'];
          const xs = [400, 550, 650, 600, 450, 250, 150, 180];
          const ys = [50, 150, 300, 450, 550, 520, 400, 200];
          const nodes: MapNode[] = types.slice(0, 8).map((type: string, idx: number) => ({
            label: type,
            val: nationalRes.value.laboratories.by_type[type] || 0,
            color: colors[idx % colors.length] || '#6366f1',
            hospitals: nationalRes.value.laboratories.by_type[type] || 0,
            critical: 0,
            x: xs[idx % xs.length] || 400,
            y: ys[idx % ys.length] || 50,
          }));
          setMapNodes(nodes);
        } else {
          setMapNodes([
            { label: 'Baghdad', val: 72, color: '#6366f1', hospitals: 12, critical: 4, x: 400, y: 50 },
            { label: 'Basrah', val: 88, color: '#f43f5e', hospitals: 8, critical: 7, x: 550, y: 150 },
          ]);
        }
        if (ordersRes.status === 'fulfilled') {
          const orders = ordersRes.value?.data || [];
          const mapped: Task[] = orders.slice(0, 10).map((o: any, idx: number) => ({
            id: o.id || `task-${idx}`,
            title: `Order #${(o.id || '').slice(0, 8) || idx + 1}`,
            status: (o.status === 'completed' ? 'completed' : 'in_progress') as Task['status'],
            priority: (o.priority || 'normal') as Task['priority'],
            assignee: o.assigned_to || o.doctor_name || 'Unassigned',
            description: o.test_name || o.description || '',
            createdAt: o.created_at || new Date().toISOString(),
            updatedAt: o.updated_at || new Date().toISOString(),
          } as unknown as Task));
          setTasks(mapped);
        }
      } catch {
        setMapNodes([]);
      }
    };
    fetchData();
  }, []);
  const handleSearch = (q: string) => {
    setSearchQuery(q);
  };
  const handleBulkAction = async (action: string, taskIds: string[]) => {
    const statusMap: Record<string, string> = { assign: 'assigned', complete: 'completed', hold: 'on_hold', process: 'in_progress' };
    const newStatus = statusMap[action] || action;
    try {
      await Promise.all(taskIds.map(id => apiPut(`/orders/${id}/status`, { status: newStatus })));
      setTasks(prev => prev.map(t => taskIds.includes(t.id) ? { ...t, status: newStatus as Task['status'] } : t));
    } catch (e) {
      console.error('Bulk action failed', e);
    }
  };
  return (
    <div className="p-8 max-w-7xl mx-auto space-y-12">
      {/* Header Section */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-8">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
             <div className="w-12 h-12 bg-indigo-600 rounded-2xl flex items-center justify-center shadow-xl shadow-indigo-100">
                <Building2 size={24} className="text-white" />
             </div>
             <div>
                <span className="text-[10px] font-black text-indigo-600 uppercase tracking-[0.2em]">{t.ministryWing}</span>
                <h1 className="text-3xl lg:text-4xl font-black text-slate-900 tracking-tight leading-none mt-1 uppercase">
                   {t.nationalCommandCenter}
                </h1>
             </div>
          </div>
          <p className="text-sm text-slate-500 font-medium max-w-xl">
             Centralized analytical oversight of the national health infrastructure. 
             Real-time monitoring across active lab nodes and clinical centers.
          </p>
        </div>
        <div className="flex items-center gap-4 w-full lg:w-auto">
          <div className="relative flex-1 lg:w-64 group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-600 transition-colors" size={18} />
            <input 
              type="text" 
              placeholder={t.globalSearch}
              value={searchQuery}
              onChange={e => handleSearch(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-white border border-slate-100 rounded-2xl text-sm font-medium focus:ring-4 focus:ring-indigo-50 focus:border-indigo-200 transition-all shadow-sm"
            />
          </div>
          <button className="p-3 bg-white border border-slate-100 rounded-2xl text-slate-400 hover:text-indigo-600 transition-all shadow-sm relative">
            <Bell size={20} />
            <span className="absolute top-3 right-3 w-2 h-2 bg-red-500 rounded-full border-2 border-white" />
          </button>
        </div>
      </div>
      <MinistryCommandCenter />
      {/* Main Analysis Grid */}
      <div className="grid grid-cols-12 gap-8">
        {/* Geographical Surveillance */}
        <div className="col-span-12 lg:col-span-8 space-y-8">
           <div className="bg-white rounded-[2.5rem] border border-slate-100 shadow-sm p-8">
              <div className="flex justify-between items-center mb-10">
                <div className="flex items-center gap-4">
                   <div className="w-12 h-12 bg-slate-50 rounded-2xl flex items-center justify-center">
                      <MapIcon size={24} className="text-slate-600" />
                   </div>
                   <div>
                      <h2 className="text-xl font-black text-slate-900 tracking-tight uppercase">{t.gisSurveillance}</h2>
                      <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">{t.globalStatus}</p>
                   </div>
                </div>
              </div>
              <div className="aspect-[16/9] bg-slate-50 rounded-3xl border border-slate-100 relative overflow-hidden flex items-center justify-center group p-8">
                 <div className="absolute inset-0 opacity-40 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] pointer-events-none" />
                 <svg 
                   viewBox="0 0 800 600" 
                   className="w-full h-full text-slate-200 fill-slate-200 relative z-10 transition-all duration-700 group-hover:scale-105"
                 >
                    {/* Stylized Iraq/Kurdistan Map Contours */}
                    <path d="M400 50 L550 150 L650 300 L600 450 L450 550 L250 520 L150 400 L180 200 Z" className="fill-slate-100 stroke-slate-200 stroke-2" />
                    
                    {/* Interconnected Nodes */}
                     {mapNodes.map((node: any, i: number) => (
                      <g 
                        key={i} 
                        className="cursor-pointer group/node"
                        onClick={() => setSelectedNode(node === selectedNode ? null : node)}
                      >
                        {/* Area of influence */}
                        <circle cx={node.x} cy={node.y} r={selectedNode === node ? node.val : node.val / 2} fill={node.color} fillOpacity={selectedNode === node ? "0.1" : "0.05"} className={cn("transition-all duration-500", selectedNode === node ? "" : "animate-pulse")} />
                        <circle cx={node.x} cy={node.y} r={selectedNode === node ? "10" : "6"} fill={node.color} className="shadow-lg transition-all duration-300" />
                        <motion.circle 
                          cx={node.x} cy={node.y} r="12" 
                          fill="none" stroke={node.color} strokeOpacity="0.3" 
                          initial={{ scale: 0.8 }}
                          animate={{ scale: [1, 1.5, 1], opacity: [0.3, 0, 0.3] }}
                          transition={{ repeat: Infinity, duration: 2, delay: i * 0.4 }}
                        />
                        <text x={node.x + 12} y={node.y + 4} className={cn("text-[12px] font-black fill-slate-500 uppercase tracking-tighter transition-opacity", selectedNode === node ? "opacity-100" : "opacity-0 group-hover/node:opacity-100")}>
                          {node.label} • {node.val}%
                        </text>
                        {/* Connection Lines (Simulated Mesh) */}
                        {i > 0 && (
                          <line 
                            x1={node.x} y1={node.y} 
                            x2={400} y2={300} 
                            stroke={node.color} strokeWidth="1" strokeDasharray="4 4" strokeOpacity="0.2" 
                          />
                        )}
                      </g>
                    ))}
                 </svg>
                 {selectedNode && (
                   <motion.div 
                     initial={{ opacity: 0, scale: 0.9 }}
                     animate={{ opacity: 1, scale: 1 }}
                     className="absolute top-6 left-6 p-6 bg-white/90 backdrop-blur-xl border border-indigo-100 rounded-3xl shadow-2xl z-20 w-64"
                   >
                      <div className="flex justify-between items-start mb-4">
                        <div className="p-2 bg-indigo-50 rounded-xl">
                          <MapIcon size={18} className="text-indigo-600" />
                        </div>
                        <button onClick={() => setSelectedNode(null)} className="text-[10px] font-black uppercase text-slate-400 hover:text-slate-900">Close</button>
                      </div>
                      <h4 className="text-lg font-black text-slate-900 uppercase tracking-tight">{selectedNode.label} Drill-Down</h4>
                      <div className="space-y-4 mt-6">
                        <div className="flex justify-between items-end">
                          <span className="text-[10px] font-black uppercase text-slate-400">Regional Health Load</span>
                          <span className="text-lg font-black text-indigo-600">{selectedNode.val}%</span>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                           <div className="p-3 bg-slate-50 rounded-2xl">
                             <p className="text-[8px] font-black uppercase text-slate-400 mb-1">Hospitals</p>
                             <p className="text-sm font-black text-slate-900">{selectedNode.hospitals}</p>
                           </div>
                           <div className="p-3 bg-red-50 rounded-2xl">
                             <p className="text-[8px] font-black uppercase text-red-400 mb-1">Critical Cases</p>
                             <p className="text-sm font-black text-red-600">{selectedNode.critical}</p>
                           </div>
                        </div>
                        <button className="w-full py-3 bg-indigo-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-indigo-700 transition-all">
                          Full Analytics
                        </button>
                      </div>
                   </motion.div>
                 )}
                 <div className="absolute bottom-6 right-6 flex items-center gap-2 bg-white/80 backdrop-blur px-3 py-1.5 rounded-lg border border-slate-200 text-[9px] font-black uppercase tracking-widest text-slate-500 shadow-sm transition-opacity group-hover:opacity-0">
                    <Target size={12} className="animate-pulse text-indigo-500" /> Live Feed Active
                 </div>
              </div>
           </div>
           {/* Executive Task Oversight */}
           <div className="space-y-4">
              <div className="flex items-center gap-3 px-4">
                 <ClipboardList className="text-indigo-600" size={20} />
                 <h2 className="text-lg font-black text-slate-900 uppercase tracking-tight">Executive Task Oversight</h2>
              </div>
               <TaskQueue 
                 tasks={tasks} 
                 onAssign={async (id) => { try { await apiPut(`/orders/${id}/status`, { status: 'in_progress' }); } catch {} }}
                 onUpdateStatus={async (id, status) => { try { await apiPut(`/orders/${id}/status`, { status }); } catch {} }}
                 onBulkAction={handleBulkAction}
               />
           </div>
        </div>
        {/* Inventory & Supply Chain */}
        <div className="col-span-12 lg:col-span-4 space-y-8">
           <div className="bg-slate-900 rounded-[2.5rem] p-8 text-white relative overflow-hidden">
             <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/20 blur-[80px] -mr-16 -mt-16" />
              <h3 className="text-lg font-black uppercase tracking-tight mb-6">{t.supplyChain}</h3>
              
              <div className="text-center py-8">
                <p className="text-slate-400 text-sm font-medium">Supply chain data will appear once inventory is configured.</p>
              </div>
              
              <button className="w-full mt-10 py-4 bg-white/10 hover:bg-white text-white hover:text-slate-900 rounded-2xl font-black text-[10px] uppercase tracking-widest transition-all border border-white/10">
                 {t.manageCredentials}
              </button>
           </div>
        </div>
      </div>
    </div>
  );
}