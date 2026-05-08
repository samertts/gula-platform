import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface Props {
  /** Children to protect. */
  children: ReactNode;
  /**
   * When this prop changes, the boundary auto-resets. Pass `location.pathname`
   * so a route change clears any prior error.
   */
  resetKey?: string | number;
  /** Optional custom render override. */
  fallback?: (args: { error: Error; reset: () => void }) => ReactNode;
}

interface State {
  error: Error | null;
}

/**
 * Route-level error boundary. Catches render-time exceptions in any descendant
 * so a single broken view does not blank the entire shell.
 *
 * Notes:
 *   - Async errors thrown outside React's render path are NOT caught — wrap
 *     async work in `try/catch` and surface them via state instead.
 *   - The default fallback offers Retry (re-mount the subtree) and Home.
 */
export class RouteErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidUpdate(prevProps: Props) {
    if (prevProps.resetKey !== this.props.resetKey && this.state.error) {
      this.setState({ error: null });
    }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Surface to console for now. A future hook into Sentry/Telegram alerts
    // would plug in here without changing call sites.
    if (typeof console !== 'undefined') {
      // eslint-disable-next-line no-console
      console.error('[RouteErrorBoundary]', error, info.componentStack);
    }
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
        className="min-h-[60vh] flex items-center justify-center p-8"
        data-testid="route-error-boundary"
      >
        <div className="max-w-lg w-full bg-white border border-rose-100 rounded-3xl shadow-xl shadow-rose-100/40 p-10 text-center space-y-5">
          <div className="mx-auto w-16 h-16 rounded-2xl bg-rose-50 text-rose-500 flex items-center justify-center">
            <AlertTriangle size={32} strokeWidth={1.5} />
          </div>
          <div>
            <h2 className="font-headline text-2xl font-black tracking-tight text-slate-900">
              Something went wrong on this page
            </h2>
            <p className="text-sm text-slate-500 mt-2 leading-relaxed">
              The rest of the platform is unaffected. You can retry, go back
              home, or report this if it keeps happening.
            </p>
          </div>
          <pre className="bg-slate-50 text-left text-[11px] font-mono text-slate-500 p-4 rounded-xl overflow-auto max-h-32">
            {error.message || String(error)}
          </pre>
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <button
              type="button"
              onClick={this.reset}
              className="px-5 py-2.5 bg-indigo-600 text-white text-sm font-bold rounded-xl shadow-sm hover:bg-indigo-700 active:scale-95 transition-all flex items-center gap-2"
            >
              <RefreshCw size={16} /> Retry
            </button>
            <a
              href="/"
              className="px-5 py-2.5 bg-slate-50 text-slate-700 border border-slate-100 text-sm font-bold rounded-xl hover:bg-slate-100 active:scale-95 transition-all flex items-center gap-2"
            >
              <Home size={16} /> Go home
            </a>
          </div>
        </div>
      </div>
    );
  }
}
