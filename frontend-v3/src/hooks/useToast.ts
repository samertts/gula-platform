import { useState, useCallback } from "react";

interface Toast {
  id: string;
  variant?: "default" | "destructive" | "success";
  title?: string;
  description?: string;
}

let toastListeners: Array<(toast: Toast) => void> = [];
let toastCount = 0;

export function toast(props: Omit<Toast, "id">) {
  const id = String(++toastCount);
  const t: Toast = { id, ...props };
  toastListeners.forEach((fn) => fn(t));
  return id;
}

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((t: Toast) => {
    setToasts((prev) => [...prev, t]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((x) => x.id !== t.id));
    }, 5000);
  }, []);

  useState(() => {
    toastListeners.push(addToast);
    return () => {
      toastListeners = toastListeners.filter((fn) => fn !== addToast);
    };
  });

  const dismiss = (id: string) => {
    setToasts((prev) => prev.filter((x) => x.id !== id));
  };

  return { toasts, toast, dismiss };
}
