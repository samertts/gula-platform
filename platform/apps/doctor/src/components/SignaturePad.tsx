import { useRef, useState, useCallback, useEffect } from 'react';
import { Card, CardHeader, CardBody, Button } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';

interface SignaturePadProps {
  onSave: (signatureData: string) => void;
  onClear?: () => void;
  width?: number;
  height?: number;
  label?: string;
  labelAr?: string;
}

export function SignaturePad({ onSave, onClear, width = 500, height = 200, label, labelAr }: SignaturePadProps) {
  const { isRtl } = useRTL();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [hasSignature, setHasSignature] = useState(false);
  const [signatureType, setSignatureType] = useState<'draw' | 'typed'>('draw');
  const [typedName, setTypedName] = useState('');

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.strokeStyle = '#1e3a5f';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
  }, []);

  const getPos = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    if ('touches' in e) {
      return {
        x: (e.touches[0].clientX - rect.left) * (canvas.width / rect.width),
        y: (e.touches[0].clientY - rect.top) * (canvas.height / rect.height),
      };
    }
    return {
      x: (e.clientX - rect.left) * (canvas.width / rect.width),
      y: (e.clientY - rect.top) * (canvas.height / rect.height),
    };
  }, []);

  const startDrawing = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault();
    const ctx = canvasRef.current?.getContext('2d');
    if (!ctx) return;
    const pos = getPos(e);
    ctx.beginPath();
    ctx.moveTo(pos.x, pos.y);
    setIsDrawing(true);
    setHasSignature(true);
  }, [getPos]);

  const draw = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault();
    if (!isDrawing) return;
    const ctx = canvasRef.current?.getContext('2d');
    if (!ctx) return;
    const pos = getPos(e);
    ctx.lineTo(pos.x, pos.y);
    ctx.stroke();
  }, [isDrawing, getPos]);

  const stopDrawing = useCallback(() => {
    setIsDrawing(false);
  }, []);

  const clearCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setHasSignature(false);
    setTypedName('');
    onClear?.();
  }, [onClear]);

  const saveSignature = useCallback(() => {
    if (signatureType === 'typed' && typedName.trim()) {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.font = '36px "Cairo", sans-serif';
      ctx.fillStyle = '#1e3a5f';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(typedName, canvas.width / 2, canvas.height / 2);
      setHasSignature(true);
    }

    const dataUrl = canvasRef.current?.toDataURL('image/png');
    if (dataUrl && hasSignature) {
      onSave(dataUrl);
    }
  }, [signatureType, typedName, hasSignature, onSave]);

  return (
    <Card>
      <CardHeader title={label || (isRtl ? 'التوقيع الرقمي' : 'Digital Signature')} />
      <CardBody>
        <div className="space-y-4">
          <div className="flex gap-2">
            <button
              onClick={() => setSignatureType('draw')}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                signatureType === 'draw'
                  ? 'bg-primary-500 text-white'
                  : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300'
              }`}
            >
              {isRtl ? 'رسم التوقيع' : 'Draw'}
            </button>
            <button
              onClick={() => setSignatureType('typed')}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                signatureType === 'typed'
                  ? 'bg-primary-500 text-white'
                  : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300'
              }`}
            >
              {isRtl ? 'كتابة الاسم' : 'Type'}
            </button>
          </div>

          {signatureType === 'draw' ? (
            <div className="border-2 border-neutral-200 dark:border-neutral-700 rounded-xl overflow-hidden touch-none">
              <canvas
                ref={canvasRef}
                width={width}
                height={height}
                className="w-full bg-white dark:bg-neutral-900 cursor-crosshair"
                style={{ touchAction: 'none' }}
                onMouseDown={startDrawing}
                onMouseMove={draw}
                onMouseUp={stopDrawing}
                onMouseLeave={stopDrawing}
                onTouchStart={startDrawing}
                onTouchMove={draw}
                onTouchEnd={stopDrawing}
              />
            </div>
          ) : (
            <input
              type="text"
              value={typedName}
              onChange={e => { setTypedName(e.target.value); setHasSignature(true); }}
              placeholder={isRtl ? 'اكتب اسمك الكامل' : 'Type your full name'}
              className="w-full rounded-xl border-2 border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 px-4 py-3 text-lg font-cairo text-center"
              dir={isRtl ? 'rtl' : 'ltr'}
            />
          )}

          <div className="flex gap-3">
            <Button variant="primary" onClick={saveSignature} disabled={!hasSignature}>
              {isRtl ? 'حفظ التوقيع' : 'Save Signature'}
            </Button>
            <Button variant="ghost" onClick={clearCanvas}>
              {isRtl ? 'مسح' : 'Clear'}
            </Button>
          </div>

          <p className="text-xs text-neutral-500 dark:text-neutral-400">
            {isRtl
              ? 'بالتوقيع، أنا أقر بأن المعلومات المذكورة أعلاه صحيحة.'
              : 'By signing, I confirm that the above information is correct.'}
          </p>
        </div>
      </CardBody>
    </Card>
  );
}
