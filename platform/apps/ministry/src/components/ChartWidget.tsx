import { ReactNode, useState } from 'react';
import { cn } from '@gula/ui-platform';
import { Maximize2, Minimize2, Download } from 'lucide-react';

interface ChartWidgetProps {
  title: string;
  subtitle?: string;
  type?: string;
  children?: ReactNode;
  className?: string;
  action?: ReactNode;
  onExport?: () => void;
  fullscreen?: boolean;
}

export function ChartWidget({ title, subtitle, type, children, className, action, onExport, fullscreen: controlledFullscreen }: ChartWidgetProps) {
  const [internalFullscreen, setInternalFullscreen] = useState(false);
  const isFullscreen = controlledFullscreen !== undefined ? controlledFullscreen : internalFullscreen;
  const toggleFullscreen = () => setInternalFullscreen(f => !f);

  return (
    <div className={cn(
      'rounded-2xl border bg-white/5 border-white/10 overflow-hidden transition-all duration-300',
      isFullscreen && 'fixed inset-4 z-50 bg-slate-950 border-white/20 overflow-auto',
      className,
    )}>
      <div className="flex items-center justify-between p-5 border-b border-white/5">
        <div>
          <h3 className="text-sm font-bold text-white">{title}</h3>
          {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
        </div>
        <div className="flex items-center gap-2">
          {action}
          {onExport && (
            <button
              onClick={onExport}
              className="p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
              title="تصدير"
            >
              <Download size={16} />
            </button>
          )}
          <button
            onClick={toggleFullscreen}
            className="p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
          >
            {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </button>
        </div>
      </div>
      <div
        className={cn('p-5', isFullscreen && 'min-h-[calc(100vh-8rem)]')}
        data-chart-type={type}
      >
        {children ?? <p className="text-sm text-slate-500">لا توجد بيانات متاحة حالياً</p>}
      </div>
    </div>
  );
}
