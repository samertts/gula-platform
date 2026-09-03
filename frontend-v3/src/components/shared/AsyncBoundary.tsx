import { ClinicalStatePanel, type ClinicalSurfaceState } from "@/components/clinical";
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
  clinicalState?: ClinicalSurfaceState;
  stateTitle?: string;
  stateDescription?: string;
  stateActionLabel?: string;
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
  clinicalState,
  stateTitle,
  stateDescription,
  stateActionLabel,
  children,
}: AsyncBoundaryProps) {
  if (clinicalState && clinicalState !== "loaded") {
    return <ClinicalStatePanel state={clinicalState} title={stateTitle} description={stateDescription} actionLabel={stateActionLabel} onAction={onRetry} />;
  }

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
