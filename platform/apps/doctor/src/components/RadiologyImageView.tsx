import { useState } from 'react';
import { Card, CardHeader, CardBody, Badge, Button } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import type { RadiologyReport } from '../services/clinical';

interface RadiologyImageViewProps {
  report: RadiologyReport;
}

export function RadiologyImageView({ report }: RadiologyImageViewProps) {
  const { isRtl } = useRTL();
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const [brightness, setBrightness] = useState(100);
  const [contrast, setContrast] = useState(100);

  return (
    <Card>
      <CardHeader
        title={isRtl ? report.examTypeAr : report.examType}
        subtitle={`${report.bodyPart} | ${new Date(report.performedAt).toLocaleDateString(isRtl ? 'ar-IQ' : 'en-US')}`}
      />
      <CardBody>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            {report.images.length > 0 ? (
              <div className="space-y-3">
                <div
                  className="relative rounded-xl overflow-hidden bg-black cursor-crosshair"
                  style={{ minHeight: 300 }}
                >
                  {selectedImage ? (
                    <img
                      src={selectedImage}
                      alt={report.examType}
                      className="w-full h-full object-contain transition-transform"
                      style={{
                        transform: `scale(${zoom})`,
                        filter: `brightness(${brightness}%) contrast(${contrast}%)`,
                      }}
                    />
                  ) : (
                    <div className="flex items-center justify-center h-[300px] text-neutral-400">
                      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z" />
                        <circle cx="12" cy="13" r="4" />
                      </svg>
                    </div>
                  )}

                  {selectedImage && (
                    <div className="absolute bottom-3 left-3 right-3 flex items-center gap-2 bg-black/60 rounded-lg p-2">
                      <button onClick={() => setZoom(z => Math.min(z + 0.1, 3))} className="text-white text-sm px-2 py-1 hover:bg-white/20 rounded">+</button>
                      <span className="text-white text-xs">{Math.round(zoom * 100)}%</span>
                      <button onClick={() => setZoom(z => Math.max(z - 0.1, 0.5))} className="text-white text-sm px-2 py-1 hover:bg-white/20 rounded">-</button>
                      <div className="h-4 w-px bg-white/30 mx-1" />
                      <input type="range" min="50" max="150" value={brightness} onChange={e => setBrightness(Number(e.target.value))} className="w-20 accent-white" />
                      <input type="range" min="50" max="150" value={contrast} onChange={e => setContrast(Number(e.target.value))} className="w-20 accent-white" />
                    </div>
                  )}
                </div>

                {report.images.length > 1 && (
                  <div className="flex gap-2 overflow-x-auto pb-2">
                    {report.images.map((img, i) => (
                      <button
                        key={i}
                        onClick={() => setSelectedImage(img)}
                        className={`shrink-0 w-16 h-16 rounded-lg overflow-hidden border-2 transition-colors ${
                          selectedImage === img ? 'border-primary-500' : 'border-transparent'
                        }`}
                      >
                        <img src={img} alt="" className="w-full h-full object-cover" />
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-center h-[300px] rounded-xl bg-neutral-100 dark:bg-neutral-800">
                <p className="text-neutral-500">{isRtl ? 'لا توجد صور' : 'No images available'}</p>
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div>
              <p className="text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">
                {isRtl ? 'التقنية' : 'Technique'}
              </p>
              <p className="text-sm text-neutral-600 dark:text-neutral-400">
                {report.technique || (isRtl ? 'غير محدد' : 'Not specified')}
              </p>
            </div>

            <div>
              <p className="text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">
                {isRtl ? 'النتائج' : 'Findings'}
              </p>
              <div className="p-3 rounded-xl bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700">
                <p className="text-sm text-neutral-700 dark:text-neutral-300 whitespace-pre-wrap">
                  {isRtl ? report.findingsAr : report.findings}
                </p>
              </div>
            </div>

            <div>
              <p className="text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">
                {isRtl ? 'الانطباع' : 'Impression'}
              </p>
              <div className="p-3 rounded-xl bg-warning-50 dark:bg-warning-900/10 border border-warning-200 dark:border-warning-900/30">
                <p className="text-sm text-neutral-700 dark:text-neutral-300 whitespace-pre-wrap">
                  {isRtl ? report.impressionAr : report.impression}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Badge variant={report.status === 'verified' ? 'success' : report.status === 'completed' ? 'info' : 'warning'}>
                {report.status === 'verified' ? (isRtl ? 'موثق' : 'Verified') :
                 report.status === 'completed' ? (isRtl ? 'مكتمل' : 'Completed') :
                 (isRtl ? 'قيد الانتظار' : 'Pending')}
              </Badge>
              {report.radiologist && (
                <span className="text-xs text-neutral-500">
                  {isRtl ? 'أخصائي الأشعة' : 'Radiologist'}: {report.radiologist}
                </span>
              )}
            </div>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
