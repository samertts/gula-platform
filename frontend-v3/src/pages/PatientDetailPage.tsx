import { useQuery } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { patients, orders, ehr, patientCard } from '@/api/endpoints';
import { Button } from '@/components/ui/Button';
import { StatusBadge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { useTranslation } from 'react-i18next';
import { formatDate, formatDateTime, getAge } from '@/lib/utils';
import { ArrowLeft, User, Phone, Calendar, Activity, FileText, Pill, HeartPulse } from 'lucide-react';

export function PatientDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const patientId = Number(id);

  const { data: patient, isLoading } = useQuery({
    queryKey: ['patient', patientId],
    queryFn: () => patients.get(patientId),
    enabled: !!patientId,
  });

  const { data: patientOrders } = useQuery({
    queryKey: ['patient-orders', patientId],
    queryFn: () => orders.list({ patient_id: patientId, limit: 20 }),
    enabled: !!patientId,
  });

  const { data: conditions } = useQuery({
    queryKey: ['patient-conditions', patientId],
    queryFn: () => ehr.conditions.list(patientId),
    enabled: !!patientId,
  });

  const { data: medications } = useQuery({
    queryKey: ['patient-medications', patientId],
    queryFn: () => ehr.medications.list(patientId),
    enabled: !!patientId,
  });

  if (isLoading) return <Skeleton className="h-96" />;
  if (!patient) return <EmptyState icon={User} title={t('noData')} />;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/patients" className="p-2 rounded-lg hover:bg-surface-container-high">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <h1 className="text-2xl font-bold text-on-surface">{patient.full_name}</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-4">
          <div className="rounded-xl border border-outline bg-surface p-5 space-y-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                <User className="h-8 w-8 text-primary" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-on-surface">{patient.full_name}</h2>
                <p className="text-sm text-on-surface-variant">#{patient.health_id || patient.id}</p>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm">
                <Phone className="h-4 w-4 text-on-surface-variant" />
                <span dir="ltr">{patient.phone}</span>
              </div>
              {patient.birth_date && (
                <div className="flex items-center gap-2 text-sm">
                  <Calendar className="h-4 w-4 text-on-surface-variant" />
                  <span>{formatDate(patient.birth_date)} ({getAge(patient.birth_date)} {t('age')})</span>
                </div>
              )}
              {patient.gender && (
                <div className="flex items-center gap-2 text-sm">
                  <Activity className="h-4 w-4 text-on-surface-variant" />
                  <span>{patient.gender === 'M' ? t('male') : t('female')}</span>
                </div>
              )}
            </div>
            <div className="pt-2 space-y-2">
              <Button className="w-full" variant="secondary" size="sm">
                {t('patientCard')}
              </Button>
              <Button className="w-full" variant="secondary" size="sm">
                {t('print')}
              </Button>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <div className="rounded-xl border border-outline bg-surface">
            <div className="flex items-center justify-between px-5 py-4 border-b border-outline">
              <h3 className="font-semibold text-on-surface flex items-center gap-2">
                <FileText className="h-4 w-4" /> {t('orders')}
              </h3>
              <Link to={`/orders?patient_id=${patientId}`} className="text-sm text-primary hover:underline">{t('viewAll')}</Link>
            </div>
            <div className="p-4">
              {!patientOrders?.items?.length ? (
                <p className="text-sm text-on-surface-variant text-center py-4">{t('noData')}</p>
              ) : (
                <div className="space-y-2">
                  {patientOrders.items.slice(0, 5).map((o) => (
                    <Link key={o.id} to={`/orders/${o.id}`} className="flex items-center justify-between p-3 rounded-lg hover:bg-surface-container-low transition-colors">
                      <div>
                        <p className="text-sm font-medium text-on-surface">Order #{o.id}</p>
                        <p className="text-xs text-on-surface-variant">{formatDateTime(o.created_at)}</p>
                      </div>
                      <StatusBadge status={o.status} />
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-xl border border-outline bg-surface">
              <div className="px-5 py-4 border-b border-outline">
                <h3 className="font-semibold text-on-surface flex items-center gap-2">
                  <HeartPulse className="h-4 w-4" /> {t('diagnosis', 'التشخيصات')}
                </h3>
              </div>
              <div className="p-4">
                {!conditions?.length ? (
                  <p className="text-sm text-on-surface-variant text-center py-4">{t('noData')}</p>
                ) : (
                  <div className="space-y-2">
                    {conditions.map((c) => (
                      <div key={c.id} className="p-2 rounded-lg bg-surface-container-low">
                        <p className="text-sm font-medium text-on-surface">{c.condition_name}</p>
                        {c.onset_date && <p className="text-xs text-on-surface-variant">{formatDate(c.onset_date)}</p>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="rounded-xl border border-outline bg-surface">
              <div className="px-5 py-4 border-b border-outline">
                <h3 className="font-semibold text-on-surface flex items-center gap-2">
                  <Pill className="h-4 w-4" /> {t('medication')}
                </h3>
              </div>
              <div className="p-4">
                {!medications?.length ? (
                  <p className="text-sm text-on-surface-variant text-center py-4">{t('noData')}</p>
                ) : (
                  <div className="space-y-2">
                    {medications.map((m) => (
                      <div key={m.id} className="p-2 rounded-lg bg-surface-container-low">
                        <p className="text-sm font-medium text-on-surface">{m.medication_name}</p>
                        {m.dosage && <p className="text-xs text-on-surface-variant">{m.dosage} — {m.frequency}</p>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
