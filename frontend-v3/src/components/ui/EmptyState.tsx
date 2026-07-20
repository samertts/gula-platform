import { cn } from '@/lib/utils';
import { Inbox } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { Button } from './Button';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
  className?: string;
}

export function EmptyState({ icon: Icon = Inbox, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-16 px-4 text-center', className)}>
      <div className="rounded-full bg-surface-container-high p-4 mb-4">
        <Icon className="h-8 w-8 text-on-surface-variant" />
      </div>
      <h3 className="text-lg font-medium text-on-surface mb-1">{title}</h3>
      {description && <p className="text-sm text-on-surface-variant max-w-sm mb-4">{description}</p>}
      {action && <Button onClick={action.onClick}>{action.label}</Button>}
    </div>
  );
}
