import React from 'react';
import { useI18n } from '../i18n';
import { ErrorProvider } from '../errors';

interface AppShellProps {
  children: React.ReactNode;
  header?: React.ReactNode;
  sidebar?: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
}

export const AppShell: React.FC<AppShellProps> = ({ children, header, sidebar, footer, className }) => {
  const { direction } = useI18n();

  return (
    <div
      className={`flex min-h-screen bg-neutral-50 dark:bg-neutral-950 ${direction === 'rtl' ? 'rtl' : 'ltr'}`}
      dir={direction}
    >
      {sidebar && (
        <aside className="fixed top-0 bottom-0 z-30 w-72 border-l border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
          {sidebar}
        </aside>
      )}
      <div className={`flex-1 flex flex-col ${sidebar ? 'mr-72' : ''}`}>
        {header && (
          <header className="sticky top-0 z-20 bg-white/80 dark:bg-neutral-900/80 backdrop-blur-lg border-b border-neutral-200 dark:border-neutral-800">
            {header}
          </header>
        )}
        <main className={`flex-1 ${className || ''}`}>
          <ErrorProvider>{children}</ErrorProvider>
        </main>
        {footer && (
          <footer className="border-t border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900">
            {footer}
          </footer>
        )}
      </div>
    </div>
  );
};

export const SplashScreen: React.FC<{ message?: string }> = ({ message }) => (
  <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-white dark:bg-neutral-950">
    <div className="w-16 h-16 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
    {message && <p className="mt-4 text-sm text-neutral-500">{message}</p>}
  </div>
);
