import { useOffline } from '../contexts/OfflineContext';

export function OfflineIndicator() {
  const { isOffline, queueLength } = useOffline();

  if (!isOffline) return null;

  return (
    <div className="fixed top-14 inset-x-0 z-50 pointer-events-none">
      <div className="mx-auto max-w-lg px-4">
        <div className="bg-amber-500 text-white px-4 py-2 rounded-2xl shadow-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636a9 9 0 010 12.728m-2.829-2.829a5 5 0 000-7.07m-4.243 4.243a1 1 0 010-1.414" />
            </svg>
            <span className="text-xs font-bold">لا يوجد اتصال بالإنترنت</span>
          </div>
          {queueLength > 0 && (
            <span className="text-[10px] font-bold bg-white/20 px-2 py-0.5 rounded-lg">
              {queueLength} في الانتظار
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
