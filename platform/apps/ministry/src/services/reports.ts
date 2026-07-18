import type { NationalReport, ReportConfig } from './api';

export interface ReportTemplate {
  id: string;
  name: string;
  nameAr: string;
  description: string;
  descriptionAr: string;
  category: 'surveillance' | 'statistics' | 'vaccination' | 'mortality' | 'workforce' | 'comprehensive';
  defaultConfig: Partial<ReportConfig>;
}

export const REPORT_TEMPLATES: ReportTemplate[] = [
  {
    id: 'weekly-surveillance',
    name: 'Weekly Surveillance Report',
    nameAr: 'تقرير الترصد الأسبوعي',
    description: 'Comprehensive disease surveillance report with outbreak tracking',
    descriptionAr: 'تقرير شامل لترصد الأمراض مع تتبع الفاشيات',
    category: 'surveillance',
    defaultConfig: { type: 'detailed', sections: ['surveillance', 'outbreaks', 'regions'] },
  },
  {
    id: 'monthly-statistics',
    name: 'Monthly Health Statistics',
    nameAr: 'الإحصاءات الصحية الشهرية',
    description: 'National health statistics with KPI trends',
    descriptionAr: 'إحصاءات صحية وطنية مع اتجاهات مؤشرات الأداء',
    category: 'statistics',
    defaultConfig: { type: 'summary', sections: ['kpis', 'hospitals', 'labs'] },
  },
  {
    id: 'vaccination-coverage',
    name: 'Vaccination Coverage Report',
    nameAr: 'تقرير تغطية التطعيم',
    description: 'Vaccination coverage by region and demographic',
    descriptionAr: 'تغطية التطعيم حسب المنطقة والديموغرافيا',
    category: 'vaccination',
    defaultConfig: { type: 'detailed', sections: ['vaccination', 'coverage', 'doses'] },
  },
  {
    id: 'mortality-analysis',
    name: 'Mortality Analysis Report',
    nameAr: 'تقرير تحليل الوفيات',
    description: 'Mortality statistics and cause analysis',
    descriptionAr: 'إحصاءات الوفيات وتحليل الأسباب',
    category: 'mortality',
    defaultConfig: { type: 'detailed', sections: ['mortality', 'causes', 'demographics'] },
  },
  {
    id: 'workforce-report',
    name: 'Health Workforce Report',
    nameAr: 'تقرير القوى العاملة الصحية',
    description: 'Health workforce distribution and vacancies',
    descriptionAr: 'توزيع القوى العاملة الصحية والوظائف الشاغرة',
    category: 'workforce',
    defaultConfig: { type: 'summary', sections: ['workforce', 'specialists', 'vacancies'] },
  },
  {
    id: 'comprehensive-national',
    name: 'Comprehensive National Report',
    nameAr: 'التقرير الوطني الشامل',
    description: 'Full national health system status report',
    descriptionAr: 'تقرير شامل عن حالة النظام الصحي الوطني',
    category: 'comprehensive',
    defaultConfig: { type: 'comparative', sections: ['all'] },
  },
];

export function formatReportPeriod(dateFrom: string, dateTo: string): string {
  const from = new Date(dateFrom);
  const to = new Date(dateTo);
  const options: Intl.DateTimeFormatOptions = { year: 'numeric', month: 'long', day: 'numeric' };
  return `${from.toLocaleDateString('ar-IQ', options)} - ${to.toLocaleDateString('ar-IQ', options)}`;
}

export function getReportStatusColor(status: NationalReport['status']): string {
  switch (status) {
    case 'generating': return 'text-amber-400';
    case 'ready': return 'text-emerald-400';
    case 'failed': return 'text-rose-400';
    default: return 'text-slate-400';
  }
}

export function getReportStatusLabel(status: NationalReport['status']): string {
  switch (status) {
    case 'generating': return 'جاري التوليد';
    case 'ready': return 'جاهز';
    case 'failed': return 'فشل';
    default: return 'غير معروف';
  }
}
