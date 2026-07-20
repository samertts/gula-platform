import { cn } from '../../lib/utils';

interface KbdProps {
  children: React.ReactNode;
  className?: string;
  size?: 'sm' | 'md';
}

export function Kbd({ children, className, size = 'sm' }: KbdProps) {
  return (
    <kbd
      className={cn(
        'font-mono font-black text-slate-500 bg-slate-100 border border-slate-200 rounded-md shadow-sm',
        size === 'sm' ? 'px-1.5 py-0.5 text-[9px]' : 'px-2.5 py-1 text-[10px]',
        className,
      )}
    >
      {children}
    </kbd>
  );
}
