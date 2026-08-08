import { type ReactNode } from 'react';
import { cn } from '../../utils/cn';

export interface LayoutProps {
  sidebar?: ReactNode;
  header?: ReactNode;
  children: ReactNode;
  sidebarCollapsible?: boolean;
  defaultSidebarCollapsed?: boolean;
  className?: string;
  contentClassName?: string;
}

export function Layout({
  sidebar,
  header,
  children,
  sidebarCollapsible = false,
  defaultSidebarCollapsed = false,
  className,
  contentClassName,
}: LayoutProps) {
  return (
    <div className={cn('flex h-screen overflow-hidden bg-neutral-50 dark:bg-neutral-950', className)}>
      {sidebar && (
        <div className="shrink-0 hidden lg:flex flex-col">
          {sidebar}
        </div>
      )}

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {header}

        <main
          className={cn(
            'flex-1 overflow-y-auto p-4 md:p-6 lg:p-8',
            contentClassName,
          )}
        >
          {children}
        </main>
      </div>
    </div>
  );
}

export interface LayoutContentProps {
  children: ReactNode;
  className?: string;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
}

const maxWidthStyles = {
  sm: 'max-w-3xl',
  md: 'max-w-5xl',
  lg: 'max-w-7xl',
  xl: 'max-w-[1600px]',
  full: 'max-w-full',
};

export function LayoutContent({ children, className, maxWidth = 'xl' }: LayoutContentProps) {
  return (
    <div className={cn('mx-auto w-full', maxWidthStyles[maxWidth], className)}>
      {children}
    </div>
  );
}

export interface LayoutSplitProps {
  left: ReactNode;
  right: ReactNode;
  ratio?: '1:1' | '1:2' | '2:1' | '1:3' | '3:1';
  className?: string;
}

const ratioStyles = {
  '1:1': 'grid-cols-1 lg:grid-cols-2',
  '1:2': 'grid-cols-1 lg:grid-cols-[1fr_2fr]',
  '2:1': 'grid-cols-1 lg:grid-cols-[2fr_1fr]',
  '1:3': 'grid-cols-1 lg:grid-cols-[1fr_3fr]',
  '3:1': 'grid-cols-1 lg:grid-cols-[3fr_1fr]',
};

export function LayoutSplit({ left, right, ratio = '1:1', className }: LayoutSplitProps) {
  return (
    <div className={cn('grid gap-6', ratioStyles[ratio], className)}>
      <div>{left}</div>
      <div>{right}</div>
    </div>
  );
}
