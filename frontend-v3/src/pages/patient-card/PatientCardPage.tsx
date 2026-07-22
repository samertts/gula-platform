import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, Input, Button } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import { CreditCard, QrCode, Printer } from "lucide-react";

export function PatientCardPage() {
  const [patientId, setPatientId] = useState("");

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
              />
            </div>
            <div className="flex gap-2">
              <Button disabled={!patientId}>
                <QrCode className="h-4 w-4" /> عرض البطاقة
              </Button>
              <Button variant="outline" disabled={!patientId}>
                <Printer className="h-4 w-4" /> طباعة
              </Button>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <QrCode className="h-5 w-5" />
              مسح بطاقة
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <QrCode className="h-24 w-24 text-muted-foreground mb-4" />
              <p className="text-sm text-muted-foreground">استخدم كاميرا الجهاز لمسح رمز QR الخاص بالمريض</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
