import { LoadingSpinner, ErrorDisplay, EmptyState } from "./PageComponents";

interface AsyncBoundaryProps {
  isLoading: boolean;
  isError: boolean;
  error?: Error | null;
  isEmpty?: boolean;
  emptyMessage?: string;
  onRetry?: () => void;
  loadingFallback?: React.ReactNode;
  errorFallback?: React.ReactNode;
  emptyFallback?: React.ReactNode;
  children: React.ReactNode;
}

export function AsyncBoundary({
  isLoading,
  isError,
  error,
  isEmpty = false,
  emptyMessage,
  onRetry,
  loadingFallback,
  errorFallback,
  emptyFallback,
  children,
}: AsyncBoundaryProps) {
  if (isLoading) {
    return loadingFallback ?? <LoadingSpinner />;
  }

  if (isError) {
    return errorFallback ?? <ErrorDisplay error={error?.message} onRetry={onRetry} />;
  }

  if (isEmpty) {
    return emptyFallback ?? <EmptyState title={emptyMessage ?? "No data"} />;
  }

  return <>{children}</>;
}
