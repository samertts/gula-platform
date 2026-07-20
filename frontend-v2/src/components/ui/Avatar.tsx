import { cn } from '../../lib/utils';

interface AvatarProps {
  name?: string;
  src?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  status?: 'online' | 'offline' | 'busy' | 'away';
}

const sizes = {
  sm: 'w-8 h-8 text-[10px]',
  md: 'w-10 h-10 text-xs',
  lg: 'w-12 h-12 text-sm',
  xl: 'w-16 h-16 text-lg',
};

const statusColors = {
  online: 'bg-emerald-500',
  offline: 'bg-slate-400',
  busy: 'bg-red-500',
  away: 'bg-amber-500',
};

const statusSizes = { sm: 'w-2.5 h-2.5', md: 'w-3 h-3', lg: 'w-3.5 h-3.5', xl: 'w-4 h-4' };

function getInitials(name?: string): string {
  if (!name) return '?';
  return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
}

function getColorFromName(name?: string): string {
  if (!name) return 'bg-indigo-100 text-indigo-600';
  const colors = [
    'bg-indigo-100 text-indigo-600',
    'bg-emerald-100 text-emerald-600',
    'bg-amber-100 text-amber-600',
    'bg-rose-100 text-rose-600',
    'bg-sky-100 text-sky-600',
    'bg-violet-100 text-violet-600',
    'bg-cyan-100 text-cyan-600',
    'bg-orange-100 text-orange-600',
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return colors[Math.abs(hash) % colors.length];
}

export function Avatar({ name, src, size = 'md', className, status }: AvatarProps) {
  return (
    <div className={cn('relative shrink-0', className)}>
      {src ? (
        <img
          src={src}
          alt={name || 'Avatar'}
          className={cn('rounded-xl object-cover', sizes[size])}
        />
      ) : (
        <div className={cn(
          'rounded-xl flex items-center justify-center font-black',
          sizes[size],
          getColorFromName(name),
        )}>
          {getInitials(name)}
        </div>
      )}
      {status && (
        <span className={cn(
          'absolute -bottom-0.5 -right-0.5 rounded-full border-2 border-white',
          statusSizes[size],
          statusColors[status],
        )} />
      )}
    </div>
  );
}
