import React from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { 
  Code2, 
  Terminal, 
  Key, 
  Database, 
  Globe, 
  Download,
  Copy,
  CheckCircle2,
  Lock,
  ArrowRight
} from 'lucide-react';
import { motion } from 'motion/react';

const CodeBlock = ({ code }: { code: string }) => {
  const [copied, setCopied] = React.useState(false);

  const copy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-slate-900 rounded-2xl p-6 relative group overflow-hidden border border-white/5">
      <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity">
        <button onClick={copy} className="p-2 hover:bg-white/10 rounded-xl text-white/40 hover:text-white transition-all">
          {copied ? <CheckCircle2 size={16} className="text-green-400" /> : <Copy size={16} />}
        </button>
      </div>
      <pre className="text-indigo-300 font-mono text-xs leading-relaxed overflow-x-auto">
        <code>{code}</code>
      </pre>
    </div>
  );
};

export function IntegrationHub() {
  const { t } = useLanguage();

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-12">
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-8">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-indigo-600 mb-1">
            <Code2 size={20} />
            <span className="text-[10px] font-black uppercase tracking-[0.2em]">Interoperability Layer</span>
          </div>
          <h1 className="text-4xl font-black text-slate-900 tracking-tight uppercase">Developer Integration Hub.</h1>
          <p className="text-slate-500 font-medium max-w-2xl">Connect external LIMS, RIS, and clinical systems through standardized FHIR/HL7 compatible APIs.</p>
        </div>

        <button className="px-6 py-3 bg-indigo-600 text-white rounded-2xl shadow-xl shadow-indigo-100 font-black text-[10px] uppercase tracking-widest flex items-center gap-2 hover:scale-105 transition-all">
           Generate API Credentials <Key size={16} />
        </button>
      </div>

      <div className="grid grid-cols-12 gap-8">
        {/* API Stats */}
        <div className="col-span-12 lg:col-span-4 bg-white rounded-[2.5rem] border border-slate-100 p-8 space-y-8">
           <div className="space-y-4">
              <h3 className="text-sm font-black text-slate-900 uppercase tracking-tight">Active Endpoints</h3>
              <div className="space-y-3">
                 {[
                   { label: 'FHIR Patient Resource', status: 'Optimal', load: '12%', color: 'text-green-500' },
                   { label: 'LOINC Diagnostic Report', status: 'Optimal', load: '45%', color: 'text-green-500' },
                   { label: 'SMART-on-FHIR Auth', status: 'Warning', load: '88%', color: 'text-amber-500' },
                 ].map((api, i) => (
                   <div key={i} className="p-4 bg-slate-50 rounded-2xl flex items-center justify-between group hover:bg-indigo-50 transition-colors">
                      <div>
                         <p className="text-[10px] font-black text-slate-900 uppercase tracking-tight">{api.label}</p>
                         <p className="text-[9px] font-bold text-slate-400 mt-0.5">{api.load} Load</p>
                      </div>
                      <span className={`text-[8px] font-black uppercase tracking-widest ${api.color}`}>{api.status}</span>
                   </div>
                 ))}
              </div>
           </div>

           <div className="bg-slate-900 rounded-[2rem] p-6 text-white overflow-hidden relative">
              <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/20 blur-[60px] -mr-8 -mt-8" />
              <div className="relative z-10">
                 <Terminal size={24} className="text-indigo-400 mb-4" />
                 <h4 className="text-xs font-black uppercase tracking-widest mb-2">Platform Webhook status</h4>
                 <div className="flex items-center gap-2 mb-6">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-ping" />
                    <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Listening...</span>
                 </div>
              </div>
           </div>
        </div>

        {/* Documentation / Code */}
        <div className="col-span-12 lg:col-span-8 bg-white rounded-[2.5rem] border border-slate-100 p-8">
           <div className="flex items-center gap-4 mb-10">
              <div className="w-12 h-12 bg-slate-50 rounded-2xl flex items-center justify-center text-indigo-600">
                 <Globe size={24} />
              </div>
              <div>
                 <h2 className="text-xl font-black text-slate-900 tracking-tight uppercase">Implementation Guide</h2>
                 <p className="text-[10px] text-slate-400 font-black uppercase tracking-widest">REST and GraphQL documentation</p>
              </div>
           </div>

           <div className="space-y-8">
              <div className="space-y-4">
                 <div className="flex items-center justify-between">
                    <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest">Authentication (OIDC/OAuth2)</h4>
                    <span className="px-2 py-1 bg-indigo-50 text-indigo-600 text-[8px] font-black uppercase rounded-md tracking-widest">v1.2.0</span>
                 </div>
                 <CodeBlock code={`POST /api/v1/auth/token
Content-Type: application/json

{
  "client_id": "GULA_HL7_NODE_882",
  "client_secret": "********************",
  "grant_type": "client_credentials",
  "scope": "system/*.read system/*.write"
}`} />
              </div>

              <div className="space-y-4">
                 <div className="flex items-center justify-between">
                    <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest">Query Patient Data (FHIR R4)</h4>
                    <button className="text-[9px] font-black text-indigo-600 uppercase tracking-widest flex items-center gap-1 hover:gap-2 transition-all">
                       Open Documentation <ArrowRight size={12} />
                    </button>
                 </div>
                 <CodeBlock code={`GET /fhir/Patient?identifier=national_id|123456789
Authorization: Bearer {{ACCESS_TOKEN}}
Accept: application/fhir+json`} />
              </div>

              <div className="p-6 bg-slate-50 rounded-3xl border border-dashed border-slate-200 flex items-start gap-4">
                 <div className="p-2 bg-white rounded-xl shadow-sm border border-slate-100">
                    <Lock size={18} className="text-amber-500" />
                 </div>
                 <div className="space-y-1">
                    <h5 className="text-[10px] font-black text-slate-900 uppercase tracking-tight">Zero-Trust Enforcement Active</h5>
                    <p className="text-[10px] text-slate-500 leading-relaxed font-medium">
                       All API requests undergo multi-layered validation. Identifiers must match valid national nodes.
                       Shadow requests are automatically flagged in the security audit.
                    </p>
                 </div>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
