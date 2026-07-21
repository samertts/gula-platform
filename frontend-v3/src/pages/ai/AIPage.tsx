import { useQuery } from "@tanstack/react-query";
import { aiApi } from "@/api/endpoints";
import { Card, CardHeader, CardTitle, CardContent, Badge, Button } from "@/components/ui";
import { PageHeader, LoadingSpinner, ErrorDisplay, EmptyState } from "@/components/shared/PageComponents";
import { Bot, MessageSquare, FlaskConical, CheckCircle2 } from "lucide-react";
import { useState } from "react";

export function AIPage() {
  const [activeTab, setActiveTab] = useState<"chat" | "interpret" | "approvals">("chat");

  return (
    <div className="space-y-6">
      <PageHeader title="المساعد الذكي" description="الذكاء الاصطناعي للمختبر" />

      <div className="flex gap-2 border-b pb-2">
        <Button variant={activeTab === "chat" ? "default" : "ghost"} size="sm" onClick={() => setActiveTab("chat")}>
          <MessageSquare className="h-4 w-4" /> محادثة
        </Button>
        <Button variant={activeTab === "interpret" ? "default" : "ghost"} size="sm" onClick={() => setActiveTab("interpret")}>
          <FlaskConical className="h-4 w-4" /> تفسير النتائج
        </Button>
        <Button variant={activeTab === "approvals" ? "default" : "ghost"} size="sm" onClick={() => setActiveTab("approvals")}>
          <CheckCircle2 className="h-4 w-4" /> الموافقات المعلقة
        </Button>
      </div>

      {activeTab === "chat" && (
        <Card>
          <CardHeader><CardTitle>محادثة مع المساعد الذكي</CardTitle></CardHeader>
          <CardContent>
            <EmptyState
              icon={Bot}
              title="المساعد الذكي"
              description="اطرح أسئلتك حول تفسير النتائج أو إرشادات المختبر"
            />
          </CardContent>
        </Card>
      )}

      {activeTab === "interpret" && (
        <Card>
          <CardHeader><CardTitle>تفسير النتائج</CardTitle></CardHeader>
          <CardContent>
            <EmptyState
              icon={FlaskConical}
              title="تفسير النتائج"
              description="اختر نتيجة لتحليلها باستخدام الذكاء الاصطناعي"
            />
          </CardContent>
        </Card>
      )}

      {activeTab === "approvals" && <AIPendingApprovals />}
    </div>
  );
}

function AIPendingApprovals() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["ai-approvals"],
    queryFn: () => aiApi.pending(),
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay onRetry={refetch} />;

  const items = (data as any)?.items || (data as any)?.approvals || [];

  if (items.length === 0) {
    return (
      <Card>
        <CardContent>
          <EmptyState icon={CheckCircle2} title="لا توجد موافقات معلقة" description="جميع التفسيرات تمت مراجعتها" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader><CardTitle>الموافقات المعلقة</CardTitle></CardHeader>
      <CardContent>
        {items.map((item: any) => (
          <div key={item.id} className="flex items-center justify-between border-b py-3 last:border-0">
            <div>
              <p className="font-medium">{item.test_name}</p>
              <p className="text-sm text-muted-foreground">{item.patient_name}</p>
            </div>
            <Badge variant="warning">قيد المراجعة</Badge>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
