import { useEffect, useRef, useState, useCallback } from 'react';

interface QRScannerProps {
  onScan: (data: string) => void;
  onError?: (error: string) => void;
  continuous?: boolean;
  className?: string;
}

export function QRScanner({ onScan, onError, continuous = false, className = '' }: QRScannerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const scannerRef = useRef<any>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);

  const startScanning = useCallback(async () => {
    try {
      const { Html5Qrcode } = await import('html5-qrcode');
      const scanner = new Html5Qrcode('qr-reader');
      scannerRef.current = scanner;

      await scanner.start(
        { facingMode: 'environment' },
        {
          fps: 10,
          qrbox: { width: 250, height: 250 },
        },
        (decodedText: string) => {
          onScan(decodedText);
          if (!continuous) {
            scanner.stop().catch(() => {});
            setIsScanning(false);
          }
        },
        () => {},
      );

      setHasPermission(true);
      setIsScanning(true);
    } catch (err) {
      const message = (err as Error).message || 'فشل تشغيل الماسح';
      setHasPermission(false);
      onError?.(message);
    }
  }, [onScan, onError, continuous]);

  const stopScanning = useCallback(async () => {
    if (scannerRef.current) {
      try {
        await scannerRef.current.stop();
      } catch {}
      scannerRef.current = null;
    }
    setIsScanning(false);
  }, []);

  useEffect(() => {
    return () => {
      stopScanning();
    };
  }, [stopScanning]);

  if (hasPermission === false) {
    return (
      <div className={`flex flex-col items-center justify-center p-8 bg-neutral-50 dark:bg-neutral-800 rounded-2xl ${className}`}>
        <svg className="w-12 h-12 text-danger-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
        </svg>
        <p className="text-sm font-bold text-neutral-700 dark:text-neutral-300 text-center">
          لم يتم منح إذن الكاميرا
        </p>
        <p className="text-xs text-neutral-500 mt-1 text-center">
          الرجاء السماح بالوصول إلى الكاميرا في إعدادات المتصفح
        </p>
        <button
          onClick={startScanning}
          className="mt-4 px-6 py-2 bg-primary-500 text-white rounded-xl text-sm font-bold"
        >
          إعادة المحاولة
        </button>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      <div id="qr-reader" className="overflow-hidden rounded-2xl" />
      {!isScanning && (
        <div className="absolute inset-0 flex items-center justify-center bg-neutral-900/30 backdrop-blur-sm rounded-2xl">
          <button
            onClick={startScanning}
            className="px-6 py-3 bg-white text-neutral-900 rounded-2xl text-sm font-bold shadow-lg hover:bg-neutral-50 transition-colors flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            بدء المسح
          </button>
        </div>
      )}
      {isScanning && (
        <div className="absolute inset-0 border-2 border-primary-500 rounded-2xl pointer-events-none">
          <div className="absolute inset-x-4 top-1/2 h-0.5 bg-primary-500 animate-pulse" />
        </div>
      )}
    </div>
  );
}
