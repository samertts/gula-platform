import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardHeader, CardBody, Button, Badge, LayoutContent, Tabs } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';
import { OrderPanel, type OrderFormData } from '../components/OrderPanel';

interface Order {
  id: string;
  category: string;
  categoryAr: string;
  priority: string;
  priorityAr: string;
  description: string;
  descriptionAr: string;
  status: string;
  statusAr: string;
  orderedAt: string;
  orderedBy: string;
}

const MOCK_ORDERS: Order[] = [
  { id: 'o1', category: 'lab', categoryAr: 'مختبر', priority: 'urgent', priorityAr: 'عاجل', description: 'Complete Blood Count', descriptionAr: 'تعداد دم كامل', status: 'active', statusAr: 'نشط', orderedAt: '2024-12-15T09:00:00', orderedBy: 'Dr. Ahmed' },
  { id: 'o2', category: 'radiology', categoryAr: 'أشعة', priority: 'routine', priorityAr: 'روتيني', description: 'Chest X-Ray', descriptionAr: 'أشعة الصدر', status: 'completed', statusAr: 'مكتمل', orderedAt: '2024-12-14T14:30:00', orderedBy: 'Dr. Ahmed' },
  { id: 'o3', category: 'medication', categoryAr: 'دواء', priority: 'stat', priorityAr: 'فوري', description: 'IV Antibiotics', descriptionAr: 'مضادات حيوية وريدية', status: 'active', statusAr: 'نشط', orderedAt: '2024-12-15T08:45:00', orderedBy: 'Dr. Sara' },
];

export function Orders() {
  const { patientId } = useParams<{ patientId: string }>();
  const { isRtl } = useRTL();
  const navigate = useNavigate();
  const [orders, setOrders] = useState<Order[]>(MOCK_ORDERS);
  const [showOrderPanel, setShowOrderPanel] = useState(false);

  const handleSubmitOrder = (data: OrderFormData) => {
    const newOrder: Order = {
      id: `o-${Date.now()}`,
      category: data.category,
      categoryAr: data.category,
      priority: data.priority,
      priorityAr: data.priority,
      description: data.description,
      descriptionAr: data.descriptionAr,
      status: 'active',
      statusAr: 'نشط',
      orderedAt: new Date().toISOString(),
      orderedBy: 'Dr. Ahmed',
    };
    setOrders(prev => [newOrder, ...prev]);
    setShowOrderPanel(false);
  };

  const priorityColors: Record<string, 'danger' | 'warning' | 'info' | 'default'> = {
    stat: 'danger',
    urgent: 'warning',
    asap: 'info',
    routine: 'default',
  };

  const statusColors: Record<string, 'success' | 'default' | 'danger' | 'warning'> = {
    active: 'success',
    completed: 'default',
    cancelled: 'danger',
    pending: 'warning',
  };

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={() => navigate(-1)} className="p-2 rounded-xl hover:bg-neutral-100 dark:hover:bg-neutral-800">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d={isRtl ? "M19 12H5M12 19l-7-7 7-7" : "M5 12h14M12 5l7 7-7 7"} />
              </svg>
            </button>
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
              {isRtl ? 'الطلبات السريرية' : 'Clinical Orders'}
            </h1>
          </div>
          <Button variant="primary" onClick={() => setShowOrderPanel(true)}>
            {isRtl ? 'طلب جديد' : 'New Order'}
          </Button>
        </div>

        {showOrderPanel && (
          <OrderPanel
            patientId={patientId || ''}
            category="lab"
            onSubmit={handleSubmitOrder}
            onCancel={() => setShowOrderPanel(false)}
          />
        )}

        <div className="space-y-2">
          {orders.map(order => (
            <Card key={order.id} padding="md">
              <CardBody>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant={priorityColors[order.priority]} size="sm">
                        {isRtl ? order.priorityAr : order.priority}
                      </Badge>
                      <Badge variant="default" size="sm">
                        {isRtl ? order.categoryAr : order.category}
                      </Badge>
                      <span className="text-xs text-neutral-400">
                        {new Date(order.orderedAt).toLocaleDateString(isRtl ? 'ar-IQ' : 'en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <p className="font-medium text-sm">
                      {isRtl ? order.descriptionAr : order.description}
                    </p>
                    <p className="text-xs text-neutral-400 mt-1">{order.orderedBy}</p>
                  </div>
                  <Badge variant={statusColors[order.status]}>
                    {isRtl ? order.statusAr : order.status}
                  </Badge>
                </div>
              </CardBody>
            </Card>
          ))}
          {orders.length === 0 && (
            <p className="text-sm text-neutral-500 text-center py-8">{isRtl ? 'لا توجد طلبات' : 'No orders'}</p>
          )}
        </div>
      </div>
    </LayoutContent>
  );
}
