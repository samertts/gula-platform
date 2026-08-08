import { type ReactNode } from 'react';
import { cn } from '../../utils/cn';

export type AuthState = 'loading' | 'authenticated' | 'unauthenticated';

export interface ProtectedRouteProps {
  children: ReactNode;
  isAuthenticated: boolean;
  authState?: AuthState;
  requiredRoles?: string[];
  userRole?: string;
  fallback?: ReactNode;
  loadingFallback?: ReactNode;
  unauthorizedFallback?: ReactNode;
  redirectTo?: string;
}

export function ProtectedRoute({
  children,
  isAuthenticated,
  authState = isAuthenticated ? 'authenticated' : 'unauthenticated',
  requiredRoles,
  userRole,
  fallback,
  loadingFallback,
  unauthorizedFallback,
  redirectTo,
}: ProtectedRouteProps) {
  if (authState === 'loading') {
    if (loadingFallback) return <>{loadingFallback}</>;
    return (
      <div className="min-h-[40vh] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <svg className="animate-spin w-8 h-8 text-primary-500" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 font-medium">Verifying access...</p>
        </div>
      </div>
    );
  }

  if (authState === 'unauthenticated' || !isAuthenticated) {
    if (fallback) return <>{fallback}</>;
    if (redirectTo && typeof window !== 'undefined') {
      window.location.href = redirectTo;
      return null;
    }
    return (
      <div className="min-h-[40vh] flex items-center justify-center">
        <div className="text-center">
          <div className="mx-auto w-14 h-14 rounded-2xl bg-warning-50 dark:bg-warning-900/20 text-warning-500 flex items-center justify-center mb-4">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <path d="M14 4L3 23h22L14 4z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
              <path d="M14 11v4M14 19v.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </div>
          <h2 className="text-xl font-bold text-neutral-900 dark:text-neutral-50">Authentication required</h2>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">Please sign in to access this page.</p>
        </div>
      </div>
    );
  }

  if (requiredRoles && requiredRoles.length > 0 && userRole && !requiredRoles.includes(userRole)) {
    if (unauthorizedFallback) return <>{unauthorizedFallback}</>;
    return (
      <div className="min-h-[40vh] flex items-center justify-center">
        <div className="text-center">
          <div className="mx-auto w-14 h-14 rounded-2xl bg-danger-50 dark:bg-danger-900/20 text-danger-500 flex items-center justify-center mb-4">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <rect x="4" y="11" width="20" height="13" rx="3" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M9 11V8a5 5 0 0110 0v3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </div>
          <h2 className="text-xl font-bold text-neutral-900 dark:text-neutral-50">Access denied</h2>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            You do not have the required permissions to view this page.
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
