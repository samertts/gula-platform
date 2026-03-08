import React, { createContext, useContext, useState, useCallback, useEffect } from "react";

/* ---- Types ---- */
type ToastType = "success" | "error" | "warning" | "info";

interface ToastItem {
  id:      string;
  type:    ToastType;
  message: string;
  duration?: number;
}

interface ToastCtx {
  toast: (msg: string, type?: ToastType, duration?: number) => void;
  success: (msg: string) => void;
  error:   (msg: string) => void;
  warning: (msg: string) => void;
  info:    (msg: string) => void;
}

/* ---- Context ---- */
const ToastContext = createContext<ToastCtx | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const toast = useCallback((message: string, type: ToastType = "info", duration = 4000) => {
    const id = Math.random().toString(36).slice(2);
    setToasts(prev => [...prev, { id, type, message, duration }]);
  }, []);

  const remove = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{
      toast,
      success: (m) => toast(m, "success"),
      error:   (m) => toast(m, "error", 6000),
      warning: (m) => toast(m, "warning"),
      info:    (m) => toast(m, "info"),
    }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={remove} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be inside ToastProvider");
  return ctx;
}

/* ---- Toast Item Component ---- */
function ToastItem({ toast, onRemove }: { toast: ToastItem; onRemove: (id: string) => void }) {
  useEffect(() => {
    const t = setTimeout(() => onRemove(toast.id), toast.duration ?? 4000);
    return () => clearTimeout(t);
  }, [toast, onRemove]);

  const ICONS: Record<ToastType, string> = {
    success: "✓",
    error:   "✕",
    warning: "⚠",
    info:    "ℹ",
  };

  const COLORS: Record<ToastType, string> = {
    success: "var(--success)",
    error:   "var(--danger)",
    warning: "var(--warning)",
    info:    "var(--primary)",
  };

  const BG: Record<ToastType, string> = {
    success: "var(--success-lt)",
    error:   "var(--danger-lt)",
    warning: "var(--warning-lt)",
    info:    "var(--primary-lt)",
  };

  return (
    <div style={{
      display:      "flex",
      alignItems:   "flex-start",
      gap:          10,
      background:   BG[toast.type],
      border:       `1px solid ${COLORS[toast.type]}40`,
      borderRight:  `4px solid ${COLORS[toast.type]}`,
      borderRadius: "var(--radius)",
      padding:      "12px 14px",
      boxShadow:    "var(--shadow-md)",
      animation:    "slideIn .2s ease",
      minWidth:     280,
      maxWidth:     360,
    }}>
      <span style={{
        width:          24, height: 24, borderRadius: "50%",
        background:     COLORS[toast.type],
        color:          "#fff",
        display:        "flex", alignItems: "center", justifyContent: "center",
        fontWeight:     700, fontSize: ".8rem", flexShrink: 0,
      }}>
        {ICONS[toast.type]}
      </span>
      <span style={{ flex: 1, fontSize: ".875rem", color: "var(--gray-900)", lineHeight: 1.5 }}>
        {toast.message}
      </span>
      <button onClick={() => onRemove(toast.id)} style={{
        background: "none", border: "none", cursor: "pointer",
        color: "var(--gray-400)", padding: "0 2px", fontSize: "1rem", lineHeight: 1
      }}>×</button>
    </div>
  );
}

/* ---- Container ---- */
function ToastContainer({ toasts, onRemove }: { toasts: ToastItem[]; onRemove: (id: string) => void }) {
  if (!toasts.length) return null;

  return (
    <>
      <style>{`
        @keyframes slideIn {
          from { transform: translateX(100%); opacity: 0; }
          to   { transform: translateX(0);    opacity: 1; }
        }
      `}</style>
      <div style={{
        position:  "fixed",
        bottom:    24,
        left:      24,
        zIndex:    9999,
        display:   "flex",
        flexDirection: "column",
        gap:       10,
      }}>
        {toasts.map(t => (
          <ToastItem key={t.id} toast={t} onRemove={onRemove} />
        ))}
      </div>
    </>
  );
}
