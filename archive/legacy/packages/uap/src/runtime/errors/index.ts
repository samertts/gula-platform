import React, { createContext, useContext, useState, useCallback } from 'react';

export type ErrorSeverity = 'info' | 'warning' | 'error' | 'fatal';

export interface AppError {
  id: string;
  message: string;
  details?: string;
  severity: ErrorSeverity;
  timestamp: number;
  recoverable: boolean;
  source?: string;
  handled?: boolean;
}

interface ErrorContextValue {
  errors: AppError[];
  captureError: (error: Omit<AppError, 'id' | 'timestamp'>) => void;
  dismissError: (id: string) => void;
  clearErrors: () => void;
  hasErrors: (severity?: ErrorSeverity) => boolean;
  lastError: AppError | null;
}

const ErrorContext = createContext<ErrorContextValue>({
  errors: [],
  captureError: () => {},
  dismissError: () => {},
  clearErrors: () => {},
  hasErrors: () => false,
  lastError: null,
});

export const useErrorHandler = () => useContext(ErrorContext);

export const ErrorProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [errors, setErrors] = useState<AppError[]>([]);

  const captureError = useCallback((error: Omit<AppError, 'id' | 'timestamp'>) => {
    const entry: AppError = {
      ...error,
      id: `err-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      timestamp: Date.now(),
    };
    setErrors((prev) => [entry, ...prev].slice(0, 50));
    if (error.severity === 'fatal') {
      console.error('[UAP Fatal]', error.message, error.details);
    }
  }, []);

  const dismissError = useCallback((id: string) => {
    setErrors((prev) => prev.filter((e) => e.id !== id));
  }, []);

  const clearErrors = useCallback(() => setErrors([]), []);

  const hasErrors = useCallback(
    (severity?: ErrorSeverity) =>
      severity ? errors.some((e) => e.severity === severity) : errors.length > 0,
    [errors]
  );

  return (
    <ErrorContext.Provider
      value={{
        errors,
        captureError,
        dismissError,
        clearErrors,
        hasErrors,
        lastError: errors[0] ?? null,
      }}
    >
      {children}
    </ErrorContext.Provider>
  );
};

export const AppErrorBoundary: React.FC<{ children: React.ReactNode; fallback?: React.ReactNode }> = ({
  children,
  fallback,
}) => {
  const [hasError, setHasError] = useState(false);

  const handleError = useCallback((error: Error) => {
    console.error('[UAP ErrorBoundary]', error);
    setHasError(true);
  }, []);

  if (hasError) {
    return fallback ? (
      <>{fallback}</>
    ) : (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <div className="text-error-500 text-4xl mb-4">!</div>
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">Something went wrong</h2>
        <p className="text-sm text-neutral-500 mt-1">An unexpected error occurred. Please try again.</p>
        <button
          onClick={() => setHasError(false)}
          className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  return <ErrorBoundaryInner onError={handleError}>{children}</ErrorBoundaryInner>;
};

class ErrorBoundaryInner extends React.Component<
  { children: React.ReactNode; onError: (error: Error) => void },
  { hasError: boolean }
> {
  constructor(props: { children: React.ReactNode; onError: (error: Error) => void }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error) {
    this.props.onError(error);
  }

  render() {
    if (this.state.hasError) return null;
    return this.props.children;
  }
}
