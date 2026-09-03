import { useEffect, useState } from "react";
import { CloudOff, Database, Wifi } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export function AppRuntimeIndicator() {
  const { demoMode } = useAuth();
  const [online, setOnline] = useState(() => typeof navigator === "undefined" || navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setOnline(true);
    const handleOffline = () => setOnline(false);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  if (demoMode) {
    return <span className="hidden items-center gap-1.5 rounded-lg border border-amber-200 bg-amber-50 px-2 py-1.5 text-[10px] font-semibold text-amber-800 sm:inline-flex dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-200" role="status" aria-label="وضع المعاينة: لا اتصال ببيانات حقيقية"><Database className="h-3.5 w-3.5" aria-hidden="true" />Demo · لا API</span>;
  }

  return <span className={`hidden items-center gap-1.5 rounded-lg border px-2 py-1.5 text-[10px] font-semibold sm:inline-flex ${online ? "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-200" : "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-200"}`} role="status" aria-live="polite" aria-label={online ? "متصل بالشبكة" : "دون اتصال بالشبكة"}>{online ? <Wifi className="h-3.5 w-3.5" aria-hidden="true" /> : <CloudOff className="h-3.5 w-3.5" aria-hidden="true" />}{online ? "متصل" : "دون اتصال"}</span>;
}
