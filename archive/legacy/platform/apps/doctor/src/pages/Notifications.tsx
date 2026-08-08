import { useState } from 'react';
import { Card, CardHeader, CardBody, Badge, Button, LayoutContent, Tabs } from '@gula/ui-platform';
import { useRTL } from '@gula/ui-platform';

interface Notification {
  id: string;
  type: 'critical_alert' | 'lab_result' | 'appointment' | 'prescription' | 'referral' | 'system';
  title: string;
  titleAr: string;
  message: string;
  messageAr: string;
  isRead: boolean;
  createdAt: string;
  actionable: boolean;
  patientId?: string;
}

const MOCK_NOTIFICATIONS: Notification[] = [
  { id: 'n1', type: 'critical_alert', title: 'Critical Lab Result', titleAr: 'نتيجة مختبر حرجة', message: 'Potassium: 6.8 mmol/L - Omar Hassan', messageAr: 'البوتاسيوم: 6.8 - عمر حسن', isRead: false, createdAt: '2024-12-15T09:30:00', actionable: true, patientId: 'p5' },
  { id: 'n2', type: 'lab_result', title: 'New Lab Results', titleAr: 'نتائج مختبر جديدة', message: 'CBC results available for Ahmed Ali', messageAr: 'نتائج CBC متاحة لأحمد علي', isRead: false, createdAt: '2024-12-15T08:45:00', actionable: true, patientId: 'p1' },
  { id: 'n3', type: 'appointment', title: 'Appointment Reminder', titleAr: 'تذكير موعد', message: 'Sara Mohammed in 30 minutes', messageAr: 'سارة محمد بعد 30 دقيقة', isRead: false, createdAt: '2024-12-15T09:30:00', actionable: false },
  { id: 'n4', type: 'prescription', title: 'Prescription Expiring', titleAr: 'وصفة منتهية', message: 'Lisinopril prescription for Ahmed Ali expires in 3 days', messageAr: 'وصفة ليزينوبريل تنتهي بعد 3 أيام', isRead: true, createdAt: '2024-12-14T14:00:00', actionable: true, patientId: 'p1' },
  { id: 'n5', type: 'referral', title: 'Referral Accepted', titleAr: 'تحويل مقبول', message: 'Cardiology accepted referral for Ahmed Ali', messageAr: 'القلب قبل تحويل أحمد علي', isRead: true, createdAt: '2024-12-14T11:00:00', actionable: false },
  { id: 'n6', type: 'system', title: 'System Update', titleAr: 'تحديث النظام', message: 'App updated to version 2.1.0', messageAr: 'تم تحديث التطبيق إلى الإصدار 2.1.0', isRead: false, createdAt: '2024-12-13T00:00:00', actionable: false },
];

const typeConfig: Record<string, { icon: string; color: string }> = {
  critical_alert: { icon: '🚨', color: 'border-r-4 border-danger-500' },
  lab_result: { icon: '🔬', color: 'border-r-4 border-primary-500' },
  appointment: { icon: '📅', color: 'border-r-4 border-info-500' },
  prescription: { icon: '💊', color: 'border-r-4 border-success-500' },
  referral: { icon: '🔄', color: 'border-r-4 border-warning-500' },
  system: { icon: '⚙️', color: 'border-r-4 border-neutral-500' },
};

export function Notifications() {
  const { isRtl } = useRTL();
  const [notifications, setNotifications] = useState(MOCK_NOTIFICATIONS);
  const [activeTab, setActiveTab] = useState('all');

  const unreadCount = notifications.filter(n => !n.isRead).length;

  const filtered = activeTab === 'unread'
    ? notifications.filter(n => !n.isRead)
    : activeTab === 'critical'
      ? notifications.filter(n => n.type === 'critical_alert')
      : notifications;

  const markAsRead = (id: string) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, isRead: true } : n));
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, isRead: true })));
  };

  const tabs = [
    { id: 'all', label: isRtl ? 'الكل' : 'All' },
    { id: 'unread', label: isRtl ? 'غير مقروء' : 'Unread' },
    { id: 'critical', label: isRtl ? 'حرجة' : 'Critical' },
  ];

  return (
    <LayoutContent>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50">
              {isRtl ? 'الإشعارات' : 'Notifications'}
            </h1>
            <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
              {isRtl
                ? `${unreadCount} إشعار غير مقروء`
                : `${unreadCount} unread notifications`}
            </p>
          </div>
          {unreadCount > 0 && (
            <Button variant="ghost" size="sm" onClick={markAllAsRead}>
              {isRtl ? 'تحديد الكل كمقروء' : 'Mark all as read'}
            </Button>
          )}
        </div>

        <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

        <div className="space-y-2">
          {filtered.map(notif => {
            const config = typeConfig[notif.type] || typeConfig.system;
            return (
              <div
                key={notif.id}
                onClick={() => markAsRead(notif.id)}
                className={`relative flex items-start gap-3 p-4 rounded-xl border transition-colors cursor-pointer ${
                  notif.isRead
                    ? 'bg-white dark:bg-neutral-800 border-neutral-200 dark:border-neutral-700'
                    : 'bg-primary-50 dark:bg-primary-950 border-primary-200 dark:border-primary-900'
                } ${config.color}`}
              >
                {!notif.isRead && (
                  <div className="absolute top-4 left-4 rtl:left-auto rtl:right-4 w-2 h-2 rounded-full bg-primary-500" />
                )}
                <span className="text-xl">{config.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <p className={`font-medium text-sm ${notif.isRead ? 'text-neutral-700 dark:text-neutral-300' : 'text-neutral-900 dark:text-neutral-50'}`}>
                      {isRtl ? notif.titleAr : notif.title}
                    </p>
                    <Badge variant={notif.type === 'critical_alert' ? 'danger' : 'default'} size="xs">
                      {notif.type === 'critical_alert' ? (isRtl ? 'حرج' : 'Critical') :
                       notif.type === 'lab_result' ? (isRtl ? 'مختبر' : 'Lab') :
                       notif.type === 'appointment' ? (isRtl ? 'موعد' : 'Appt') :
                       notif.type === 'prescription' ? (isRtl ? 'وصفة' : 'Rx') :
                       notif.type === 'referral' ? (isRtl ? 'تحويل' : 'Ref') :
                       (isRtl ? 'نظام' : 'System')}
                    </Badge>
                  </div>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400">
                    {isRtl ? notif.messageAr : notif.message}
                  </p>
                  <p className="text-[10px] text-neutral-400 mt-1">
                    {new Date(notif.createdAt).toLocaleDateString(isRtl ? 'ar-IQ' : 'en-US', {
                      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
                    })}
                  </p>
                </div>
                {notif.actionable && (
                  <Button variant="outline" size="xs">
                    {isRtl ? 'عرض' : 'View'}
                  </Button>
                )}
              </div>
            );
          })}
          {filtered.length === 0 && (
            <Card>
              <CardBody>
                <p className="text-sm text-neutral-500 text-center py-8">
                  {isRtl ? 'لا توجد إشعارات' : 'No notifications'}
                </p>
              </CardBody>
            </Card>
          )}
        </div>
      </div>
    </LayoutContent>
  );
}
