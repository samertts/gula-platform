import { useState, useRef, useCallback, useEffect } from 'react';
import { cn } from '@gula/ui-platform';
import { barcodeService } from '@/services/barcode';

interface BarcodeScannerProps {
  onScan: (barcode: string, parsed: ReturnType<typeof barcodeService.parseBarcode>) => void;
  onError?: (error: string) => void;
  continuous?: boolean;
  autoStart?: boolean;
  className?: string;
  placeholder?: string;
}

export function BarcodeScanner({
  onScan,
  onError,
  continuous = false,
  autoStart = true,
  className,
  placeholder = 'امسح الباركود أو أدخل الرقم يدوياً',
}: BarcodeScannerProps) {
  const [inputValue, setInputValue] = useState('');
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [lastScanned, setLastScanned] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const lastScannedRef = useRef<string>('');

  const handleBarcode = useCallback((barcode: string) => {
    const trimmed = barcode.trim();
    if (!trimmed || trimmed === lastScannedRef.current) return;
    lastScannedRef.current = trimmed;
    const parsed = barcodeService.parseBarcode(trimmed);
    onScan(trimmed, parsed);
    setLastScanned(trimmed);
    setInputValue('');

    if (!continuous) {
      setScanning(false);
      stopCamera();
    }

    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      lastScannedRef.current = '';
    }, 2000);
  }, [onScan, continuous]);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsCameraActive(false);
  }, []);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 480 } },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setIsCameraActive(true);
    } catch (e) {
      onError?.((e as Error).message || 'تعذر الوصول إلى الكاميرا');
      setIsCameraActive(false);
    }
  }, [onError]);

  useEffect(() => {
    if (autoStart) {
      inputRef.current?.focus();
    }
    return () => {
      stopCamera();
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [autoStart, stopCamera]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && inputValue.trim()) {
      handleBarcode(inputValue.trim());
    }
  };

  const toggleCamera = () => {
    if (isCameraActive) {
      stopCamera();
    } else {
      startCamera();
    }
  };

  return (
    <div className={cn('space-y-3', className)}>
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={e => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="w-full px-4 py-3.5 pr-12 pl-4 bg-white dark:bg-neutral-800 border-2 border-neutral-200 dark:border-neutral-700 rounded-2xl text-sm font-medium focus:border-primary-500 dark:focus:border-primary-400 focus:outline-none transition-colors dark:text-neutral-100"
          autoFocus
          dir="auto"
        />
        <button
          type="button"
          onClick={toggleCamera}
          className={cn(
            'absolute left-2 top-1/2 -translate-y-1/2 p-2 rounded-xl transition-colors',
            isCameraActive
              ? 'bg-danger-50 text-danger-600 dark:bg-danger-900/30 dark:text-danger-400'
              : 'text-neutral-400 hover:text-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/30',
          )}
          title={isCameraActive ? 'إيقاف الكاميرا' : 'مسح بالكاميرا'}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
            <circle cx="12" cy="13" r="3" />
          </svg>
        </button>
      </div>

      {isCameraActive && (
        <div className="relative rounded-2xl overflow-hidden bg-black aspect-video">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 border-2 border-primary-500/50 rounded-2xl pointer-events-none">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3/4 h-1 border-t-2 border-primary-500" />
          </div>
          <button
            type="button"
            onClick={stopCamera}
            className="absolute top-2 right-2 p-2 bg-black/50 text-white rounded-xl hover:bg-black/70 transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {scanning && (
        <div className="text-center py-2">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 rounded-xl text-sm font-medium">
            <div className="w-4 h-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
            جاري المسح...
          </div>
        </div>
      )}

      {lastScanned && (
        <div className="flex items-center gap-2 px-4 py-2.5 bg-success-50 dark:bg-success-900/30 text-success-600 dark:text-success-400 rounded-xl text-sm font-medium">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          <span dir="ltr" className="font-mono text-xs">{lastScanned}</span>
        </div>
      )}
    </div>
  );
}
