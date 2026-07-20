import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { orders, results } from '@/api/endpoints';
import { Button } from '@/components/ui/Button';
import { StatusBadge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { useTranslation } from 'react-i18next';
import { formatDateTime } from '@/lib/utils';
import { ArrowLeft, ClipboardList, User, CheckCircle, XCircle } from 'lucide-react';

export function OrderDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const orderId = Number(id);
  const queryClient = useQueryClient();

  const { data: order, isLoading } = useQuery({
    queryKey: ['order', orderId],
    queryFn: () => orders.get(orderId),
    enabled: !!orderId,
  });

  const validateMutation = useMutation({
    mutationFn: () => orders.validate(orderId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['order', orderId] }),
  });

  const cancelMutation = useMutation({
    mutationFn: () => orders.cancel(orderId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['order', orderId] }),
  });

  if (isLoading) return <Skeleton className="h-96" />;
  if (!order) return <EmptyState icon={ClipboardList} title={t('noData')} />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/orders" className="p-2 rounded-lg hover:bg-surface-container-high">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-on-surface">{t('order')} #{order.id}</h1>
            <p className="text-on-surface-variant mt-1">{formatDateTime(order.created_at)}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <StatusBadge status={order.status} className="text-base px-4 py-1.5" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-4">
          <div className="rounded-xl border border-outline bg-surface p-5 space-y-3">
            <h3 className="font-semibold text-on-surface">{t('details')}</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-on-surface-variant">{t('patientName')}</span>
                <Link to={`/patients/${order.patient_id}`} className="text-primary hover:underline font-medium">
                  {order.patient?.full_name || `#${order.patient_id}`}
                </Link>
              </div>
              <div className="flex justify-between">
                <span className="text-on-surface-variant">{t('doctorName')}</span>
                <span>{order.doctor_name || '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-on-surface-variant">{t('status')}</span>
                <StatusBadge status={order.status} />
              </div>
              <div className="flex justify-between">
                <span className="text-on-surface-variant">{t('version', 'النسخة')}</span>
                <span>{order.version}</span>
              </div>
            </div>
          </div>

          {order.status === 'pending' && (
            <div className="space-y-2">
              <Button className="w-full" onClick={() => validateMutation.mutate()}>
                <CheckCircle className="h-4 w-4" />
                {t('validateOrder')}
              </Button>
              <Button className="w-full" variant="danger" onClick={() => cancelMutation.mutate()}>
                <XCircle className="h-4 w-4" />
                {t('cancelOrder')}
              </Button>
            </div>
          )}
        </div>

        <div className="lg:col-span-2 space-y-4">
          <div className="rounded-xl border border-outline bg-surface">
            <div className="px-5 py-4 border-b border-outline">
              <h3 className="font-semibold text-on-surface">{t('results')}</h3>
            </div>
            <div className="p-4">
              {!order.results?.length ? (
                <p className="text-sm text-on-surface-variant text-center py-8">{t('noData')}</p>
              ) : (
                <div className="space-y-2">
                  {order.results.map((r) => (
                    <div key={r.id} className="flex items-center justify-between p-3 rounded-lg bg-surface-container-low">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-on-surface">{r.test_name}</p>
                        <p className="text-xs text-on-surface-variant">{r.unit}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold">{r.value ?? r.value_text ?? '—'}</p>
                        {r.normal_range_low != null && (
                          <p className="text-xs text-on-surface-variant">
                            {r.normal_range_low} — {r.normal_range_high}
                          </p>
                        )}
                      </div>
                      {r.flag && <StatusBadge status={r.flag} className="mr-3" />}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
