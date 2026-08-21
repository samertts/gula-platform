import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle, Input, Button } from "@/components/ui";
import { PageHeader, LoadingSpinner, EmptyState, ErrorDisplay } from "@/components/shared/PageComponents";
import { patientCardApi } from "@/api/endpoints";
import { CreditCard, QrCode, Printer, Eye } from "lucide-react";

export function PatientCardPage() {
  const [patientId, setPatientId] = useState("");
  const [activeId, setActiveId] = useState<number | null>(null);

  const { data: card, isLoading, error, refetch } = useQuery({
    queryKey: ["patient-card", activeId],
    queryFn: () => patientCardApi.get(activeId!),
    enabled: activeId !== null,
  });

  const handleView = () => {
    const id = Number(patientId);
    if (id > 0) setActiveId(id);
  };

  const handlePrint = () => {
    if (activeId !== null) {
      window.open(`/api/patient-card/${activeId}/print`, "_blank");
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader title="بطاقة المريض" description="إنشاء وعرض بطاقات المرضى الرقمية" />
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              إنشاء بطاقة مريض
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">رقم المريض</label>
              <Input
                placeholder="أدخل رقم المريض..."
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") handleView(); }}
              />
            </div>
            <div className="flex gap-2">
              <Button disabled={!patientId} onClick={handleView}>
                <Eye className="h-4 w-4" /> عرض البطاقة
              </Button>
              <Button variant="outline" disabled={activeId === null} onClick={handlePrint}>
                <Printer className="h-4 w-4" /> طباعة
              </Button>
            </div>
            {isLoading && <LoadingSpinner />}
            {error && <ErrorDisplay error={(error as Error).message} onRetry={() => refetch()} />}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <QrCode className="h-5 w-5" />
              بطاقة المريض
            </CardTitle>
          </CardHeader>
          <CardContent>
            {card ? (
              <div className="space-y-3">
                <div className="flex items-center justify-center p-4">
                  {card.qr_url ? (
                    <img src={card.qr_url} alt="QR" className="w-48 h-48" />
                  ) : (
                    <QrCode className="w-48 h-48 text-muted-foreground" />
                  )}
                </div>
                <div className="text-center space-y-1">
                  <p className="font-medium text-lg">{card.card.full_name}</p>
                  <p className="text-sm text-muted-foreground">الهاتف: {card.card.phone_masked ?? "محجوب"}</p>
                  <p className="text-xs text-muted-foreground">المعرّف الصحي: {card.card.health_id_masked ?? "محجوب"}</p>
                </div>
              </div>
            ) : (
              <EmptyState
                icon={CreditCard}
                title="بطاقة المريض"
                description="أدخل رقم المريض لعرض البطاقة"
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
