import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui";
import { PageHeader, ErrorDisplay, LoadingSpinner } from "@/components/shared/PageComponents";
import { Button } from "@/components/ui";
import { Input } from "@/components/ui";
import { Badge } from "@/components/ui";
import { notificationsApi } from "@/api/endpoints";
import { Send, History, Phone, CheckCircle, Clock } from "lucide-react";

type Channel = "whatsapp" | "sms";

export function NotificationsPage() {
  const [orderId, setOrderId] = useState("");
  const [channel, setChannel] = useState<Channel>("whatsapp");
  const [searchedOrderId, setSearchedOrderId] = useState<string | null>(null);

  const searchOrder = () => {
    if (orderId.trim()) {
      setSearchedOrderId(orderId.trim());
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader title="الإشعارات" description="إرسال إشعارات النتائج للمرضى عبر واتساب أو رسائل نصية" />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Send className="h-5 w-5" />
            إرسال إشعار نتيجة
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <Input
              placeholder="رقم الطلب (Order ID)"
              value={orderId}
              onChange={(e) => setOrderId(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") searchOrder(); }}
              className="flex-1"
              dir="ltr"
            />
            <div className="flex gap-2">
              <Button
                variant={channel === "whatsapp" ? "default" : "outline"}
                onClick={() => setChannel("whatsapp")}
              >
                WhatsApp
              </Button>
              <Button
                variant={channel === "sms" ? "default" : "outline"}
                onClick={() => setChannel("sms")}
              >
                SMS
              </Button>
              <Button onClick={searchOrder}>
                <Send className="h-4 w-4 ms-2" />
                إرسال
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {searchedOrderId && (
        <>
          <SendStatus orderId={Number(searchedOrderId)} channel={channel} />
          <ViewHistory orderId={Number(searchedOrderId)} />
        </>
      )}
    </div>
  );
}

function SendStatus({ orderId, channel }: { orderId: number; channel: Channel }) {
  const mutation = useMutation({
    mutationFn: () => notificationsApi.send({ order_id: orderId, channel }),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Send className="h-5 w-5" />
          إرسال إشعار
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
          {mutation.isPending ? "جاري الإرسال..." : `إرسال عبر ${channel === "whatsapp" ? "واتساب" : "رسالة نصية"}`}
        </Button>
        {mutation.error && (
          <ErrorDisplay error={(mutation.error as Error).message} />
        )}
        {mutation.data && (
          <div className="space-y-3 p-4 bg-muted rounded-lg">
            <div className="flex items-center gap-2 text-green-600">
              <CheckCircle className="h-5 w-5" />
              <span className="font-medium">رابط الإشعار جاهز</span>
            </div>
            <div className="flex items-center gap-2">
              <Phone className="h-4 w-4 text-muted-foreground" />
              <span dir="ltr">{mutation.data?.patient_phone as string}</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline">
                {channel === "whatsapp" ? "WhatsApp" : "SMS"}
              </Badge>
            </div>
            <div className="p-3 bg-background rounded border text-sm whitespace-pre-wrap font-mono leading-relaxed">
              {mutation.data?.message_preview as string}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ViewHistory({ orderId }: { orderId: number }) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["notification-history", orderId],
    queryFn: () => notificationsApi.history(orderId),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <History className="h-5 w-5" />
          سجل المشاهدة
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading && <LoadingSpinner />}
        {error && <ErrorDisplay error={(error as Error).message} onRetry={() => refetch()} />}
        {data && (
          <div className="space-y-3">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">إجمالي المشاهدات:</span>
                <span className="font-bold text-lg">{data.total_views as number}</span>
              </div>
            </div>
            {(data.total_views as number) > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-muted-foreground">أول مشاهدة:</span>
                  <span>{new Date(data.first_viewed as string).toLocaleString("ar-IQ")}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-muted-foreground">آخر مشاهدة:</span>
                  <span>{new Date(data.last_viewed as string).toLocaleString("ar-IQ")}</span>
                </div>
              </div>
            )}
            {(data.total_views as number) === 0 && (
              <div className="flex flex-col items-center gap-2 py-6 text-muted-foreground">
                <Clock className="h-8 w-8" />
                <span>لم يتم مشاهدة النتائج بعد</span>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
