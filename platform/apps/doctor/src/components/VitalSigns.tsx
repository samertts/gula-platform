import { Card, CardHeader, CardBody, Badge } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import type { VitalSigns as VitalSignsData } from '../services/clinical';

interface VitalSignsProps {
  vitals: VitalSignsData;
  showHistory?: boolean;
  history?: VitalSignsData[];
  onRecord?: () => void;
}

interface VitalItem {
  label: string;
  labelAr: string;
  value: string | number;
  unit: string;
  normalRange?: string;
  flag?: 'normal' | 'high' | 'low' | 'critical';
}

export function VitalSigns({ vitals, showHistory, history, onRecord }: VitalSignsProps) {
  const { isRtl } = useRTL();

  const items: VitalItem[] = [
    {
      label: 'Blood Pressure',
      labelAr: 'ضغط الدم',
      value: `${vitals.bloodPressureSystolic}/${vitals.bloodPressureDiastolic}`,
      unit: 'mmHg',
      normalRange: '120/80',
      flag: vitals.bloodPressureSystolic > 140 ? 'high' : vitals.bloodPressureSystolic < 90 ? 'low' : 'normal',
    },
    {
      label: 'Heart Rate',
      labelAr: 'معدل ضربات القلب',
      value: vitals.heartRate,
      unit: 'bpm',
      normalRange: '60-100',
      flag: vitals.heartRate > 100 ? 'high' : vitals.heartRate < 60 ? 'low' : 'normal',
    },
    {
      label: 'Temperature',
      labelAr: 'درجة الحرارة',
      value: vitals.temperature.toFixed(1),
      unit: '°C',
      normalRange: '36.5-37.5',
      flag: vitals.temperature > 38 ? 'high' : vitals.temperature < 36 ? 'low' : 'normal',
    },
    {
      label: 'Respiratory Rate',
      labelAr: 'معدل التنفس',
      value: vitals.respiratoryRate,
      unit: 'rpm',
      normalRange: '12-20',
      flag: vitals.respiratoryRate > 20 ? 'high' : vitals.respiratoryRate < 12 ? 'low' : 'normal',
    },
    {
      label: 'O2 Saturation',
      labelAr: 'تشبع الأكسجين',
      value: vitals.oxygenSaturation,
      unit: '%',
      normalRange: '95-100',
      flag: vitals.oxygenSaturation < 90 ? 'critical' : vitals.oxygenSaturation < 95 ? 'low' : 'normal',
    },
  ];

  if (vitals.bloodGlucose !== undefined) {
    items.push({
      label: 'Blood Glucose',
      labelAr: 'سكر الدم',
      value: vitals.bloodGlucose,
      unit: 'mg/dL',
      normalRange: '70-140',
      flag: vitals.bloodGlucose > 180 ? 'high' : vitals.bloodGlucose < 70 ? 'low' : 'normal',
    });
  }

  const flagColors = {
    normal: 'bg-success-100 text-success-700 dark:bg-success-900/20 dark:text-success-400',
    high: 'bg-warning-100 text-warning-700 dark:bg-warning-900/20 dark:text-warning-400',
    low: 'bg-warning-100 text-warning-700 dark:bg-warning-900/20 dark:text-warning-400',
    critical: 'bg-danger-100 text-danger-700 dark:bg-danger-900/20 dark:text-danger-400 animate-pulse',
  };

  return (
    <Card>
      <CardHeader
        title={isRtl ? 'العلامات الحيوية' : 'Vital Signs'}
        subtitle={`${new Date(vitals.recordedAt).toLocaleDateString(isRtl ? 'ar-IQ' : 'en-US')} ${new Date(vitals.recordedAt).toLocaleTimeString(isRtl ? 'ar-IQ' : 'en-US', { hour: '2-digit', minute: '2-digit' })}`}
        action={onRecord && (
          <button onClick={onRecord} className="text-sm text-primary-600 dark:text-primary-400 hover:underline">
            {isRtl ? 'تسجيل' : 'Record'}
          </button>
        )}
      />
      <CardBody>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {items.map(item => (
            <div
              key={item.label}
              className="p-3 rounded-xl bg-neutral-50 dark:bg-neutral-900 border border-neutral-100 dark:border-neutral-800"
            >
              <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-1">
                {isRtl ? item.labelAr : item.label}
              </p>
              <div className="flex items-baseline gap-1">
                <span className={`text-lg font-bold ${flagColors[item.flag || 'normal'].split(' ')[0].replace('bg-', 'text-')}`}>
                  {item.value}
                </span>
                <span className="text-xs text-neutral-400">{item.unit}</span>
              </div>
              {item.flag && item.flag !== 'normal' && (
                <Badge
                  variant={item.flag === 'critical' ? 'danger' : 'warning'}
                  size="xs"
                  className="mt-1"
                >
                  {item.flag === 'critical' ? (isRtl ? 'حرج' : 'Critical') : item.flag === 'high' ? (isRtl ? 'مرتفع' : 'High') : (isRtl ? 'منخفض' : 'Low')}
                </Badge>
              )}
            </div>
          ))}
        </div>

        {showHistory && history && history.length > 1 && (
          <div className="mt-4 pt-4 border-t border-neutral-100 dark:border-neutral-700">
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-2">
              {isRtl ? 'آخر القياسات' : 'Recent Measurements'}
            </p>
            <div className="flex gap-2 overflow-x-auto pb-2">
              {history.slice(-5).reverse().map((v, i) => (
                <div key={i} className="shrink-0 p-2 rounded-lg bg-neutral-50 dark:bg-neutral-900 text-center min-w-[70px]">
                  <p className="text-[10px] text-neutral-400">
                    {new Date(v.recordedAt).toLocaleTimeString(isRtl ? 'ar-IQ' : 'en-US', { hour: '2-digit', minute: '2-digit' })}
                  </p>
                  <p className="text-xs font-bold">{v.bloodPressureSystolic}/{v.bloodPressureDiastolic}</p>
                  <p className="text-[10px] text-neutral-400">{v.heartRate}bpm</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardBody>
    </Card>
  );
}
