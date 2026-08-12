import { AlertCircle, FileSearch, LoaderCircle } from "lucide-react";

type StateKind = "loading" | "empty" | "error";

export function UiState({ kind, title, description, onRetry }: { kind: StateKind; title: string; description: string; onRetry?: () => void }) {
  const Icon = kind === "loading" ? LoaderCircle : kind === "error" ? AlertCircle : FileSearch;
  return (
    <div className={`ui-state ui-state--${kind}`} role={kind === "error" ? "alert" : "status"} aria-live="polite">
      <span className="ui-state__icon"><Icon size={22} className={kind === "loading" ? "spin" : ""} /></span>
      <div>
        <h3>{title}</h3>
        <p>{description}</p>
        {onRetry ? <button className="text-button" onClick={onRetry}>إعادة المحاولة</button> : null}
      </div>
    </div>
  );
}
