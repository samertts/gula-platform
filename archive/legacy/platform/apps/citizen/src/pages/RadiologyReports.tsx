import { useState } from 'react';
import { Button, cn } from '@gula/ui-platform';
import { useRadiologyReports } from '../hooks/useHealthData';
import type { RadiologyReport } from '../types';

const modalityLabels: Record<string, string> = {
  'X-ray': 'أشعة سينية',
  CT: 'مقطعي',
  MRI: 'رنين مغناطيسي',
  Ultrasound: 'موجات صوتية',
  Mammography: 'ماموغرام',
  PET: 'PET',
  Other: 'أخرى',
};

const modalityColors: Record<string, string> = {
  'X-ray': 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
  CT: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400',
  MRI: 'bg-cyan-100 text-cyan-600 dark:bg-cyan-900/30 dark:text-cyan-400',
  Ultrasound: 'bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400',
  Mammography: 'bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400',
  PET: 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400',
  Other: 'bg-neutral-100 text-neutral-600 dark:bg-neutral-900/30 dark:text-neutral-400',
};

const statusLabels: Record<string, string> = {
  preliminary: 'أولي',
  final: 'نهائي',
  amended: 'معدل',
};

export function RadiologyReports() {
  const { data: reports, isLoading, error } = useRadiologyReports();
  const [selectedReport, setSelectedReport] = useState<RadiologyReport | null>(null);

  if (isLoading) {
    return (
      <div className="pb-24 px-4 pt-4 space-y-4">
        {[1, 2].map((i) => (
          <div key={i} className="bg-neutral-100 dark:bg-neutral-800 rounded-2xl h-48 animate-pulse" />
        ))}
      </div>
    );
  }

  if (selectedReport) {
    return (
      <div className="pb-24 px-4 pt-4">
        <button
          onClick={() => setSelectedReport(null)}
          className="flex items-center gap-2 text-primary-600 dark:text-primary-400 text-sm font-bold mb-4"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          العودة إلى القائمة
        </button>

        <div className="bg-white dark:bg-neutral-800 rounded-3xl p-6 border border-neutral-200 dark:border-neutral-700 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-black text-neutral-900 dark:text-neutral-50">
                {selectedReport.bodyPart}
              </h2>
              <p className="text-xs text-neutral-500">{selectedReport.facility}</p>
            </div>
            <span className={cn(
              'px-3 py-1 rounded-xl text-[10px] font-bold',
              modalityColors[selectedReport.modality] || 'bg-neutral-100 text-neutral-600',
            )}>
              {modalityLabels[selectedReport.modality] || selectedReport.modality}
            </span>
          </div>

          <div className="space-y-4">
            <div>
              <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest mb-1">النتائج</p>
              <p className="text-sm text-neutral-700 dark:text-neutral-300 leading-relaxed">
                {selectedReport.findings}
              </p>
            </div>
            <div>
              <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest mb-1">الانطباع</p>
              <div className="p-4 bg-primary-50 dark:bg-primary-900/20 rounded-2xl">
                <p className="text-sm font-bold text-primary-700 dark:text-primary-400">
                  {selectedReport.impression}
                </p>
              </div>
            </div>
            <div className="flex items-center justify-between text-[10px] text-neutral-400 pt-4 border-t border-neutral-100 dark:border-neutral-700">
              <span>طبيب الأشعة: {selectedReport.radiologist}</span>
              <span className={cn(
                'px-2 py-0.5 rounded-lg font-bold',
                selectedReport.status === 'final' ? 'bg-success-50 text-success-600' : 'bg-warning-50 text-warning-600',
              )}>
                {statusLabels[selectedReport.status]}
              </span>
            </div>
            <div className="flex items-center justify-between text-[10px] text-neutral-400">
              <span>تاريخ الدراسة: {new Date(selectedReport.studyDate).toLocaleDateString('ar-IQ')}</span>
              <span>تاريخ التقرير: {new Date(selectedReport.reportDate).toLocaleDateString('ar-IQ')}</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="pb-24 px-4 pt-4">
      {reports.length === 0 ? (
        <div className="text-center py-16">
          <svg className="w-16 h-16 mx-auto text-neutral-300 dark:text-neutral-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-sm text-neutral-500 mb-2">لا توجد تقارير أشعة</p>
          <p className="text-[10px] text-neutral-400">سيتم عرض تقارير الأشعة هنا عند توفرها</p>
        </div>
      ) : (
        <div className="space-y-4">
          {reports.map((report) => (
            <button
              key={report.id}
              onClick={() => setSelectedReport(report)}
              className="w-full text-right bg-white dark:bg-neutral-800 rounded-2xl p-5 border border-neutral-200 dark:border-neutral-700 shadow-sm hover:shadow-md transition-all"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="min-w-0 flex-1">
                  <h3 className="font-bold text-neutral-900 dark:text-neutral-50 truncate">{report.bodyPart}</h3>
                  <p className="text-[10px] text-neutral-500 mt-0.5">{report.facility}</p>
                </div>
                <span className={cn('px-2 py-0.5 rounded-lg text-[10px] font-bold', modalityColors[report.modality])}>
                  {modalityLabels[report.modality]}
                </span>
              </div>
              <p className="text-xs text-neutral-600 dark:text-neutral-400 line-clamp-2">{report.impression}</p>
              <div className="flex items-center gap-3 mt-3 text-[10px] text-neutral-400">
                <span>{new Date(report.studyDate).toLocaleDateString('ar-IQ')}</span>
                <span className="w-1 h-1 rounded-full bg-neutral-300" />
                <span>{report.radiologist}</span>
                <span className={cn(
                  'px-1.5 py-0.5 rounded font-bold',
                  report.status === 'final' ? 'bg-success-50 text-success-600' : 'bg-warning-50 text-warning-600',
                )}>
                  {statusLabels[report.status]}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 rounded-2xl">
          <p className="text-xs text-danger-600 dark:text-danger-400">{error}</p>
        </div>
      )}
    </div>
  );
}
