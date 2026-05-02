import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { cn } from '../lib/utils';

export function Breadcrumbs() {
  const location = useLocation();
  const { t, isRtl } = useLanguage();
  const pathnames = location.pathname.split('/').filter((x) => x);

  if (location.pathname === '/') return null;

  return (
    <nav className="flex mb-8 items-center" aria-label="Breadcrumb">
      <ol className={cn(
        "flex items-center space-x-2 md:space-x-4",
        isRtl ? "flex-row-reverse space-x-reverse" : "flex-row"
      )}>
        <li>
          <div className="flex items-center">
            <Link 
              to="/" 
              className="text-slate-400 hover:text-indigo-600 transition-colors flex items-center gap-2 group"
            >
              <Home size={16} className="group-hover:scale-110 transition-transform" />
              <span className="sr-only">Home</span>
            </Link>
          </div>
        </li>
        {pathnames.map((value, index) => {
          const last = index === pathnames.length - 1;
          const to = `/${pathnames.slice(0, index + 1).join('/')}`;
          
          // Simple heuristic to format the breadcrumb name
          const name = value.charAt(0).toUpperCase() + value.slice(1).replace(/-/g, ' ');

          return (
            <li key={to}>
              <div className="flex items-center">
                <ChevronRight size={14} className={cn("text-slate-300", isRtl && "rotate-180")} />
                {last ? (
                  <span className="ml-2 md:ml-4 text-xs font-black uppercase tracking-widest text-indigo-600">
                    {name}
                  </span>
                ) : (
                  <Link
                    to={to}
                    className="ml-2 md:ml-4 text-xs font-black uppercase tracking-widest text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    {name}
                  </Link>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
