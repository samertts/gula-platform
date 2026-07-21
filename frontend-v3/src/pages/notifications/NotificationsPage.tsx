import { Card, CardContent } from "@/components/ui";
import { PageHeader, EmptyState } from "@/components/shared/PageComponents";
import { Bell } from "lucide-react";

export function NotificationsPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="الإشعارات" description="جميع الإشعارات والتنبيهات" />
      <Card>
        <CardContent>
          <EmptyState icon={Bell} title="لوحة الإشعارات" description="سيتم عرض الإشعارات عند توفرها" />
        </CardContent>
      </Card>
    </div>
  );
}
