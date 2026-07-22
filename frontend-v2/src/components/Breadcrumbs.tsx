import { memo } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home, ChevronLeft } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { cn } from '../lib/utils';
const ROUTE_LABELS: Record<string, string> = {
  lab: 'Lab Operations',
  citizen: 'Citizen Portal',
  ministry: 'Ministry',
  admin: 'Administration',
  patients: 'Patients',
  appointments: 'Appointments',
  intelligence: 'AI Intelligence',
  dashboard: 'Dashboard',
  queue: 'Work Queue',
  samples: 'Samples',
  devices: 'Devices',
  inventory: 'Inventory',
  qc: 'Quality Control',
  imaging: 'Imaging Lab',
  profile: 'Profile',
  results: 'Results',
  medications: 'Medications',
  assistant: 'AI Assistant',
  family: 'Family',
  history: 'History',
  consent: 'Consent',
  verification: 'Verification',
  register: 'Registration',
  epidemiology: 'Epidemiology',
  analytics: 'Analytics',
  audit: 'Audit',
  infrastructure: 'Infrastructure',
  integrations: 'Integrations',
  architecture: 'Architecture',
  settings: 'Settings',
  research: 'Research',
  security: 'Security',
};
const ROUTE_ICONS: Record<string, string> = {
  lab: '🔬',
  citizen: '👤',
  ministry: '🏛️',
  admin: '🛡️',
};
export const Breadcrumbs = memo(function Breadcrumbs() {
  const location = useLocation();
  const { t, isRtl } = useLanguage();
  const pathnames = location.pathname.split('/').filter((x) => x);
  if (location.pathname === '/') return null;
  const ChevronIcon = isRtl ? ChevronLeft : ChevronRight;
  return (
    <nav className="flex mb-6 items-center" aria-label="Breadcrumb">
      <ol className={cn('flex items-center gap-1.5', isRtl && 'flex-row-reverse')}>
        <li>
          <Link to="/" className="text-slate-400 hover:text-indigo-600 transition-colors flex items-center gap-1.5 group">
            <Home size={14} className="group-hover:scale-110 transition-transform" />
            <span className="text-[10px] font-bold uppercase tracking-wider hidden sm:inline">{t.home || 'Home'}</span>
          </Link>
        </li>
        {pathnames.map((value, index) => {
          const last = index === pathnames.length - 1;
          const to = `/${pathnames.slice(0, index + 1).join('/')}`;
          const label = ROUTE_LABELS[value] || value.charAt(0).toUpperCase() + value.slice(1).replace(/-/g, ' ');
          return (
            <li key={to} className="flex items-center gap-1.5">
              <ChevronIcon size={12} className="text-slate-300" />
              {last ? (
                <span className="text-[10px] font-black uppercase tracking-widest text-indigo-600">
                  {label}
                </span>
              ) : (
                <Link to={to} className="text-[10px] font-bold uppercase tracking-wider text-slate-400 hover:text-slate-600 transition-colors">
                  {label}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
});