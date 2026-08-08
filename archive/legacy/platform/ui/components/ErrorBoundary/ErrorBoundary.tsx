import { Component, type ErrorInfo, type ReactNode } from 'react';

export interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: (args: { error: Error; reset: () => void }) => ReactNode;
  resetKey?: string | number;
  onError?: (error: Error, info: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps) {
    if (prevProps.resetKey !== this.props.resetKey && this.state.error) {
      this.setState({ error: null });
    }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    this.props.onError?.(error, info);
  }

  reset = () => {
    this.setState({ error: null });
  };

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;

    if (this.props.fallback) {
      return this.props.fallback({ error, reset: this.reset });
    }

    return (
      <div
        role="alert"
        className="min-h-[40vh] flex items-center justify-center p-8"
      >
        <div className="max-w-md w-full bg-white dark:bg-neutral-900 border border-danger-200 dark:border-danger-800 rounded-3xl shadow-xl p-8 text-center space-y-4">
          <div className="mx-auto w-14 h-14 rounded-2xl bg-danger-50 dark:bg-danger-900/20 text-danger-500 flex items-center justify-center">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <circle cx="14" cy="14" r="11" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M14 9v6M14 19v.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </div>
          <div>
            <h2 className="text-xl font-bold text-neutral-900 dark:text-neutral-50">
              Something went wrong
            </h2>
            <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
              An unexpected error occurred. You can try again or refresh the page.
            </p>
          </div>
          <pre className="bg-neutral-50 dark:bg-neutral-800 text-left text-xs font-mono text-neutral-500 dark:text-neutral-400 p-3 rounded-xl overflow-auto max-h-24">
            {error.message || String(error)}
          </pre>
          <div className="flex items-center justify-center gap-3">
            <button
              type="button"
              onClick={this.reset}
              className="px-5 py-2.5 bg-primary-500 text-white text-sm font-bold rounded-xl hover:bg-primary-600 active:scale-95 transition-all flex items-center gap-2 shadow-sm"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M2 8a6 6 0 0111.3-3M14 3v3h-3M14 8a6 6 0 01-11.3 3M2 13v-3h3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Retry
            </button>
            <button
              type="button"
              onClick={() => window.location.href = '/'}
              className="px-5 py-2.5 bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 text-sm font-bold rounded-xl hover:bg-neutral-200 dark:hover:bg-neutral-700 active:scale-95 transition-all border border-neutral-200 dark:border-neutral-700"
            >
              Go home
            </button>
          </div>
        </div>
      </div>
    );
  }
}
